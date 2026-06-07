# 模块 03: 自选股管理 (Stocks)

> **API 前缀**: `/api/stocks`  
> **源码**: `src/web/api/stocks.py`  
> **认证要求**: 是  
> **数据库表**: `stocks`, `stock_agents`

## 模块概述

自选股管理是 PanWatch 的核心模块，管理用户关注的股票列表，并将股票与 Agent 绑定。每只股票可以关联多个 Agent，每个绑定可独立配置 AI 模型和通知渠道。

## 数据模型

### Stock 表 (stocks)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| symbol | VARCHAR | 股票代码 |
| name | VARCHAR | 股票名称 |
| market | VARCHAR | 市场: CN/HK/US |
| sort_order | INTEGER | 排序权重 |

### StockAgent 表 (stock_agents)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| stock_id | FK(stocks) | 股票 ID |
| agent_name | VARCHAR | Agent 名称 |
| schedule | VARCHAR | 调度表达式 (覆盖默认) |
| ai_model_id | FK(ai_models) | AI 模型覆盖 |
| notify_channel_ids | JSON | 通知渠道 ID 列表覆盖 |

## API 端点

### GET /api/stocks

获取所有自选股列表。

**响应**：
```json
[
  {
    "id": 1,
    "symbol": "600519",
    "name": "贵州茅台",
    "market": "CN",
    "sort_order": 1,
    "agents": [
      {
        "agent_name": "daily_report",
        "schedule": "",
        "ai_model_id": null,
        "notify_channel_ids": []
      }
    ]
  }
]
```

### GET /api/stocks/search

模糊搜索股票（名称/代码）。

**参数**：
- `q` (string, required) — 搜索关键词
- `market` (string, optional) — 市场过滤

### POST /api/stocks/refresh-list

刷新股票列表缓存（从数据源重新拉取）。

**响应**：`{"count": 5120}`

### POST /api/stocks

添加自选股。

**请求体**：
```json
{
  "symbol": "000858",
  "name": "五粮液",
  "market": "CN"
}
```

**说明**：同市场同代码不可重复添加

### PUT /api/stocks/reorder

批量调整自选股排序。

**请求体**：
```json
{
  "items": [
    {"id": 1, "sort_order": 3},
    {"id": 2, "sort_order": 1}
  ]
}
```

### PUT /api/stocks/{stock_id}

更新股票名称。

### DELETE /api/stocks/{stock_id}

删除股票。

**前置条件**：需要先删除该股票的所有持仓（positions），否则返回 400。
自动清理：关联的 `stock_agents`、`price_alert_rules`、`price_alert_hits`。

### PUT /api/stocks/{stock_id}/agents

设置股票关联的 Agent 列表。

**请求体**：
```json
{
  "agents": [
    {
      "agent_name": "daily_report",
      "schedule": "30 15 * * 1-5",
      "ai_model_id": 2,
      "notify_channel_ids": [1]
    },
    {
      "agent_name": "intraday_monitor"
    }
  ]
}
```

**说明**：
- 全量替换模式：传入的列表完全替换该股票的所有 Agent 绑定
- 可对每个绑定独立覆盖 AI 模型和通知渠道
- 仅 `workflow` 类型的 Agent 可被绑定；`capability` 类型会返回 400

### POST /api/stocks/{stock_id}/agents/{agent_name}/trigger

手动触发单只股票的 Agent 分析。

**参数**：
- `stock_id` (path) — 股票 ID，传 `0` 可针对未关注的股票
- `agent_name` (path) — Agent 名称
- `bypass_throttle` (query) — 跳过节流限制
- `bypass_market_hours` (query) — 跳过交易时段限制
- `allow_unbound` (query) — 允许对未绑定股票触发
- `wait` (query) — 同步等待结果（默认异步）
- `force_refresh` (query) — 强制重跑（TradingAgents）

**异步模式响应**（默认）：
```json
{
  "queued": true,
  "trace_id": "man-intraday_monitor-600519-1716300000000",
  "message": "已提交后台执行"
}
```

**同步模式响应** (`wait=true`)：
```json
{
  "result": {
    "code": 0,
    "success": true,
    "message": "ok",
    "title": "...",
    "content": "...",
    "should_alert": true,
    "notified": true
  },
  "trace_id": "man-intraday_monitor-600519-1716300000000"
}
```

**无绑定模式** (`stock_id=0, allow_unbound=true`)：
- 可对未关注的股票进行一次性分析
- 默认禁用通知（仅生成建议）
- 需传 `symbol`、`market` 和 `name` 参数

### GET /api/stocks/quotes

获取所有自选股的实时行情（批量）。

**响应**：以 symbol 为 key 的行情对象 map：
```json
{
  "600519": {
    "current_price": 1680.50,
    "change_pct": 1.23,
    "change_amount": 20.50,
    "prev_close": 1660.00
  }
}
```

### GET /api/stocks/markets/status

获取各市场的交易状态。

**响应**：
```json
[
  {
    "code": "CN",
    "name": "A股",
    "status": "trading",
    "status_text": "交易中",
    "is_trading": true,
    "sessions": ["09:30-11:30", "13:00-15:00"],
    "local_time": "14:25",
    "timezone": "Asia/Shanghai"
  }
]
```

## 使用场景

- 前端 "自选股" 页面展示股票列表
- 为每只股票勾选需要激活的 Agent
- 手动触发某只股票的 AI 分析
- 调整关注列表的排序
