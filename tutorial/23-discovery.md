# 模块 23: 市场发现 (Discovery)

> **API 前缀**: `/api/discovery`  
> **源码**: `src/web/api/discovery.py` + `src/collectors/discovery_collector.py`  
> **认证要求**: 是

## 模块概述

市场发现模块提供热门股票和板块的发现功能，帮助用户发掘市场机会。支持 A 股真实行业板块数据，对港股/美股使用个股热度数据合成主题看板。

## API 端点

### GET /api/discovery/stocks

获取热门股票（按成交额或涨幅排名）。

**参数**:
- `market` (query, default "CN") — 市场
- `mode` (query, default "turnover") — `turnover` / `gainers`
- `limit` (query, default 20)

**响应**:
```json
[
  {
    "symbol": "300750",
    "market": "CN",
    "name": "宁德时代",
    "price": 210.50,
    "change_pct": 5.23,
    "turnover": 8560000000.00,
    "volume": 42000000
  }
]
```

### GET /api/discovery/boards

获取热门板块/主题。

**参数**:
- `market` (query, default "CN")
- `mode` (query, default "gainers") — `gainers` / `turnover` / `hot`
- `limit` (query, default 12)

**A 股**：返回真实的东方财富行业板块数据

**响应**:
```json
[
  {
    "code": "BK0001",
    "name": "人工智能",
    "change_pct": 3.5,
    "change_amount": null,
    "turnover": 12500000000.00
  }
]
```

**港股/美股**：合成主题看板（无真实行业板块数据时回退）

### GET /api/discovery/boards/{board_code}/stocks

获取板块下的成分股。

**参数**: `board_code` (path), `mode`, `limit`, `market`

## 数据采集流程（代码级）

```python
async def _hot_stocks_live_or_snapshot(collector, db, market, mode, limit):
    """获取热门股票：优先实时源，失败回退到数据库快照"""
    try:
        # Step 1: 尝试实时获取
        items = await collector.fetch_hot_stocks(market=market, mode=mode, limit=limit)
        if items:
            return [format_item(it) for it in items]
    except Exception as e:
        logger.warning(f"discovery stocks live failed: {e}")
    
    # Step 2: 回退到数据库快照（market_scan_snapshots 表）
    return _latest_snapshot_stocks(db, market, limit)

def _latest_snapshot_stocks(db, market, limit):
    """从最新 market_scan_snapshot 中获取数据"""
    # 查询最新快照日期
    latest_date = db.query(MarketScanSnapshot.snapshot_date).filter(
        MarketScanSnapshot.stock_market == market
    ).order_by(MarketScanSnapshot.snapshot_date.desc()).first()
    
    if not latest_date:
        return []
    
    # 按 score_seed 降序取 top N
    rows = db.query(MarketScanSnapshot).filter(
        MarketScanSnapshot.stock_market == market,
        MarketScanSnapshot.snapshot_date == latest_date[0]
    ).order_by(MarketScanSnapshot.score_seed.desc()).limit(limit).all()
    
    return [format_snapshot_row(row) for row in rows]
```

## 合成主题看板逻辑（港股/美股回退方案）

当港股/美股无真实板块数据时，从个股热度中构建主题看板：

```python
def _build_synthetic_boards(market, stocks, watchlist, limit):
    """从热门股票中构建四个合成看板"""
    universe = stocks[:120]  # 取 top 120 保持质量
    
    # 涨幅领先
    gainers = sorted(universe, key=lambda x: x.get("change_pct", -999), reverse=True)
    # 成交额领先
    turnover = sorted(universe, key=lambda x: x.get("turnover", 0), reverse=True)
    # 波动活跃
    volatility = sorted(universe, key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    # 自选关联
    watch_related = [x for x in universe if x["symbol"] in watchlist]
    
    return [
        {"code": "HK_GAINERS", "name": "港股涨幅领先", "change_pct": avg(gainers[:12]), ...},
        {"code": "HK_TURNOVER", "name": "港股成交额领先", ...},
        {"code": "HK_VOLATILITY", "name": "港股波动活跃", ...},
        {"code": "HK_WATCHLIST", "name": "港股自选关联", ...},
    ]
```

## 缓存策略

所有 discovery 接口使用内存缓存：

| 接口 | 缓存 TTL |
|------|----------|
| `/discovery/stocks` | 45 秒 |
| `/discovery/boards` | 60 秒 |
| `/discovery/boards/{code}/stocks` | 60 秒 |

## 数据源

A 股热门股票和板块数据来自东方财富行情中心（通过 `EastMoneyDiscoveryCollector`）。

## 使用场景

- 前端"发现"页面展示热门股票和板块
- 浏览市场热点，发掘潜在交易机会
- 板块轮动分析
