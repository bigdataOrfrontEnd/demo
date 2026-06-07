# 模块 04: 实时行情 (Quotes)

> **API 前缀**: `/api/quotes`  
> **源码**: `src/web/api/quotes.py`  
> **核心类**: `src/core/providers.py` → `QuoteOrchestrator`  
> **认证要求**: 是

## 模块概述

实时行情模块提供单只或批量股票的最新行情数据，包括价格、涨跌幅、成交量、市值等。采用编排器 (Orchestrator) 模式聚合多个行情数据源。

## API 端点

### GET /api/quotes/{symbol}

获取单只股票实时行情。

**参数**：
- `symbol` (path) — 股票代码
- `market` (query, default "CN") — 市场

**响应**：
```json
{
  "symbol": "600519",
  "market": "CN",
  "name": "贵州茅台",
  "current_price": 1680.50,
  "change_pct": 1.23,
  "change_amount": 20.50,
  "prev_close": 1660.00,
  "open_price": 1665.00,
  "high_price": 1685.00,
  "low_price": 1660.00,
  "volume": 1234567,
  "turnover": 2073645000.00,
  "turnover_rate": 0.35,
  "pe_ratio": 32.5,
  "total_market_value": 2100000000000.00,
  "circulating_market_value": 2100000000000.00
}
```

### POST /api/quotes/batch

批量获取多只股票实时行情。

**请求体**：
```json
{
  "items": [
    {"symbol": "600519", "market": "CN"},
    {"symbol": "00700", "market": "HK"},
    {"symbol": "AAPL", "market": "US"}
  ]
}
```

**响应**：数组中每项格式同单只查询。

## 行情数据来源

行情通过 `QuoteOrchestrator` 编排器统一管理，按优先级尝试多个数据源：

| 数据源 | 提供商 | 适用市场 | 类型 |
|--------|--------|----------|------|
| 腾讯行情 | tencent | CN/HK/US | 默认最高优先级 |
| YFinance 行情 | yfinance | HK/US | 备选 |

## 数据流

```
POST /api/quotes/batch
  → 解析请求 items 按市场分组
  → 调用 get_quote_orchestrator()
  → Orchestrator 遍历数据源（按优先级）
  → 对每个数据源: ProviderRequest → fetch()
  → 命中则返回，失败则尝试下一个数据源
  → 聚合结果返回
```

## 行情数据完整字段

| 字段 | 说明 |
|------|------|
| name | 股票名称 |
| current_price | 当前价 |
| change_pct | 涨跌幅 (%) |
| change_amount | 涨跌额 |
| prev_close | 昨收价 |
| open_price | 开盘价 |
| high_price | 最高价 |
| low_price | 最低价 |
| volume | 成交量 (股) |
| turnover | 成交额 |
| turnover_rate | 换手率 (%) |
| pe_ratio | 市盈率 |
| total_market_value | 总市值 |
| circulating_market_value | 流通市值 |

## 腾讯行情 API

底层通过 `_fetch_tencent_quotes()` 拉取，腾讯 symbol 格式：

| 市场 | 格式 | 示例 |
|------|------|------|
| CN (上海) | sh + 代码 | sh600519 |
| CN (深圳) | sz + 代码 | sz000858 |
| HK | hk + 代码 (4位补齐) | hk00700 |
| US | us + 代码 | usAAPL |

数据接口：`http://qt.gtimg.cn/q=sh600519,sz000858`

## 使用场景

- 前端行情页面实时展示价格
- 持仓页计算浮盈浮亏
- Agent 执行前获取最新行情
- 价格提醒扫描时获取触发数据
