# 模块 16: AI 建议池 (Suggestions)

> **API 前缀**: `/api/suggestions`  
> **源码**: `src/web/api/suggestions.py` + `src/core/suggestion_pool.py`  
> **认证要求**: 是  
> **数据库表**: `stock_suggestions`

## 模块概述

建议池汇总所有 Agent 在各次执行中产生的操作建议，是前端"AI 建议"面板的数据来源。建议有时效性，过期自动清理。

## 数据模型

### StockSuggestion 表 (stock_suggestions)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| stock_symbol | VARCHAR | 股票代码 |
| stock_market | VARCHAR | 市场 |
| stock_name | VARCHAR | 股票名称 |
| action | VARCHAR | 操作: buy/add/reduce/sell/hold/watch/alert/avoid |
| action_label | VARCHAR | 中文标签: 建仓/加仓/减仓/清仓/持有/观望 |
| signal | VARCHAR | 信号描述 |
| reason | VARCHAR | 建议理由 |
| agent_name | VARCHAR | 来源 Agent |
| agent_label | VARCHAR | Agent 中文标签 |
| prompt_context | TEXT | Prompt 上下文摘要 |
| ai_response | TEXT | AI 原始响应 |
| expires_at | DATETIME | 过期时间 |

## API 端点

### GET /api/suggestions/{symbol}

获取某只股票的所有建议。

**参数**:
- `market` (query, optional) — 市场代码
- `include_expired` (query, default false)
- `limit` (query, default 10)

### GET /api/suggestions

获取所有股票的最新建议（每只股票仅返回最新一条有效建议）。

**参数**:
- `symbols` (query, optional) — 逗号分隔的股票代码
- `stock_keys` (query, optional) — 格式 `CN:600519,HK:00700,US:AAPL`
- `include_expired` (query, default false)

### DELETE /api/suggestions/cleanup

清理过期建议。

**参数**: `days` (query, default 7)

## 建议操作类型

| action | 中文 | 含义 |
|--------|------|------|
| buy | 建仓 | 买入新仓位 |
| add | 加仓 | 增持现有仓位 |
| reduce | 减仓 | 减持现有仓位 |
| sell | 清仓 | 全部卖出 |
| hold | 持有 | 继续持有 |
| watch | 观望 | 暂不操作，关注 |
| alert | 提醒 | 触发异动警告 |
| avoid | 回避 | 建议回避 |

## 建议生命周期

```
Agent 产生建议
  → save_suggestion() 写入 stock_suggestions
  → 设置 expires_at (默认 6 小时)
  → 前端读取展示
  → 过期后定期清理 (cleanup_expired_suggestions)
```

## 使用场景

- 持仓页面的建议徽章展示
- 股票详情弹窗显示 AI 操作建议
- 建议历史追踪
