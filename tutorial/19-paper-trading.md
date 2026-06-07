# 模块 19: 模拟交易 (Paper Trading)

> **API 前缀**: `/api/paper-trading`  
> **源码**: `src/web/api/paper_trading.py` + `src/core/paper_trading_engine.py`  
> **认证要求**: 是  
> **数据库表**: `paper_trading_account`, `paper_trading_positions`, `paper_trading_trades`

## 模块概述

模拟交易（纸交易）模块实现了一个完整的虚拟交易系统，可基于策略信号自动建仓和平仓，追踪模拟盘绩效。

## 数据模型

### PaperTradingAccount (paper_trading_account)
| 字段 | 说明 |
|------|------|
| initial_capital | 初始资金（默认 100 万） |
| current_capital | 当前现金 |
| total_pnl | 总盈亏 |
| total_trades | 总交易次数 |
| winning_trades | 盈利交易次数 |
| max_drawdown_pct | 最大回撤 |
| peak_capital | 峰值资金 |
| enabled | 是否启用 |
| excluded_markets | 排除的市场 |

### PaperTradingPosition (paper_trading_positions) - 持仓中
| 字段 | 说明 |
|------|------|
| stock_symbol / stock_market | 股票标识 |
| quantity / entry_price | 数量和入场价 |
| stop_loss / target_price | 止损/目标价 |
| current_price / unrealized_pnl | 当前价/浮动盈亏 |
| status | open / closed |
| signal_run_id | 触发建仓的策略信号 |
| strategy_code | 策略代码 |

### PaperTradingTrade (paper_trading_trades) - 已平仓
| 字段 | 说明 |
|------|------|
| entry_price / exit_price | 入场/出场价 |
| pnl / pnl_pct | 盈亏 |
| exit_reason | stop_loss / target_price / signal_reversal / manual |
| holding_days | 持仓天数 |

## API 端点

### 账户管理

#### GET /api/paper-trading/account

获取模拟盘账户信息（含未平仓持仓）。

#### POST /api/paper-trading/account/toggle

启用/禁用模拟盘。

#### POST /api/paper-trading/account/reset

重置模拟盘（清空所有持仓和交易记录）。

#### POST /api/paper-trading/account/settings

更新模拟盘设置（如排除市场）。

### 持仓与交易

#### GET /api/paper-trading/positions

获取持仓列表。`status=open` / `closed` / `all`

#### GET /api/paper-trading/trades

获取已平仓交易记录（分页）。

#### POST /api/paper-trading/positions/{position_id}/close

手动平仓。

### 绩效分析

#### GET /api/paper-trading/metrics

获取完整绩效指标。

**响应**:
```json
{
  "account": {
    "total_equity": 1050000.00,
    "total_pnl": 50000.00,
    "win_rate": 65.0,
    "max_drawdown_pct": 8.5
  },
  "equity_curve": [
    {"date": "2026-05-01", "equity": 1000000},
    {"date": "2026-05-10", "equity": 1030000}
  ],
  "open_positions": 2,
  "strategy_performance": [
    {
      "strategy_code": "trend_following",
      "total_trades": 15,
      "win_rate": 73.3,
      "total_pnl": 32000,
      "avg_pnl_pct": 2.5,
      "avg_holding_days": 5.2
    }
  ]
}
```

### 自动化

#### POST /api/paper-trading/scan

手动触发一次建仓+平仓扫描。

### 通知设置

#### GET /api/paper-trading/notify-settings

获取跟单通知设置。

#### POST /api/paper-trading/notify-settings

更新通知设置。

#### POST /api/paper-trading/notify-test

发送测试通知。

#### POST /api/paper-trading/premarket-plan

手动推送盘前计划。

#### POST /api/paper-trading/daily-summary

手动推送日终摘要。

## 自动扫描流程

```
PaperTradingScheduler (60s interval)
  → 检查模拟盘是否启用
  → 获取最新策略信号 (strategy_signal_runs)
  → 筛选 active + 未持仓的 buy/add 信号
  → 检查可用资金 → 建仓
  → 遍历 open 持仓:
      → 检查止损/目标价是否触发
      → 检查对应信号是否转为不活跃
      → 满足条件 → 平仓
  → 更新账户权益和绩效
```

## 使用场景

- 验证策略信号的实际交易效果
- 无风险测试交易策略
- 追踪模拟盘收益曲线
