# 模块 22: 上下文管理 (Context)

> **API 前缀**: `/api/context`  
> **源码**: `src/web/api/context.py` + `src/core/context_store.py` + `src/core/prediction_outcome.py`  
> **认证要求**: 是  
> **数据库表**: `stock_context_snapshots`, `news_topic_snapshots`, `agent_context_runs`, `agent_prediction_outcomes`

## 模块概述

上下文管理模块提供跨天记忆机制的数据查询与维护功能。包括：
- **股票上下文快照**：每只股票每天的结构化数据存档
- **新闻主题快照**：按窗口聚合的市场主题
- **上下文运行记录**：每次 Agent 执行时使用的上下文
- **预测后验评估**：Agent 建议的实际结果追踪

## 数据模型

### StockContextSnapshot (stock_context_snapshots)
| 字段 | 说明 |
|------|------|
| symbol / market | 股票标识 |
| snapshot_date | 快照日期 (YYYY-MM-DD) |
| context_type | 类型：premarket_outlook / daily_report / ... |
| payload | 结构化上下文数据 (JSON) |
| quality | 数据质量评分 (JSON) |

唯一约束：`(symbol, market, snapshot_date, context_type)`

### NewsTopicSnapshot (news_topic_snapshots)
| 字段 | 说明 |
|------|------|
| snapshot_date | 快照日期 |
| window_days | 聚合窗口（天数） |
| symbols | 关联股票列表 |
| summary | 摘要文本 |
| topics | 主题列表 `[{"topic":"AI算力", "score":95.0, "sentiment":"bullish"}]` |
| sentiment | 整体情绪 |

### AgentPredictionOutcome (agent_prediction_outcomes)
| 字段 | 说明 |
|------|------|
| agent_name | Agent 名称 |
| stock_symbol / stock_market | 股票标识 |
| prediction_date | 预测日期 |
| horizon_days | 预测周期 (1/5/10/20) |
| action / action_label | 建议操作 |
| trigger_price | 预测时价格 |
| outcome_price | 实际价格 |
| outcome_return_pct | 实际收益率 |
| outcome_status | pending / hit / miss / partial |

## API 端点

### GET /api/context/snapshots/{symbol}

获取某只股票的历史上下文快照。

**参数**:
- `market` (query, default "CN")
- `context_type` (query, optional) — 如 `daily_report`
- `days` (query, default 30)
- `limit` (query, default 30)

### GET /api/context/topics/latest

获取最新的新闻主题快照。

**参数**: `window_days` (query, default 7)

### GET /api/context/runs

获取 Agent 执行时的上下文运行记录。

**参数**: `agent_name` (required), `stock_symbol` (optional), `days`, `limit`

### 预测后验

#### GET /api/context/predictions

获取历史预测的后验评估结果。

**参数**:
- `agent_name` (optional)
- `stock_symbol` (optional)
- `status` (optional) — pending / hit / miss
- `days` (query, default 90)
- `limit` (query, default 200)

#### POST /api/context/predictions/evaluate

手动触发评估 pending 状态的预测结果。

**参数**: `max_horizon_days` (default 10), `limit` (default 300)

**评估流程（代码级）**：
```python
def evaluate_pending_prediction_outcomes(max_horizon_days, limit):
    # Step 1: 查询所有 pending 状态的预测
    predictions = db.query(AgentPredictionOutcome).filter(
        AgentPredictionOutcome.outcome_status == "pending"
    ).limit(limit).all()
    
    for pred in predictions:
        # Step 2: 根据 horizon_days 查询对应日期的实际 K线收盘价
        target_date = pred.prediction_date + timedelta(days=pred.horizon_days)
        close_price = get_close_price(pred.stock_symbol, pred.stock_market, target_date)
        
        if close_price is None:
            continue  # 数据还不可用，保持 pending
        
        # Step 3: 计算实际收益
        pred.outcome_price = close_price
        pred.outcome_return_pct = (close_price - pred.trigger_price) / pred.trigger_price * 100
        
        # Step 4: 判断命中状态
        if pred.action in ("buy", "add") and pred.outcome_return_pct > 0:
            pred.outcome_status = "hit"
        elif pred.action in ("sell", "reduce") and pred.outcome_return_pct < 0:
            pred.outcome_status = "hit"
        else:
            pred.outcome_status = "miss"
        
        pred.evaluated_at = datetime.now(timezone.utc)
    
    db.commit()
    return {"evaluated": len(predictions)}
```

### POST /api/context/cleanup

清理过期的上下文数据。

**参数**:
- `snapshot_days` (default 180) — 上下文快照保留天数
- `topic_days` (default 180) — 新闻主题保留天数
- `context_run_days` (default 180) — 运行记录保留天数
- `outcome_days` (default 365) — 后验结果保留天数

## 数据写入时机

上下文数据由 `ContextMaintenanceScheduler` 定期维护：

```
ContextMaintenanceScheduler (每 6 小时)
  → 检查快照是否需要更新
  → 评估 pending 的预测后验
  → 清理过期数据
```

## 使用场景

- 上下文快照：Agent 分析时注入历史上下文，实现跨天记忆
- 预测后验：追踪 Agent 建议的准确率
- 数据清理：防止数据库无限膨胀
