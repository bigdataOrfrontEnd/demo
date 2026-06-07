# 模块 21: 首页仪表盘 (Dashboard)

> **API 前缀**: `/api/dashboard`  
> **源码**: `src/web/api/dashboard.py`  
> **认证要求**: 是

## 模块概述

Dashboard 模块是前端首页的聚合数据接口，将 KPI 指标、策略信号、市场热度、主题标签、最新洞察等打包在一次请求中返回。

## 数据来源

Dashboard 聚合了多张表的数据（轻量版，不含实时行情请求）：

| 数据 | 来源 |
|------|------|
| KPI 指标 | stocks / positions / accounts |
| 入场机会 | strategy_signal_runs (status=active, holding=unheld) |
| 风险持仓 | strategy_signal_runs (holding=held, 带风险标记) |
| 市场热度 | market_scan_snapshots (最近快照) |
| 热门主题 | news_topic_snapshots (最近快照) |
| 策略绩效 | strategy_outcomes (命中率/收益率) |
| 最新洞察 | analysis_history (盘前/盘后/新闻) |
| 数据新鲜度 | 各表最新 snapshot_date |

## API 端点

### GET /api/dashboard/overview

获取首页完整数据。

**参数**:
- `market` (query, default "ALL") — 市场过滤：ALL/CN/HK/US
- `action_limit` (query, default 6) — 入场机会数量
- `risk_limit` (query, default 6) — 风险持仓数量
- `days` (query, default 45) — 策略统计回溯天数

**响应结构**:
```json
{
  "generated_at": "2026-05-21T09:00:00+08:00",
  "market": "ALL",
  "snapshot_date": "2026-05-20",
  
  "data_freshness": {
    "strategy_snapshot_date": "2026-05-21",
    "entry_snapshot_date": "2026-05-21",
    "market_scan_snapshot_date": "2026-05-21",
    "latest_history_updated_at": "2026-05-20T15:31:00+08:00"
  },
  
  "kpis": {
    "watchlist_count": 25,
    "positions_count": 8,
    "available_funds": 500000.00,
    "invested_cost": 800000.00,
    "total_assets_estimate": 1300000.00,
    "executable_opportunities": 3,
    "risk_positions": 2,
    "win_rate_3d": 68.5,
    "win_sample_3d": 45,
    "errors_24h": 0
  },
  
  "portfolio": {
    "positions_count": 8,
    "watchlist_count": 25,
    "available_funds": 500000.00,
    "invested_cost": 800000.00,
    "by_market": [
      {"market": "CN", "positions": 6, "invested_cost": 650000.00},
      {"market": "HK", "positions": 2, "invested_cost": 150000.00}
    ]
  },
  
  "action_center": {
    "opportunities": [
      {
        "stock_symbol": "300418",
        "stock_name": "昆仑万维",
        "action": "buy",
        "action_label": "建仓",
        "rank_score": 85.5,
        "entry_low": 45.0,
        "entry_high": 48.0,
        "strategy_count": 3
      }
    ],
    "risk_items": [
      {
        "stock_symbol": "600519",
        "stock_name": "贵州茅台",
        "risk_flags": ["信号转弱", "高风险"]
      }
    ]
  },
  
  "market_pulse": {
    "hot_stocks": [
      {"symbol": "300750", "market": "CN", "name": "宁德时代",
       "score_seed": 92.5, "change_pct": 5.2}
    ],
    "hot_topics": [
      {"name": "AI算力", "score": 95.0, "sentiment": "bullish"}
    ]
  },
  
  "strategy": {
    "coverage": {"snapshot_date": "2026-05-21", "total_signals": 120},
    "top_by_strategy": [
      {"strategy_code": "trend_following", "sample_size": 45, "win_rate": 73.3}
    ]
  },
  
  "insights": [
    {"agent_name": "premarket_outlook", "agent_label": "盘前分析",
     "analysis_date": "2026-05-21", "title": "盘前市场展望"}
  ]
}
```

## 入场机会排名逻辑（代码级）

```python
def _group_signals(items):
    """多条策略信号按股票聚合，选最优的一条为代表"""
    grouped: dict[str, dict] = {}
    for row in items:
        key = f"{row['stock_market']}:{row['stock_symbol']}"
        prev = grouped.get(key)
        if not prev:
            row["strategy_count"] = 1
            grouped[key] = row
            continue
        prev["strategy_count"] += 1
        
        # 选择逻辑：active 优先 → action 优先(buy>add>watch) → rank_score 高优先
        if row["status"] == "active" and prev["status"] != "active":
            grouped[key] = row
        elif action_priority(row) > action_priority(prev):
            grouped[key] = row
        elif row["rank_score"] > prev["rank_score"]:
            grouped[key] = row
    
    return list(grouped.values())
```

## 风险标记规则

持仓股票出现以下情况之一即标记为风险：

| 标记 | 条件 |
|------|------|
| 组合约束 | `constrained == true` |
| 高风险 | `risk_level == "high"` |
| 非活跃状态 | `status != "active"` |
| 信号转弱 | `rank_score < 68` |

## KPI 计算

```python
# 持仓成本（带汇率换算）
invested_cost = sum(pos.cost_price * pos.quantity * fx_rate for pos, stock in positions)

# 总资产估算 = 可用资金 + 持仓成本（不含浮动盈亏的快照）
total_assets_estimate = total_available_funds + invested_cost

# 3日策略胜率
win_rate_3d = wins_3d / sample_3d * 100  # 仅在 sample_3d > 0 时计算
```

## 使用场景

- 前端首页 Dashboard 面板
- 快速了解组合健康度、入场机会、风险提醒
- 市场热度和策略绩效一目了然
