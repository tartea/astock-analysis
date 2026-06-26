# astock-analysis

A-share 股票数据源抽象层 —— 按维度分类，Provider 可替换，配置驱动路由，SQLite 分级缓存。

## 架构概览

```
调用方
  │
  ▼
dimensions/kline/fetch_kline()          ← 维度路由（TypedDict 返回值）
  │
  ▼
core/chain.py  ·  try_chain()           ← 引擎：按优先级遍历 provider
  │               ├─ 指数退避重试
  │               ├─ 熔断器
  │               └─ fallback 链
  ▼
providers/akshare.py                    ← Provider 实现（鸭子类型）
  │
  ▼
core/cache.py  ·  SQLite 缓存           ← 6 级 TTL（60s → 7d）
```

## 环境要求

- Python ≥ 3.10
- akshare ≥ 1.12.0
- pandas ≥ 2.0.0
- PyYAML ≥ 6.0

## 安装

### 方式一：conda 环境（推荐）

```bash
# 创建 conda 环境
conda create -n astock python=3.11 -y
conda activate astock

# 安装依赖
pip install akshare pandas pyyaml

# 安装项目（开发模式）
cd /path/to/astock-analysis
pip install -e ".[dev]"
```

### 方式二：venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 方式三：直接安装

```bash
pip install -e ".[dev]"
```

## 快速开始

```python
from astock_analysis.dimensions.kline import fetch_kline

# 获取贵州茅台近 30 天日 K 线
response = fetch_kline("600519", "2024-01-01", "2024-06-01")

print(f"Provider: {response['provider']}")
print(f"记录数:   {len(response['records'])}")

for r in response['records'][:3]:
    print(f"  {r['date']}  O:{r['open']:.2f}  C:{r['close']:.2f}")
```

完整示例见 `examples/basic_usage.py`：

```bash
conda activate astock
cd /path/to/astock-analysis
python examples/basic_usage.py
```

## 配置文件

编辑 `config/providers.yaml` 控制 provider 行为和维度路由：

```yaml
providers:
  akshare:
    retry_count: 3
    backoff_base: 2.0
    circuit_breaker_threshold: 5
    cooldown_seconds: 300

dimensions:
  kline:
    providers:
      - akshare
```

替换数据源时只需修改维度下的 `providers` 列表顺序即可。

## 扩展新维度

三步模式：

**1. 定义 TypedDict**

```python
# src/astock_analysis/dimensions/realtime/types.py
from typing import TypedDict

class RealtimeResponse(TypedDict):
    price: float
    change_pct: float
    provider: str
    code: str
```

**2. 写维度路由**

```python
# src/astock_analysis/dimensions/realtime/__init__.py
from astock_analysis.core.chain import try_chain
from astock_analysis.providers.akshare import provider as akshare
from astock_analysis.core.chain import register_provider

register_provider("akshare", akshare)

def fetch_realtime(code: str) -> RealtimeResponse:
    data, provider_name = try_chain("fetch_realtime", "realtime", code=code)
    return RealtimeResponse(
        price=data["price"],
        change_pct=data["change_pct"],
        provider=provider_name,
        code=code,
    )
```

**3. 注册到配置**

```yaml
# config/providers.yaml
dimensions:
  realtime:
    providers:
      - akshare
```

## 扩展新 Provider

三步模式：

**1. 实现 Provider 类**

```python
# src/astock_analysis/providers/tushare.py
from astock_analysis.core.chain import ProviderError

class TushareProvider:
    name = "tushare"
    requires_key = True
    markets = ("A",)

    def fetch_kline(self, code, start_date, end_date, period="daily", adjust="qfq"):
        # ... 实现逻辑，失败时 raise ProviderError(...)
        pass
```

**2. 写入配置**

```yaml
# config/providers.yaml
providers:
  tushare:
    retry_count: 2
    circuit_breaker_threshold: 3
    cooldown_seconds: 600
```

**3. 在维度中注册**

```python
# 在对应维度的 __init__.py 中
from astock_analysis.providers.tushare import provider as tushare
register_provider("tushare", tushare)

# config/providers.yaml 的维度列表中加入 tushare
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ASTOCK_CONFIG` | 配置文件路径 | 自动搜索 `config/providers.yaml` |
| `STOCK_CACHE_DB` | SQLite 缓存数据库路径 | `~/.astock_analysis/cache.db` |
| `STOCK_NO_CACHE` | 设为 `1` 禁用缓存 | 未设置（启用） |

## 运行测试

```bash
conda activate astock
cd /path/to/astock-analysis

# 运行不需要网络的单元测试
pytest tests/ -v -m "not network"

# 运行全部测试（含需要 akshare 网络的集成测试）
pytest tests/ -v
```

## 缓存

默认使用 SQLite 存储，数据库位于 `~/.astock_analysis/cache.db`。TTL 分级：

| 级别 | TTL | 适用数据 |
|------|-----|---------|
| `TTL_REALTIME` | 60s | 实时报价 |
| `TTL_INTRADAY` | 5min | 盘中 K 线、资金流向 |
| `TTL_HOURLY` | 1h | 新闻 |
| `TTL_DAILY` | 2h | 龙虎榜、北向资金 |
| `TTL_QUARTERLY` | 24h | 财报、研报 |
| `TTL_STATIC` | 7d | 行业分类、股票元数据 |

## 项目结构

```
astock-analysis/
├── pyproject.toml
├── config/
│   └── providers.yaml              # Provider 配置 + 维度路由
├── src/astock_analysis/
│   ├── core/
│   │   ├── cache.py                # SQLite 分级缓存
│   │   ├── config.py               # YAML 配置加载
│   │   └── chain.py                # try_chain 引擎
│   ├── providers/
│   │   └── akshare.py              # Akshare provider
│   └── dimensions/
│       └── kline/
│           ├── __init__.py          # K 线路由
│           └── types.py             # KlineResponse TypedDict
├── tests/
│   └── test_core.py
└── examples/
    └── basic_usage.py
```

## License

MIT
