# astock-analysis 项目结构

## 目录树

```
astock-analysis/
├── .gitignore
├── pyproject.toml                       # 项目元数据、依赖、工具配置
├── README.md                            # 使用文档
├── docs/
│   └── STRUCTURE.md                     # 本文件 — 项目结构示意图
├── config/
│   └── providers.yaml                   # Provider 重试/熔断配置 + 维度路由表
├── src/astock_analysis/
│   ├── __init__.py                      # 包标识
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cache.py                     # SQLite 分级缓存（6 级 TTL）
│   │   ├── config.py                    # YAML → AppConfig dataclass 加载
│   │   └── chain.py                     # try_chain 故障转移引擎（重试+熔断+退避）
│   ├── providers/
│   │   ├── __init__.py
│   │   └── akshare.py                   # AkshareProvider → 东方财富 / 腾讯备用
│   └── dimensions/
│       ├── __init__.py
│       └── kline/
│           ├── __init__.py              # fetch_kline() 维度路由入口
│           └── types.py                 # KlineRecord / KlineResponse TypedDict
├── tests/
│   ├── __init__.py
│   └── test_core.py                     # 配置 / 缓存 / K 线集成测试
└── examples/
    └── basic_usage.py                   # MVP 端到端演示脚本
```

## 模块依赖关系

```
                    ┌─────────────────────────┐
                    │   dimensions/kline/      │
                    │   fetch_kline()          │
                    │   (公共 API 入口)         │
                    └────────────┬────────────┘
                                 │ 调用
                    ┌────────────▼────────────┐
                    │   core/chain.py          │
                    │   try_chain()            │
                    │   • 按优先级遍历 provider │
                    │   • 指数退避重试          │
                    │   • 熔断器检查            │
                    │   • 故障转移链            │
                    └──┬──────────┬───────────┘
                       │ 调用      │ 读取
          ┌────────────▼──┐  ┌────▼──────────┐
          │ providers/     │  │ core/config.py │
          │ akshare.py     │  │ AppConfig      │
          │ • 东方财富(主)  │  │ • providers    │
          │ • 腾讯(备用)    │  │ • dimensions   │
          └───────┬───────┘  └────┬──────────┘
                  │               │ 读取
                  │          ┌────▼──────────┐
                  │          │ config/        │
                  │          │ providers.yaml │
                  │          └───────────────┘
          ┌───────▼──────────┐
          │ core/cache.py     │
          │ • JSON 序列化     │
          │ • DataFrame 支持  │
          │ • 6 级 TTL        │
          └──────┬───────────┘
                 │
          ┌──────▼──────────┐
          │ SQLite           │
          │ ~/.astock_       │
          │ analysis/cache.db│
          └─────────────────┘
```

## 一次完整调用流程

```
用户代码
  │
  │  fetch_kline("600519", "2026-05-26", "2026-06-25")
  ▼
dimensions/kline/__init__.py
  │
  │  try_chain(method_name="fetch_kline", dimension="kline", ...)
  ▼
core/chain.py :: try_chain()
  │
  │  1. 读取 config → 获取 kline 维度的 provider 列表: [akshare]
  │  2. 检查 akshare 熔断器 → 未开启
  │  3. 调用 akshare.fetch_kline(code, start, end, period, adjust)
  ▼
providers/akshare.py :: fetch_kline()
  │
  │  1. 尝试 stock_zh_a_hist() → 东方财富 push2his API 不可用
  │  2. 捕获异常 → 日志警告
  │  3. 回退 _fetch_kline_tencent() → proxy.finance.qq.com ✓
  │  4. 解析 JSONP → 标准化列名 → 返回 DataFrame
  ▼
core/chain.py
  │
  │  • 成功 → 重置熔断器 → 返回 (DataFrame, "akshare")
  │  • 若本层配置了 cache_ttl → 写入/读取 SQLite 缓存
  ▼
dimensions/kline/__init__.py
  │
  │  • DataFrame → list[KlineRecord]
  │  • 组装 KlineResponse { records, provider, code, ... }
  ▼
返回给用户代码
```

