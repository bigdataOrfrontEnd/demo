# 模块 02: 市场指数 (Market)

> **API 前缀**: `/api/market`  
> **源码**: `src/web/api/market.py`  
> **认证要求**: 否（公共数据）

## 模块概述

市场指数模块提供全球主要市场指数的实时行情，无需认证即可访问。数据通过腾讯行情 API 获取。

## 支持的市场指数

| 代码 | 名称 | 市场 | 腾讯代码 |
|------|------|------|----------|
| 000001 | 上证指数 | CN | sh000001 |
| 399001 | 深证成指 | CN | sz399001 |
| 399006 | 创业板指 | CN | sz399006 |
| HSI | 恒生指数 | HK | hkHSI |
| IXIC | 纳斯达克 | US | usIXIC |
| DJI | 道琼斯 | US | usDJI |

## API 端点

### GET /api/market/indices

获取所有市场指数的最新行情。

**无参数**

**响应示例**：
```json
[
  {
    "symbol": "000001",
    "name": "上证指数",
    "market": "CN",
    "current_price": 3350.67,
    "change_pct": 0.35,
    "change_amount": 11.73,
    "prev_close": 3338.94
  },
  {
    "symbol": "HSI",
    "name": "恒生指数",
    "market": "HK",
    "current_price": null,
    "change_pct": null,
    "change_amount": null,
    "prev_close": null
  }
]
```

**说明**：
- 指数列表是硬编码的，不支持动态添加
- 非交易时段返回 `null` 值
- 单个指数获取失败不影响其他指数
- 数据来源：`_fetch_tencent_quotes()` 函数

## 市场定义

市场基本属性定义在 `src/models/market.py`，包含：

```python
class MarketCode(Enum):
    CN = "CN"    # A股
    HK = "HK"    # 港股
    US = "US"    # 美股

class MarketDef:
    name: str              # 市场名称
    timezone: str          # 时区
    sessions: list[Session] # 交易时段列表
    is_trading_time()      # 是否在交易时间
    get_tz()               # 获取时区对象
```

## 数据流

```
GET /api/market/indices
  → 遍历 MARKET_INDICES 配置列表
  → 拼接腾讯行情 symbol (如 sh000001)
  → 调用 _fetch_tencent_quotes() 批量拉取
  → 解析 JSON 行情数据
  → 按 response_symbol 匹配结果
  → 返回统一格式
```

## 使用场景

- 前端首页顶部展示全球指数行情
- Dashboard 仪表盘的市场概览
- 用于判断当前市场状态（辅助盘中监测）
