# 模块 05: K线数据 (Klines)

> **API 前缀**: `/api/klines`  
> **源码**: `src/web/api/klines.py`  
> **核心类**: `src/collectors/kline_collector.py` → `KlineCollector`  
> **认证要求**: 是

## 模块概述

K线模块提供历史 K线数据和技术分析摘要，支持日线/周线/月线聚合。

## API 端点

### GET /api/klines/{symbol}

获取单只股票 K线数据。

**参数**:
- `symbol` (path) — 股票代码
- `market` (query, default "CN")
- `days` (query, default 60) — K线条数
- `interval` (query, default "1d") — 周期: 1d/1w/1m

**响应**:
```json
{
  "symbol": "600519",
  "market": "CN",
  "days": 60,
  "interval": "1d",
  "klines": [
    {
      "date": "2026-05-20",
      "open": 1650.00,
      "close": 1680.50,
      "high": 1685.00,
      "low": 1645.00,
      "volume": 2345678
    }
  ]
}
```

### POST /api/klines/batch

批量获取多只股票 K线。

**请求体**:
```json
{
  "items": [
    {"symbol": "600519", "market": "CN", "days": 60, "interval": "1d"},
    {"symbol": "300750", "market": "CN", "days": 30, "interval": "1w"}
  ]
}
```

### GET /api/klines/{symbol}/summary

获取单只股票技术分析摘要。

**响应**:
```json
{
  "symbol": "600519",
  "market": "CN",
  "summary": {
    "trend": "上涨趋势",
    "macd_status": "金叉",
    "rsi_14": 65.2,
    "support_level": 1600.0,
    "resistance_level": 1720.0,
    "volume_ratio": 1.35,
    "ma_5": 1670.0,
    "ma_20": 1630.0,
    "ma_60": 1550.0,
    "boll_upper": 1720.0,
    "boll_lower": 1580.0
  }
}
```

### POST /api/klines/summary/batch

批量获取 K线摘要。

**请求体**:
```json
{
  "items": [
    {"symbol": "600519", "market": "CN"},
    {"symbol": "300750", "market": "CN"}
  ]
}
```

## 周线/月线聚合

当 `interval` 设置为 `1w` 或 `1m` 时，后端会对日线数据做聚合：

```
日线 → 按 ISO 周 / 年月分组
     → 取首开、尾收、最高、最低、总成交量
     → 返回聚合后的 K线
```

## 数据来源

K线数据通过 `KlineCollector` 获取，当前主要使用腾讯 K线接口。配置的其他数据源（Tushare、YFinance）按优先级可用于备选。

## 使用场景

- 前端 K线图表组件
- Agent 分析中的技术面数据
- 策略引擎中的技术指标计算
