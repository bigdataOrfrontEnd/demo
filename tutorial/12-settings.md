# 模块 12: 系统设置 (Settings)

> **API 前缀**: `/api/settings`  
> **源码**: `src/web/api/settings.py`  
> **认证要求**: 是  
> **数据库表**: `app_settings`

## 模块概述

系统设置模块管理全局配置项。配置值可从环境变量读取默认值，也可通过 UI 覆盖并持久化到数据库。

## 配置项清单

| Key | 说明 | 默认值来源 |
|-----|------|-----------|
| `http_proxy` | HTTP 代理地址 | `.env` 的 `http_proxy` |
| `notify_quiet_hours` | 通知静默时段 | `.env` 的 `notify_quiet_hours` |
| `notify_retry_attempts` | 通知重试次数 | `.env` (默认 2) |
| `notify_retry_backoff_seconds` | 重试退避基数 | `.env` (默认 2.0) |
| `notify_dedupe_ttl_overrides` | 去重 TTL 覆盖 (JSON) | `.env` |
| `stock_link_platform` | 股票链接平台 | 默认 `xueqiu` |

## API 端点

### GET /api/settings

获取所有系统设置。

**响应**:
```json
[
  {
    "key": "http_proxy",
    "value": "http://127.0.0.1:7890",
    "description": "HTTP 代理地址"
  },
  {
    "key": "notify_quiet_hours",
    "value": "23:00-07:00",
    "description": "通知静默时间段（HH:MM-HH:MM，空为关闭）"
  }
]
```

### PUT /api/settings/{key}

更新单个设置。

**请求体**:
```json
{
  "value": "http://127.0.0.1:10809"
}
```

**特殊行为**: 更新 `http_proxy` 后会立即调用 `apply_proxy_env()` 实时生效，无需重启。

### GET /api/settings/version

获取应用版本号。

**响应**: `{"version": "2.1.0"}`

版本号读取优先级：`APP_VERSION` 环境变量 → `VERSION` 文件 → `"dev"`

### GET /api/settings/update-check

检查是否有新版本可用（通过 GitHub Releases API）。

**响应**:
```json
{
  "success": true,
  "current": "2.1.0",
  "latest": "2.2.0",
  "is_update_available": true,
  "release_url": "https://github.com/...",
  "published_at": "2026-05-15"
}
```

## 静默时段配置

格式：`HH:MM-HH:MM`，支持跨夜（如 `23:00-07:00`）。在静默时段内，Agent 执行后会跳过通知推送（仅记录日志）。

```python
# 例如：NotifyPolicy.is_quiet_now() 返回 True 时跳过通知
if policy.is_quiet_now():
    # 记录 "notify_skipped: quiet_hours"
    return
```

## 通知去重 TTL

可针对不同 Agent 设置不同的去重窗口：

```json
{
  "news_digest": 60,
  "daily_report": 720,
  "intraday_monitor": 15
}
```
单位：分钟。同一 Agent 在同一 TTL 内相同内容的通知不会重复发送。
