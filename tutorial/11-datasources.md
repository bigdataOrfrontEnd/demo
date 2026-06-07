# 模块 11: 数据源管理 (Datasources)

> **API 前缀**: `/api/datasources`  
> **源码**: `src/web/api/datasources.py`  
> **认证要求**: 是  
> **数据库表**: `data_sources`

## 模块概述

数据源管理模块控制系统使用的数据来源。支持 6 类数据源，每类可配置多个来源（按优先级选择）。

## 数据源类型

| 类型 | 标签 | 用途 |
|------|------|------|
| `news` | 新闻资讯 | 股票相关新闻和公告 |
| `kline` | K线数据 | 历史日线/周线/月线 |
| `quote` | 实时行情 | 盘中最新的价量数据 |
| `capital_flow` | 资金流向 | 主力/散户资金流入流出 |
| `events` | 事件日历 | 财报、分红等事件 |
| `chart` | K线截图 | Playwright 截取的 K线图 |

## 预置数据源

系统启动时通过 `seed_data_sources()` 预置以下数据源：

| 名称 | 类型 | 提供商 | 默认启用 |
|------|------|--------|----------|
| 雪球资讯 | news | xueqiu | 否 (需 cookie) |
| 东方财富资讯 | news | eastmoney_news | 是 |
| 东方财富公告 | news | eastmoney | 是 |
| 腾讯K线 | kline | tencent | 是 |
| Tushare K线 | kline | tushare | 否 (需 token) |
| YFinance K线 | kline | yfinance | 否 |
| 东方财富资金流 | capital_flow | eastmoney | 是 |
| 腾讯行情 | quote | tencent | 是 |
| YFinance 行情 | quote | yfinance | 否 |
| 东方财富事件日历 | events | eastmoney | 是 |
| 雪球K线截图 | chart | xueqiu | 是 |
| 东方财富K线截图 | chart | eastmoney | 否 |

## 数据模型

### DataSource 表 (data_sources)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 显示名称 |
| type | VARCHAR | 类型 |
| provider | VARCHAR | 提供商标识 |
| config | JSON | 配置参数 |
| enabled | BOOLEAN | 是否启用 |
| priority | INTEGER | 优先级 (越小越高) |
| supports_batch | BOOLEAN | 是否支持批量查询 |
| test_symbols | JSON | 测试用股票列表 |

## API 端点

### GET /api/datasources

获取所有数据源，可按类型筛选。

**参数**: `type` (query, optional) — 如 `news` / `kline` / `quote`

### GET /api/datasources/types

获取数据源类型列表。

### GET /api/datasources/{source_id}

获取单个数据源详情。

### POST /api/datasources

创建自定义数据源。

### PUT /api/datasources/{source_id}

更新数据源配置。

### DELETE /api/datasources/{source_id}

删除数据源。

### POST /api/datasources/{source_id}/test

测试数据源连接和数据获取。

**响应示例**:
```json
{
  "test_passed": true,
  "source_name": "东方财富资讯",
  "source_type": "news",
  "count": 15,
  "duration_ms": 1200,
  "error": null,
  "items": [
    {"title": "...", "publish_time": "..."},
    ...
  ],
  "logs": [
    "[15:30:01] 开始测试数据源: 东方财富资讯",
    "[15:30:02] 获取成功: 15 条"
  ]
}
```

## 数据采集机制

数据采集通过 `DataCollector / CollectorManager` 统一管理：

```
collector_manager.test_source(source)
  → 根据 source.type 选择对应的 Collector
  → 调用 collector.fetch() 带测试股票
  → 返回 test 结果（数据条数 + 耗时 + 错误）
```
