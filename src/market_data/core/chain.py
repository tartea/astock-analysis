"""try_chain — the core provider failover engine.

Given a dimension name, iterates through configured providers in priority order,
calling the requested method on each. On failure, moves to the next provider.
Supports configurable retry with exponential backoff and circuit breaker.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .cache import cached
from .config import AppConfig, ProviderConfig, get_config

logger = logging.getLogger(__name__)


# ── Circuit breaker state ──────────────────────────────────────

class CircuitBreaker:
    """Tracks failure counts per provider, opens circuit after threshold."""

    def __init__(self):
        """Initialize failure counters and cooldown timers per provider."""
        self._failures: Dict[str, int] = defaultdict(int)
        self._open_until: Dict[str, float] = {}

    def record_failure(self, provider_name: str, cooldown_seconds: int) -> None:
        """Increment the failure counter for a provider."""
        self._failures[provider_name] += 1

    def record_success(self, provider_name: str) -> None:
        """Reset failure counter and cooldown for a provider."""
        self._failures[provider_name] = 0
        self._open_until.pop(provider_name, None)

    def is_open(self, provider_name: str, threshold: int, cooldown_seconds: int) -> bool:
        """Check if circuit is open for this provider."""
        if self._failures[provider_name] >= threshold:
            until = self._open_until.get(provider_name, 0)
            if time.time() < until:
                return True
            # Cooldown expired, close the circuit
            self._failures[provider_name] = 0
            self._open_until.pop(provider_name, None)
        return False

    def open_circuit(self, provider_name: str, cooldown_seconds: int) -> None:
        """Open the circuit breaker, preventing calls until cooldown expires."""
        self._open_until[provider_name] = time.time() + cooldown_seconds


# Global circuit breaker instance
_breaker = CircuitBreaker()


# ── Provider registry ──────────────────────────────────────────

_provider_registry: Dict[str, Any] = {}


def register_provider(name: str, instance: Any) -> None:
    """Register a provider instance by name."""
    _provider_registry[name] = instance


def get_provider(name: str) -> Optional[Any]:
    """Get a registered provider by name."""
    return _provider_registry.get(name)


# ── try_chain ──────────────────────────────────────────────────

class ProviderError(Exception):
    """Raised when a single provider fails."""


class AllProvidersFailedError(Exception):
    """Raised when all providers in the chain have failed."""

    def __init__(self, dimension: str, errors: List[Tuple[str, str]]):
        """Build error message aggregating all provider failures for a dimension."""
        self.dimension = dimension
        self.errors = errors
        msg = f"All providers failed for dimension '{dimension}':\n"
        for provider, error in errors:
            msg += f"  - {provider}: {error}\n"
        super().__init__(msg)


def try_chain(
    method_name: str,
    dimension: str,
    *args: Any,
    ticker: str = "",
    cache_ttl: Optional[int] = None,
    config: Optional[AppConfig] = None,
    **kwargs: Any,
) -> Tuple[Any, str]:
    """Call a method across a chain of providers with automatic failover.

    Iterates through providers configured for the given dimension in priority
    order. Each provider is called with the given method_name and
    args/kwargs. On failure, the next provider is tried.

    Each provider call goes through: circuit breaker check → retry with
    exponential backoff → method call.

    Args:
        method_name: Name of the method to call on each provider (e.g. 'fetch_kline')
        dimension: Dimension name (e.g. 'kline') — used to look up the
                   provider chain from config
        *args: Positional arguments passed to the provider method
        ticker: Stock ticker for cache key generation (optional)
        cache_ttl: If provided, cache the result with this TTL
        config: Optional AppConfig (defaults to singleton)
        **kwargs: Keyword arguments passed to the provider method

    Returns:
        Tuple of (data, provider_name) where provider_name indicates which
        provider successfully fulfilled the request.

    Raises:
        AllProvidersFailedError: When no provider in the chain succeeds.
    """
    if config is None:
        config = get_config()

    dim_config = config.get_dimension(dimension)
    if dim_config is None:
        raise ValueError(
            f"Unknown dimension '{dimension}'. Available: {list(config.dimensions.keys())}"
        )

    provider_names = dim_config.providers
    if not provider_names:
        raise ValueError(f"No providers configured for dimension '{dimension}'")

    errors: List[Tuple[str, str]] = []

    # Build a cache key string for the cached() wrapper
    cache_key = f"{method_name}::{_args_to_key(*args, **kwargs)}"

    def _attempt_chain() -> Any:
        last_error: Optional[Exception] = None

        for provider_name in provider_names:
            provider_config = config.get_provider(provider_name)
            if provider_config is None:
                logger.warning(
                    "Provider '%s' not found in config, skipping", provider_name
                )
                errors.append((provider_name, "Provider not found in config"))
                continue

            provider = get_provider(provider_name)
            if provider is None:
                logger.warning(
                    "Provider '%s' not registered, skipping", provider_name
                )
                errors.append((provider_name, "Provider not registered"))
                continue

            # Circuit breaker check
            if _breaker.is_open(
                provider_name,
                provider_config.circuit_breaker_threshold,
                provider_config.cooldown_seconds,
            ):
                logger.info(
                    "Circuit breaker open for '%s', skipping", provider_name
                )
                errors.append((provider_name, "Circuit breaker open"))
                continue

            # Retry with exponential backoff
            last_error = None
            provider_failed = False
            for attempt in range(provider_config.retry_count):
                try:
                    method = getattr(provider, method_name, None)
                    if method is None:
                        raise ProviderError(
                            f"Provider '{provider_name}' has no method '{method_name}'"
                        )

                    result = method(*args, **kwargs)

                    # Success — reset circuit breaker
                    _breaker.record_success(provider_name)
                    return result, provider_name

                except ProviderError as pe:
                    # Provider signaled it cannot fulfill — skip immediately
                    last_error = pe
                    provider_failed = True
                    break
                except Exception as e:
                    last_error = e
                    if attempt < provider_config.retry_count - 1:
                        backoff = provider_config.backoff_base ** attempt
                        logger.debug(
                            "Provider '%s' attempt %d/%d failed: %s. Retrying in %.1fs...",
                            provider_name,
                            attempt + 1,
                            provider_config.retry_count,
                            e,
                            backoff,
                        )
                        time.sleep(backoff)

            # All retries exhausted or ProviderError — record failure
            if provider_failed or last_error is not None:
                _breaker.record_failure(provider_name, provider_config.cooldown_seconds)
                _breaker.open_circuit(provider_name, provider_config.cooldown_seconds)
                err_msg = str(last_error) if last_error else "Unknown error"
                logger.warning(
                    "Provider '%s' failed after %d attempts: %s",
                    provider_name,
                    provider_config.retry_count,
                    err_msg,
                )
                errors.append((provider_name, err_msg))

        raise AllProvidersFailedError(dimension, errors)

    # Wrap with cache if TTL is specified
    if cache_ttl is not None and ticker:
        return cached(ticker, cache_key, _attempt_chain, ttl=cache_ttl)  # type: ignore[return-value]
    else:
        return _attempt_chain()  # type: ignore[return-value]


def _args_to_key(*args: Any, **kwargs: Any) -> str:
    """Build a stable string key from args and kwargs for cache lookup."""
    parts = [str(a) for a in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return "::".join(parts)
