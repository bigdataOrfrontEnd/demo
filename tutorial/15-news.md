# 模块 15: 新闻分析 (News)

> **API 前缀**: `/api/news`  
> **源码**: `src/web/api/news.py`  
> **核心类**: `src/collectors/news_collector.py` → `NewsCollector`  
> **认证要求**: 是

## 模块概述

新闻模块聚合多个数据源的股票新闻和公告，支持按股票代码、名称、时间范围和来源筛选，自动去重并标记相关性。

## 新闻来源

| 来源 ID | 显示名 | 类型 |
|---------|--------|------|
| `xueqiu` | 雪球 | 资讯（需 cookie） |
| `eastmoney_news` | 东财资讯 | 新闻 |
| `eastmoney` | 东财公告 | 公告 |

## API 端点

### GET /api/news

获取新闻列表。

**参数**:
- `symbols` (query, default "") — 股票代码，逗号分隔
- `names` (query, default "") — 股票名称，逗号分隔（优先使用）
- `hours` (query, default 168) — 时间范围（小时，默认 7 天）
- `limit` (query, default 50, max 200)
- `filter_related` (query, default true) — 仅显示与自选股相关
- `source` (query, default "") — 来源过滤，逗号分隔

**响应**:
```json
[
  {
    "source": "eastmoney_news",
    "source_label": "东财资讯",
    "external_id": "...",
    "title": "茅台发布2025年报，净利润增长15%",
    "content": "详细内容...",
    "publish_time": "2026-05-21 14:30",
    "symbols": ["600519"],
    "importance": 2,
    "url": "https://..."
  }
]
```

### GET /api/news/sources

获取已配置的新闻数据源列表。

## 新闻相关性判定

```python
def is_related(item):
    # 1. 公告类天然相关
    if item.source == "eastmoney": return True
    # 2. 已标记相关股票代码
    if item.symbols & target_symbols: return True
    # 3. 标题或正文包含股票代码或名称
    if keyword in title + content: return True
    return False
```

## 新闻缓存

通过 `news_cache` 表缓存已抓取的新闻，按 `(source, external_id)` 去重，避免重复拉取同一新闻。

## 使用场景

- 前端新闻面板，按股票筛选查看
- Agent 分析时获取近期新闻上下文
- 新闻速递 (news_digest) Agent 的分析数据源
