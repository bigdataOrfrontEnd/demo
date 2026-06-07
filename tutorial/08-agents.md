# 模块 08: Agent 管理 (Agents)

> **API 前缀**: `/api/agents`  
> **源码**: `src/web/api/agents.py`  
> **认证要求**: 是  
> **数据库表**: `agent_configs`, `agent_runs`

## 模块概述

Agent 管理模块是 PanWatch 调度系统的核心入口，提供 Agent 配置 CRUD、手动触发、历史记录、进度查询等功能。同时包含盘中扫描 (`/api/agents/intraday/scan`) 接口。

## Agent 分类

| 类型 | kind 值 | 说明 |
|------|---------|------|
| workflow | `workflow` | 参与定时调度，可绑定到股票 |
| capability | `capability` | 内部能力，仅手动调用，不参与调度 |

## 核心概念

### AgentConfig
定义 Agent 的元数据：名称、调度表达式、执行模式、AI 模型和通知渠道默认配置。

### 执行模式
- **batch**: 批量模式，多只股票一起发送给 AI 分析
- **single**: 单只模式，逐只分析并分别通知

### 解析优先级 (AI 模型/通知渠道)
```
stock_agent 级别覆盖 → agent 默认 → 系统默认 (is_default=True) → 第一个
```

## API 端点

### GET /api/agents

获取 Agent 列表。

**参数**:
- `include_internal` (query, default false) — 是否包含内部能力 Agent

### GET /api/agents/capabilities

获取所有 `capability` 类型 Agent。

### PUT /api/agents/{agent_name}

更新 Agent 配置。

**请求体**:
```json
{
  "enabled": true,
  "schedule": "30 15 * * 1-5",
  "ai_model_id": 1,
  "notify_channel_ids": [1],
  "config": {"max_stocks": 10},
  "visible": true
}
```

### GET /api/agents/health

调度健康概览。返回每个 Agent 的调度状态、下次执行时间、最近一次执行结果。

**响应**:
```json
{
  "timezone": "Asia/Shanghai",
  "summary": {
    "next_24h_count": 12,
    "recent_failed_count": 1
  },
  "agents": [
    {
      "name": "daily_report",
      "display_name": "盘后日报",
      "enabled": true,
      "schedule": "30 15 * * 1-5",
      "next_runs": ["2026-05-21T15:30:00+08:00"],
      "last_run": {
        "status": "success",
        "created_at": "2026-05-20T15:30:05+08:00",
        "duration_ms": 45200
      }
    }
  ]
}
```

### GET /api/agents/schedule/preview

预览 schedule 表达式接下来几次触发时间。

### POST /api/agents/{agent_name}/trigger

手动触发 Agent（批量执行）。

**参数**:
- `wait` (query, default false) — 同步等待

### 盘中扫描

#### POST /api/agents/intraday/scan

实时扫描盘中监测 Agent 关联的股票。

**参数**:
- `analyze` (query, default false) — 是否调用 AI 分析

**响应** (analyze=false):
```json
{
  "stocks": [
    {
      "symbol": "600519",
      "name": "贵州茅台",
      "market": "CN",
      "current_price": 1680.50,
      "change_pct": 1.23,
      "alert_type": null,
      "has_position": true,
      "pnl_pct": 5.03,
      "kline": {"trend": "上涨趋势", ...},
      "suggestion": null
    }
  ],
  "scanned_count": 5,
  "total_watchlist_count": 10,
  "skipped_not_trading_count": 5,
  "is_trading": true,
  "has_watchlist": true
}
```

### 历史与进度

#### GET /api/agents/{agent_name}/history

获取 Agent 执行历史。

**参数**: `limit` (default 20)

#### GET /api/agents/runs/{trace_id}/progress

查询单次 Agent 执行的进度（用于 TradingAgents 等长耗时 Agent）。

**响应**:
```json
{
  "trace_id": "man-tradingagents-300418-...",
  "status": "running",
  "current_stage": "market_analysis",
  "elapsed_sec": 45.2,
  "total_cost_usd": 0.03,
  "stages": [
    {"name": "data_collection", "status": "done"},
    {"name": "market_analysis", "status": "running"},
    {"name": "debate", "status": "pending"}
  ]
}
```

#### GET /api/agents/tradingagents/running

查询某只股票是否有在跑的 TradingAgents 任务。

#### GET /api/agents/tradingagents/latest

获取某只股票最近一次深度分析完整结果。

#### GET /api/agents/tradingagents/history-comparison

TradingAgents 历史决策 vs 实际涨跌对比。

#### GET /api/agents/tradingagents/budget

TradingAgents 本月预算使用情况。

## 调度预览机制

通过 `preview_schedule()` 函数解析 cron 表达式并按配置时区生成下次触发时间：

```python
runs = preview_schedule("30 15 * * 1-5", count=5, timezone="Asia/Shanghai")
# 返回接下来 5 次触发时间的 datetime 列表
```

## 使用场景

- 前端 Agent 设置页面，配置各 Agent 的调度时间和参数
- 健康检查面板查看调度状态
- 盘中扫描页面实时查看股票行情+技术分析
- DeepAnalysisModal 使用进度接口轮询 TradingAgents 执行状态
