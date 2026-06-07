# 模块 14: 分析历史 (History)

> **API 前缀**: `/api/history`  
> **源码**: `src/web/api/history.py`  
> **认证要求**: 是  
> **数据库表**: `analysis_history`

## 模块概述

分析历史模块管理所有 Agent 产生的分析报告，支持按 Agent、股票、日期筛选和全文查看。

## 数据模型

### AnalysisHistory 表 (analysis_history)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| agent_name | VARCHAR | Agent 名称 |
| stock_symbol | VARCHAR | 股票代码 (`*` 表示市场分析) |
| analysis_date | VARCHAR | 分析日期 (YYYY-MM-DD) |
| title | VARCHAR | 分析标题 |
| content | TEXT | AI 分析正文 |
| raw_data | JSON | 附加数据快照 |
| agent_kind_snapshot | VARCHAR | Agent 类型快照 |

唯一约束：`(agent_name, stock_symbol, analysis_date)`

## raw_data 内容

`raw_data` 字段是 JSON，存储分析附带的上下文：

- `suggestions`: 各股票的操作建议
- `news`: 关联的新闻列表
- `quality_overview`: 数据质量评分
- `context_summary`: 上下文摘要
- `context_payload`: 完整上下文负载
- `prompt_context`: 发送给 AI 的 prompt 全文
- `prompt_stats`: prompt 统计（token 数等）
- `news_debug`: 新闻采集调试信息

## API 端点

### GET /api/history

获取分析历史列表。

**参数**:
- `agent_name` (query, optional) — 如 `daily_report`
- `stock_symbol` (query, optional) — 如 `600519`
- `kind` (query, default "workflow") — Agent 类型过滤
- `limit` (query, default 30, max 100)

**响应**:
```json
[
  {
    "id": 1,
    "agent_name": "daily_report",
    "agent_kind": "workflow",
    "stock_symbol": "600519",
    "analysis_date": "2026-05-20",
    "title": "【盘后日报】贵州茅台",
    "content": "## 今日总结\n...",
    "suggestions": {
      "600519": {
        "action": "hold",
        "action_label": "持有",
        "reason": "..."
      }
    },
    "created_at": "2026-05-20T15:31:00+08:00"
  }
]
```

### GET /api/history/{history_id}

获取单条分析详情（含完整 raw_data）。

### DELETE /api/history/{history_id}

删除单条记录。

## 数据写入时机

每次 Agent 执行完成后，通过 `record_agent_run()` 和 `save_analysis()` 函数写入：

```
Agent.run() 完成
  → record_agent_run() → agent_runs 表 (执行记录)
  → save_analysis()    → analysis_history 表 (分析内容)
  → save_suggestion()  → stock_suggestions 表 (建议)
```

## 使用场景

- 前端历史记录页面，按 Agent 类型分组查看
- 股票详情页展示该股票的历史分析报告
- 回看旧报告，追踪决策准确率
