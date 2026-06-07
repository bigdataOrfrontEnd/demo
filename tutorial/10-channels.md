# 模块 10: 通知渠道 (Channels)

> **API 前缀**: `/api/channels`  
> **源码**: `src/web/api/channels.py`  
> **认证要求**: 是  
> **数据库表**: `notify_channels`

## 模块概述

通知渠道管理模块用于配置消息推送渠道。当前支持 Telegram，架构设计上可扩展其他渠道。

## 数据模型

### NotifyChannel 表 (notify_channels)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 渠道名称 |
| type | VARCHAR | 渠道类型 (telegram) |
| config | JSON | 渠道配置参数 |
| enabled | BOOLEAN | 是否启用 |
| is_default | BOOLEAN | 是否系统默认 |

Telegram 渠道的 `config` 格式：
```json
{
  "bot_token": "123456:ABC-DEF",
  "chat_id": "123456789"
}
```

## API 端点

### GET /api/channels

获取所有通知渠道。

### GET /api/channels/types

获取支持的渠道类型及其配置字段说明。

### POST /api/channels

创建通知渠道。

**请求体**:
```json
{
  "name": "Telegram",
  "type": "telegram",
  "config": {
    "bot_token": "xxx",
    "chat_id": "xxx"
  },
  "enabled": true,
  "is_default": true
}
```

### PUT /api/channels/{channel_id}

更新渠道信息。

### DELETE /api/channels/{channel_id}

删除渠道。

### POST /api/channels/{channel_id}/test

发送测试通知。

**响应**:
```json
{
  "ok": true,
  "message": "测试通知发送成功"
}
```
失败时返回 500 并附带错误信息。

## 渠道选择优先级

```
1. StockAgent 级别: 股票-Agent 绑定中指定的 notify_channel_ids
2. AgentConfig 级别: Agent 设置的默认 notify_channel_ids
3. 系统默认: notify_channels 中 is_default=true 且 enabled=true
```

## 通知流程

```
Agent.run() 
  → should_notify() 判断
  → 静默时段检查 (notify_quiet_hours)
  → 去重检查 (per-agent TTL)
  → NotifierManager.notify_with_result()
    → 遍历所有启用的渠道
    → 逐个发送
    → 记录 send 结果
  → 写入通知日志
```