## 核心类与关系

```
┌──────────────────────────────────────────────────┐
│ AppConfig (core/config.py)                       │
├──────────────────────────────────────────────────┤
│ + providers: dict[str, ProviderConfig]           │
│ + dimensions: dict[str, DimensionConfig]         │
│ + cache_enabled: bool                            │
│ + get_provider(name) → ProviderConfig | None     │
│ + get_dimension(name) → DimensionConfig | None   │
└──────────┬───────────────────────┬───────────────┘
           │ 包含                   │ 包含
┌──────────▼──────────┐  ┌─────────▼─────────────┐
│ ProviderConfig      │  │ DimensionConfig        │
├─────────────────────┤  ├────────────────────────┤
│ + name: str         │  │ + name: str            │
│ + retry_count: int  │  │ + providers: list[str] │
│ + backoff_base: f32 │  └────────────────────────┘
│ + cb_threshold: int │
│ + cooldown_sec: int │
└─────────────────────┘

┌──────────────────────────────────────────┐
│ CircuitBreaker (core/chain.py)           │
├──────────────────────────────────────────┤
│ + _failures: dict[str, int]             │
│ + _open_until: dict[str, float]         │
│ + record_failure(name, cooldown)        │
│ + record_success(name)                  │
│ + is_open(name, threshold, cooldown)    │
│ + open_circuit(name, cooldown)          │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ AkshareProvider (providers/akshare.py)   │
├──────────────────────────────────────────┤
│ + name = "akshare"                       │
│ + requires_key = False                   │
│ + markets = ("A",)                       │
│ + fetch_kline(code, start, end, ...)     │
│ - _fetch_kline_eastmoney(...)            │
│ - _fetch_kline_tencent(...)              │
│ - _standardize_columns(df, source)       │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ KlineRecord / KlineResponse              │
│ (dimensions/kline/types.py)              │
├──────────────────────────────────────────┤
│ KlineRecord:                             │
│   date, open, high, low, close,          │
│   volume, amount, pct_chg                │
│ KlineResponse:                           │
│   records, provider, code,               │
│   start_date, end_date                   │
└──────────────────────────────────────────┘
```

## 数据流向图

```
providers.yaml ──加载──► AppConfig ──注入──► try_chain()
                                                  │
                                                  │ 按维度选择 provider 链
                                                  ▼
                                          AkshareProvider
                                          ┌──────┬──────┐
                                          │ 东方财富 │ 腾讯  │
                                          │ (主)    │ (备用)│
                                          └──────┬──────┘
                                                 │
                                                 ▼
                                           DataFrame
                                          (标准化列名)
                                                 │
                                   ┌─────────────┴─────────────┐
                                   │ 若 cache_ttl ≠ None       │
                                   │ → 写入/读取 SQLite 缓存   │
                                   └─────────────┬─────────────┘
                                                 │
                                                 ▼
                                          list[KlineRecord]
                                                 │
                                                 ▼
                                          KlineResponse
                                          (返回给调用方)
```

## 缓存 TTL 分级

| 常量 | 时长 | 适用场景 |
|------|------|---------|
| `TTL_REALTIME` | 60s | 实时报价 |
| `TTL_INTRADAY` | 5 min | 盘中 K 线、资金流向 |
| `TTL_HOURLY` | 1 h | 新闻 |
| `TTL_DAILY` | 2 h | 龙虎榜、北向资金 |
| `TTL_QUARTERLY` | 24 h | 财报、研报 |
| `TTL_STATIC` | 7 d | 行业分类、元数据 |

## 扩展点

```
新增维度:
  dimensions/{name}/
  ├── __init__.py    ← fetch_{name}() 入口, 调用 try_chain
  └── types.py       ← TypedDict 定义

新增 Provider:
  providers/{name}.py
  ├── class XxxProvider:
  │     name = "..."
  │     def fetch_{dimension}(self, ...): ...
  └── provider = XxxProvider()  ← 单例

  config/providers.yaml:
    providers.{name}: 重试/熔断配置
    dimensions.{dim}.providers: 加入 {name}
```
