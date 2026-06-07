# 模块 07: 账户与持仓管理 (Accounts)

> **API 前缀**: `/api` (无统一前缀)  
> **源码**: `src/web/api/accounts.py`  
> **认证要求**: 是  
> **数据库表**: `accounts`, `positions`

## 模块概述

账户与持仓管理模块支持多账户、多股票持仓。每个账户可以有独立的可用资金，每只股票可以在不同账户中持有，每笔持仓可设交易风格（短线/波段/长线）。

## 数据模型

### Account 表 (accounts)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 账户名称 |
| available_funds | FLOAT | 可用资金 |
| enabled | BOOLEAN | 是否启用 |

### Position 表 (positions)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| account_id | FK(accounts) | 所属账户 |
| stock_id | FK(stocks) | 持仓股票 |
| cost_price | FLOAT | 成本价 |
| quantity | INTEGER | 持仓数量 |
| invested_amount | FLOAT | 投入资金 |
| trading_style | VARCHAR | short/swing/long |
| sort_order | INTEGER | 排序 |

唯一约束：同一账户下同一股票只能有一条持仓。

## API 端点

### 账户管理

#### GET /api/accounts

获取所有账户列表。

#### GET /api/accounts/{account_id}

获取单个账户详情。

#### POST /api/accounts

创建账户。

**请求体**:
```json
{
  "name": "华泰证券",
  "available_funds": 100000
}
```

#### PUT /api/accounts/{account_id}

更新账户信息（名称/资金/启用状态）。

#### DELETE /api/accounts/{account_id}

删除账户（级联删除所有持仓）。

### 持仓管理

#### GET /api/positions

获取持仓列表，可按账户或股票筛选。

**参数**:
- `account_id` (query, optional)
- `stock_id` (query, optional)

#### POST /api/positions

创建持仓。

**请求体**:
```json
{
  "account_id": 1,
  "stock_id": 5,
  "cost_price": 1600.00,
  "quantity": 100,
  "invested_amount": 160000,
  "trading_style": "swing"
}
```

#### PUT /api/positions/{position_id}

更新持仓（成本价/数量/投入资金/交易风格）。

#### DELETE /api/positions/{position_id}

删除持仓。

#### PUT /api/positions/reorder/batch

批量调整持仓排序。

### 持仓汇总

#### GET /api/portfolio/summary

获取持仓汇总，包含实时市值、浮动盈亏等。

**参数**:
- `account_id` (query, optional) — 可按账户筛选
- `include_quotes` (query, default true) — 是否包含实时行情

**响应**:
```json
{
  "accounts": [
    {
      "id": 1,
      "name": "华泰证券",
      "available_funds": 100000,
      "total_market_value": 168050,
      "total_cost": 160000,
      "total_pnl": 8050,
      "total_pnl_pct": 5.03,
      "total_daily_pnl": 2050,
      "total_assets": 268050,
      "positions": [
        {
          "id": 1,
          "symbol": "600519",
          "name": "贵州茅台",
          "market": "CN",
          "cost_price": 1600.00,
          "quantity": 100,
          "current_price": 1680.50,
          "market_value": 168050,
          "pnl": 8050,
          "pnl_pct": 5.03,
          "daily_pnl": 2050,
          "trading_style": "swing"
        }
      ]
    }
  ],
  "total": {
    "total_market_value": 168050,
    "total_cost": 160000,
    "total_pnl": 8050,
    "total_pnl_pct": 5.03,
    "total_daily_pnl": 2050,
    "available_funds": 100000,
    "total_assets": 268050
  },
  "exchange_rates": {
    "HKD_CNY": 0.92,
    "USD_CNY": 7.25
  }
}
```

## 汇率处理

港股和美股持仓自动换算为人民币展示：

- **港币汇率**: 从新浪财经 `fx_shkdcny` 获取，1小时缓存，默认 0.92
- **美元汇率**: 从新浪财经 `fx_susdcny` 获取，1小时缓存，默认 7.25

## 使用场景

- 持仓页面展示多账户资产配置
- 实盘和模拟盘的统一持仓视图
- Agent 执行时提供持仓上下文给 AI 分析
- 配合行情实时计算浮盈浮亏
