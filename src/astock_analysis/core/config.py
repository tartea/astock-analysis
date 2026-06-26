"""YAML configuration loader for providers and dimensions.

Loads providers.yaml which defines:
- Provider-level settings (retry, circuit breaker, cooldown)
- Dimension-to-provider mapping with priority order
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ProviderConfig:
    """Per-provider configuration."""

    name: str
    retry_count: int = 3
    backoff_base: float = 2.0
    circuit_breaker_threshold: int = 5
    cooldown_seconds: int = 300

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "ProviderConfig":
        """Build a ProviderConfig from a YAML dictionary entry."""
        return cls(
            name=name,
            retry_count=int(data.get("retry_count", 3)),
            backoff_base=float(data.get("backoff_base", 2.0)),
            circuit_breaker_threshold=int(data.get("circuit_breaker_threshold", 5)),
            cooldown_seconds=int(data.get("cooldown_seconds", 300)),
        )


@dataclass
class DimensionConfig:
    """Per-dimension configuration mapping providers."""

    name: str
    providers: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "DimensionConfig":
        """Build a DimensionConfig from a YAML dictionary entry."""
        return cls(
            name=name,
            providers=[p.strip() for p in data.get("providers", [])],
        )


@dataclass
class AppConfig:
    """Top-level application configuration."""

    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    dimensions: Dict[str, DimensionConfig] = field(default_factory=dict)
    cache_enabled: bool = True

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Return provider configuration by name, or None if not found."""
        return self.providers.get(name)

    def get_dimension(self, name: str) -> Optional[DimensionConfig]:
        """Return dimension configuration by name, or None if not found."""
        return self.dimensions.get(name)

    def get_dimension_providers(self, dimension: str) -> List[str]:
        """Return ordered provider names for a dimension."""
        dim = self.dimensions.get(dimension)
        if dim is None:
            return []
        return dim.providers


# ── Config file discovery ──────────────────────────────────────

def _default_config_paths() -> List[Path]:
    """Search paths for providers.yaml."""
    paths: List[Path] = []

    # Env override
    env_path = os.environ.get("ASTOCK_CONFIG")
    if env_path:
        paths.append(Path(env_path))

    # Next to the package
    import astock_analysis

    pkg_dir = Path(astock_analysis.__file__).parent
    paths.append(pkg_dir.parent / "config" / "providers.yaml")

    # User config
    paths.append(Path.home() / ".astock_analysis" / "providers.yaml")

    return paths


def load_config(path: Optional[str | Path] = None) -> AppConfig:
    """Load configuration from a YAML file.

    Args:
        path: Optional explicit path. If None, searches default locations.

    Returns:
        AppConfig instance.

    Raises:
        FileNotFoundError: If no config file can be found.
    """
    if path:
        config_path = Path(path)
    else:
        for candidate in _default_config_paths():
            if candidate.exists():
                config_path = candidate
                break
        else:
            raise FileNotFoundError(
                "No providers.yaml found. Searched:\n"
                + "\n".join(f"  - {p}" for p in _default_config_paths())
                + "\nSet ASTOCK_CONFIG env var to specify a custom path."
            )

    with open(config_path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f) or {}

    providers: Dict[str, ProviderConfig] = {}
    for name, data in raw.get("providers", {}).items():
        providers[name] = ProviderConfig.from_dict(name, data)

    dimensions: Dict[str, DimensionConfig] = {}
    for name, data in raw.get("dimensions", {}).items():
        dimensions[name] = DimensionConfig.from_dict(name, data)

    return AppConfig(
        providers=providers,
        dimensions=dimensions,
        cache_enabled=raw.get("cache_enabled", True),
    )


# ── Module-level singleton ─────────────────────────────────────

_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Return the module-level config singleton, loading on first call."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(path: Optional[str | Path] = None) -> AppConfig:
    """Force reload configuration from disk, optionally from a new path."""
    global _config
    _config = load_config(path)
    return _config
