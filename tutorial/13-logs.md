# 模块 13: 日志中心 (Logs)

> **API 前缀**: `/api/logs`  
> **源码**: `src/web/api/logs.py`  
> **认证要求**: 是  
> **数据库表**: `log_entries`

## 模块概述

日志中心将应用所有运行日志持久化到数据库，提供强大的查询、筛选和分析能力。同时支持控制台输出，两者级别独立控制。

## 日志架构

```
root logger (DEBUG)
├── 控制台 handler (WARNING+ for 三方库, INFO+ for 业务)
│   └── _ConsoleNoiseFilter: 过滤 httpx/urllib3/apscheduler INFO/DEBUG
└── DB handler (DEBUG 全量)
    └── DBLogHandler: 写入 log_entries 表, 缓冲 2 秒批量写入
```

## 数据模型

### LogEntry 表 (log_entries)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| timestamp | DATETIME | 日志时间 |
| level | VARCHAR | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| logger_name | VARCHAR | Logger 名称 |
| message | TEXT | 日志消息 |
| trace_id | VARCHAR | 链路追踪 ID |
| run_id | VARCHAR | 运行 ID |
| agent_name | VARCHAR | Agent 名称 |
| event | VARCHAR | 事件类型 |
| tags | JSON | 结构化标签 |
| notify_status | VARCHAR | 通知状态 |
| notify_reason | VARCHAR | 通知跳过原因 |

### 索引
- `(timestamp, id)` — 按时间范围查询
- `(trace_id)` — 按链路追踪查询
- `(agent_name, event)` — 按 Agent 和事件查询

## API 端点

### GET /api/logs

查询日志列表，支持丰富筛选。

**参数**:
- `level` (query) — 级别过滤，逗号分隔: `ERROR,WARNING`
- `q` (query) — 关键词搜索（查 message/logger/trace_id/agent/event）
- `logger` (query) — Logger 名称过滤
- `trace_id` (query) — 链路追踪 ID
- `agent_name` (query) — Agent 名称
- `event` (query) — 事件类型过滤
- `notify_status` (query) — 通知状态: attempted/skipped/sent/failed
- `domain` (query) — 日志域: all/business/infra
- `since` (query) — 起始时间 (ISO 格式)
- `until` (query) — 结束时间 (ISO 格式)
- `limit` (query, default 200, max 1000)
- `offset` (query, default 0)
- `before_id` (query) — cursor 分页

**响应**:
```json
{
  "items": [
    {
      "id": 12345,
      "timestamp": "2026-05-21T15:30:05+08:00",
      "level": "INFO",
      "logger_name": "src.agents.daily_report",
      "message": "Agent [盘后日报] 开始执行",
      "trace_id": "schedule-daily_report-xxx",
      "agent_name": "daily_report",
      "event": "trigger"
    }
  ],
  "total": 50000,
  "has_more": true,
  "next_before_id": 12300
}
```

### DELETE /api/logs

清空所有日志。

### GET /api/logs/meta

日志元数据统计（级别分布、Logger 分布、事件分布）。

### GET /api/logs/health

日志存储健康检查。

## 事件类型

Agent 执行过程中会记录以下事件：

| event | 含义 |
|-------|------|
| `trigger` | Agent 被触发 |
| `collect_start` / `collect_done` | 数据采集 |
| `notify_send` | 通知开始发送 |
| `notify_sent` | 通知发送成功 |
| `notify_failed` | 通知发送失败 |
| `notify_skipped` | 通知被跳过 (quiet_hours/deduped/suppressed) |
| `ta_progress` | TradingAgents 阶段进度 |
| `ta_toolkit` | TradingAgents 工具调用诊断 |

## 日志域

- **all**: 所有日志
- **business**: 仅业务日志（排除 infra）
- **infra**: 仅基础设施日志（httpx/sqlalchemy/uvicorn）
