"""Tests for the astock_analysis MVP."""

import os
import sys
import tempfile

import pytest

# Point to test config before importing the package
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestConfig:
    """Configuration loader tests."""

    def test_load_config_from_yaml(self):
        from astock_analysis.core.config import load_config

        config = load_config()
        assert "akshare" in config.providers
        assert "kline" in config.dimensions
        assert config.dimensions["kline"].providers == ["akshare"]

    def test_provider_config_values(self):
        from astock_analysis.core.config import load_config

        config = load_config()
        akshare = config.providers["akshare"]
        assert akshare.retry_count == 3
        assert akshare.circuit_breaker_threshold == 5
        assert akshare.cooldown_seconds == 300

    def test_singleton_config(self):
        from astock_analysis.core.config import get_config, reload_config

        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

        c3 = reload_config()
        assert c3 is not c1


class TestCache:
    """SQLite cache tests."""

    def setup_method(self):
        from astock_analysis.core import cache

        cache.clear_cache()
        # Use a temp DB for testing
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._orig_path = cache.CACHE_DB_PATH
        cache.CACHE_DB_PATH = self._tmp.name

    def teardown_method(self):
        from astock_analysis.core import cache

        cache.clear_cache()
        cache.CACHE_DB_PATH = self._orig_path
        os.unlink(self._tmp.name)

    def test_cache_miss_then_hit(self):
        from astock_analysis.core.cache import cached, TTL_HOURLY

        call_count = [0]

        def fetch_fn():
            call_count[0] += 1
            return {"value": 42}

        # First call — cache miss
        result1 = cached("000001", "test_key", fetch_fn, ttl=TTL_HOURLY)
        assert result1 == {"value": 42}
        assert call_count[0] == 1

        # Second call — cache hit
        result2 = cached("000001", "test_key", fetch_fn, ttl=TTL_HOURLY)
        assert result2 == {"value": 42}
        assert call_count[0] == 1  # fetch_fn not called again

    def test_cache_different_keys(self):
        from astock_analysis.core.cache import cached, TTL_HOURLY

        call_count = [0]

        def fetch_fn():
            call_count[0] += 1
            return {"value": call_count[0]}

        r1 = cached("000001", "key_a", fetch_fn, ttl=TTL_HOURLY)
        r2 = cached("000001", "key_b", fetch_fn, ttl=TTL_HOURLY)
        assert r1 != r2
        assert call_count[0] == 2

    def test_clear_cache(self):
        from astock_analysis.core.cache import cached, clear_cache, TTL_HOURLY

        cached("000001", "test", lambda: {"x": 1}, ttl=TTL_HOURLY)
        assert clear_cache() == 1
        assert clear_cache() == 0


class TestKlineDimension:
    """K-line dimension integration tests.

    These tests require akshare to be installed and a working internet
    connection. Mark with @pytest.mark.network to opt-in.
    """

    @pytest.mark.network
    def test_fetch_kline_basic(self):
        from astock_analysis.dimensions.kline import fetch_kline

        response = fetch_kline(
            "600519",
            "2024-01-01",
            "2024-01-31",
            use_cache=False,
        )
        assert response["provider"] == "akshare"
        assert response["code"] == "600519"
        assert len(response["records"]) > 0
        assert "date" in response["records"][0]
        assert "open" in response["records"][0]
        assert "close" in response["records"][0]


class TestAllDimensions:
    """Verify all 19 dimensions are importable and configured."""

    DIMENSIONS = [
        "kline",
        "realtime",
        "financials",
        "capital_flow",
        "lhb",
        "sentiment",
        "index",
        "industry",
        "concept",
        "margin",
        "block_trade",
        "holder",
        "north_flow",
        "news",
        "fund",
        "stock_info",
        "ipo",
        "futures",
        "bond_convertible",
    ]

    def test_all_dimensions_in_config(self):
        """Verify all 19 dimensions are registered in config."""
        from astock_analysis.core.config import load_config

        config = load_config()
        for dim in self.DIMENSIONS:
            assert dim in config.dimensions, f"Dimension '{dim}' missing from config"
            dim_config = config.get_dimension(dim)
            assert dim_config is not None
            assert len(dim_config.providers) > 0, f"No providers for '{dim}'"

    def test_all_dimensions_importable(self):
        """Verify all dimension modules can be imported."""
        for dim in self.DIMENSIONS:
            module = __import__(
                f"astock_analysis.dimensions.{dim}", fromlist=["__init__"]
            )
            func_name = f"fetch_{dim}"
            assert hasattr(module, func_name), f"Missing {func_name} in {dim}"

    def test_provider_has_all_methods(self):
        """Verify AkshareProvider implements all dimension methods."""
        from astock_analysis.providers.akshare import AkshareProvider

        p = AkshareProvider()
        for dim in self.DIMENSIONS:
            method_name = f"fetch_{dim}"
            assert hasattr(p, method_name), (
                f"AkshareProvider missing method '{method_name}'"
            )
            method = getattr(p, method_name)
            assert callable(method), f"'{method_name}' is not callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
