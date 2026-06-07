# 模块 18: 价格提醒 (Price Alerts)

> **API 前缀**: `/api/price-alerts`  
> **源码**: `src/web/api/price_alerts.py` + `src/core/price_alert_engine.py`  
> **认证要求**: 是  
> **数据库表**: `price_alert_rules`, `price_alert_hits`

## 模块概述

价格提醒模块允许用户为股票设置条件触发规则，当实时行情满足条件时自动推送通知。支持多条件组合 (AND/OR)、冷却时间、每日触发上限等控制。

## 数据模型

### PriceAlertRule 表 (price_alert_rules)
| 字段 | 类型 | 说明 |
|------|------|------|
| stock_id | FK(stocks) | 关联股票 |
| name | VARCHAR | 规则名称 |
| enabled | BOOLEAN | 是否启用 |
| condition_group | JSON | 条件组 |
| market_hours_mode | VARCHAR | always / trading_only |
| cooldown_minutes | INTEGER | 冷却时间（分钟） |
| max_triggers_per_day | INTEGER | 每日最大触发次数 |
| repeat_mode | VARCHAR | once / repeat |
| expire_at | DATETIME | 过期时间 |
| notify_channel_ids | JSON | 通知渠道 |
| last_trigger_at | DATETIME | 上次触发时间 |
| trigger_count_today | INTEGER | 当日触发次数 |

### PriceAlertHit 表 (price_alert_hits)
| 字段 | 说明 |
|------|------|
| rule_id | 规则 ID |
| stock_id | 股票 ID |
| trigger_time | 触发时间 |
| trigger_snapshot | 触发时行情快照 |
| trigger_bucket | 幂等桶 (YYYYMMDDHHMM) |
| notify_success | 通知是否成功 |

## 条件类型

| 类型 | 说明 | 运算符 |
|------|------|--------|
| `price` | 当前价格 | >=, <=, >, <, ==, between |
| `change_pct` | 涨跌幅 % | >=, <=, >, <, between |
| `turnover` | 成交额 | >=, <=, >, <, between |
| `volume` | 成交量 | >=, <=, >, <, between |
| `volume_ratio` | 量比 | >=, <=, >, <, between |

## 条件组

```json
{
  "op": "and",
  "items": [
    {"type": "change_pct", "op": ">=", "value": 5},
    {"type": "volume_ratio", "op": ">=", "value": 2}
  ]
}
```
支持 `and` / `or` 组合，运算符支持单值和区间 `between`。

## API 端点

### GET /api/price-alerts

获取所有提醒规则。

### POST /api/price-alerts

创建提醒规则。

**请求体**:
```json
{
  "stock_id": 1,
  "name": "茅台大涨提醒",
  "enabled": true,
  "condition_group": {
    "op": "and",
    "items": [
      {"type": "change_pct", "op": ">=", "value": 5}
    ]
  },
  "market_hours_mode": "trading_only",
  "cooldown_minutes": 30,
  "max_triggers_per_day": 3,
  "repeat_mode": "repeat",
  "notify_channel_ids": [1]
}
```

### PUT /api/price-alerts/{rule_id}

更新规则。修改规则后自动重置当日触发计数。

### POST /api/price-alerts/{rule_id}/toggle

启用/禁用规则。

### DELETE /api/price-alerts/{rule_id}

删除规则。

### GET /api/price-alerts/{rule_id}/hits

查看规则的历史触发记录。

### POST /api/price-alerts/{rule_id}/test

测试规则（dry run，不发送通知）。

### POST /api/price-alerts/scan

手动触发一次全局提醒扫描。

## 调度扫描

价格提醒通过 `PriceAlertScheduler` 每 60 秒扫描一次：

```
PriceAlertScheduler (60s interval)
  → 查询所有 enabled 规则
  → 获取关联股票实时行情
  → 逐条评估 condition_group
  → 命中 → 冷却检查 → 通知 → 记录 hit
  → 未命中 → 跳过
```

## 幂等机制

通过 `trigger_bucket` (精确到分钟) 和唯一约束防止同一分钟内重复触发同一规则。
