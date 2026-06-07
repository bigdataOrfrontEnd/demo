# 模块 17: AI 对话助手 (Chat)

> **API 前缀**: `/api/chat`  
> **源码**: `src/web/api/chat.py`  
> **认证要求**: 是  
> **数据库表**: `chat_conversations`, `chat_messages`

## 模块概述

AI 对话助手是一个内嵌的 AI Chat 功能，支持多轮对话、上下文注入（持仓+行情+建议）、Tool Use（工具调用）自动获取数据。

## 特点

- **上下文感知**: 自动注入持仓、行情、K线摘要、AI 建议
- **Tool Use**: AI 可自动调用工具获取实时数据（如 `get_stock_quote`）
- **多会话**: 支持多个独立对话，可按股票关联

## 数据模型

### ChatConversation (chat_conversations)
| 字段 | 说明 |
|------|------|
| title | 对话标题（首条消息前20字） |
| stock_symbol | 关联的股票代码 |
| stock_market | 关联的市场 |
| ai_model_id | 使用的 AI 模型 |
| initial_context | 前端页面快照 |

### ChatMessage (chat_messages)
| 字段 | 说明 |
|------|------|
| conversation_id | 所属对话 |
| role | user/assistant/system |
| content | 消息内容 |

## 可用工具 (Tool Use)

AI 可主动调用以下工具：

| 工具名 | 功能 |
|--------|------|
| `get_portfolio` | 获取实盘+模拟盘持仓 |
| `get_stock_quote` | 获取单只股票实时行情 |
| `get_technical_analysis` | 获取技术面分析 |
| `get_stock_suggestions` | 获取 AI 建议和历史报告 |
| `get_watchlist` | 获取自选股列表 |

## API 端点

### GET /api/chat/suggested-questions

根据股票当前状态生成推荐问题（不调用 AI）。

**参数**: `symbol`, `market`

**响应**:
```json
{
  "questions": [
    "最新的「持有」信号可靠吗？入场时机如何？",
    "现在适合建仓吗？",
    "分析近期走势和关键支撑压力位",
    "有什么值得关注的消息或事件？"
  ]
}
```

### POST /api/chat/conversations

创建新对话。

**请求体**:
```json
{
  "stock_symbol": "600519",
  "stock_market": "CN",
  "initial_context": "{\"current_price\":1680.50,...}"
}
```

### GET /api/chat/conversations

获取对话列表。

### GET /api/chat/conversations/{conversation_id}

获取对话详情（含消息列表）。

### DELETE /api/chat/conversations/{conversation_id}

删除对话。

### POST /api/chat/conversations/{conversation_id}/messages

发送消息并获取 AI 回复。

**请求体**:
```json
{
  "content": "茅台现在值得买入吗？"
}
```

**响应**:
```json
{
  "id": 25,
  "role": "assistant",
  "content": "根据当前数据分析...",
  "created_at": "2026-05-21T10:30:00"
}
```

## Tool Use 流程

```
用户发问
  → 构建消息列表 (system + history + context)
  → AI 判断是否需要工具数据
  → 如有 tool_calls:
      → 执行工具 (get_portfolio / get_stock_quote 等)
      → 将工具结果追加到消息列表
      → 再次调用 AI (最多 5 轮)
  → 返回最终回复
```

## 上下文注入

每次对话自动在 system message 中注入：

1. **用户持仓** — 实盘 + 模拟盘所有持仓
2. **绑定股票行情** — 如有关联股票，自动获取实时行情
3. **绑定股票技术面** — K线摘要
4. **绑定股票建议** — 最新 AI 建议和分析报告
5. **前端页面快照** — 对话创建时传入

## 使用场景

- 前端 AI 对话面板
- 股票详情页内嵌对话
- 快速问答"某股票该不该买"
