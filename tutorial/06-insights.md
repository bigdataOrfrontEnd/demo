# 模块 06: 深度洞察 (Insights)

> **API 前缀**: `/api/insights`  
> **源码**: `src/web/api/insights.py`  
> **认证要求**: 是

## 模块概述

Insights 是一个聚合端点，将行情、K线摘要、AI 建议打包到一起返回。主要用于前端详情弹窗，一次请求获取所有需要的上下文数据。

## API 端点

### POST /api/insights/batch

聚合返回行情 + K线摘要 + 最新 AI 建议。

**请求体**:
```json
{
  "items": [
    {"symbol": "600519", "market": "CN"},
    {"symbol": "300418", "market": "CN"}
  ]
}
```

**响应**:
```json
[
  {
    "symbol": "600519",
    "market": "CN",
    "quote": {
      "name": "贵州茅台",
      "current_price": 1680.50,
      "change_pct": 1.23,
      "open_price": 1665.00,
      "high_price": 1685.00,
      "low_price": 1660.00,
      "volume": 1234567,
      "turnover": 2073645000.00
    },
    "kline_summary": {
      "trend": "上涨趋势",
      "macd_status": "金叉",
      "rsi_14": 65.2,
      "support_level": 1600.0,
      "resistance_level": 1720.0
    },
    "suggestion": {
      "action": "hold",
      "action_label": "持有",
      "signal": "趋势向好，MACD金叉",
      "reason": "股价在5日均线上方运行...",
      "agent_name": "intraday_monitor",
      "agent_label": "盘中监测"
    }
  }
]
```

## 实现细节

1. **行情** — 通过腾讯行情 API 批量拉取，按市场分组
2. **K线摘要** — 逐只获取，带 60 秒内存缓存避免重复计算
3. **建议** — 从建议池 (`stock_suggestions` 表) 读取最新有效建议

## 使用场景

- 前端 `InsightPanel` 或股票详情弹窗
- 一次 HTTP 请求满足详情页所有数据需求
- 减少前端多次轮流调用的复杂度
