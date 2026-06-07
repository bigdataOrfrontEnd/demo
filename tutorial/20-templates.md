# 模块 20: 配置导入导出 (Templates)

> **API 前缀**: `/api/templates`  
> **源码**: `src/web/api/templates.py`  
> **认证要求**: 是

## 模块概述

模板模块提供系统配置的导入导出功能，可将自选股、Agent 绑定、调度设置等打包为 JSON，方便迁移或备份。

## 导出结构 (TemplatePayload v1)

```json
{
  "version": 1,
  "exported_at": "2026-05-21T10:00:00+00:00",
  "settings": {
    "http_proxy": "http://127.0.0.1:7890",
    "notify_quiet_hours": "23:00-07:00"
  },
  "agents": [
    {
      "name": "daily_report",
      "kind": "workflow",
      "enabled": true,
      "schedule": "30 15 * * 1-5",
      "execution_mode": "batch",
      "ai_model_id": 1,
      "notify_channel_ids": [1],
      "config": {"max_stocks": 10}
    }
  ],
  "stocks": [
    {
      "symbol": "600519",
      "name": "贵州茅台",
      "market": "CN",
      "agents": [
        {
          "agent_name": "daily_report",
          "schedule": "",
          "ai_model_id": null,
          "notify_channel_ids": []
        }
      ]
    }
  ]
}
```

## API 端点

### GET /api/templates/export

导出当前系统配置。

**参数**: `include_internal` (query, default true) — 是否包含内部 Agent

### POST /api/templates/import

导入配置包。

**参数**:
- `mode` (query, default "merge") — `merge`（合并更新）或 `replace`（替换载荷涵盖的数据）

## 导入流程（代码级）

```python
def import_template(payload: TemplatePayload, mode: str, db: Session):
    # Step 1: 导入系统设置
    for key, value in payload.settings.items():
        if key not in _SETTINGS_KEYS:
            continue  # 跳过不识别的 key
        row = db.query(AppSettings).filter(AppSettings.key == key).first()
        if row:
            row.value = str(value or "")  # 更新已有设置
        else:
            db.add(AppSettings(key=key, value=str(value or "")))  # 新增设置

    # Step 2: 导入 Agent 配置
    for agent_data in payload.agents:
        row = db.query(AgentConfig).filter(AgentConfig.name == agent_data.name).first()
        if not row:
            row = AgentConfig(name=agent_data.name, display_name=agent_data.name)
            db.add(row)  # 创建新 Agent
        
        # 同步字段
        row.kind = agent_data.kind
        row.enabled = bool(agent_data.enabled)
        row.schedule = agent_data.schedule
        row.execution_mode = agent_data.execution_mode or "batch"
        row.ai_model_id = agent_data.ai_model_id
        row.notify_channel_ids = agent_data.notify_channel_ids
        
        # config 合并 vs 替换
        if mode == "replace":
            row.config = agent_data.config
        else:  # merge
            cfg = row.config or {}
            cfg.update(agent_data.config)
            row.config = cfg

    # Step 3: 导入股票和 Agent 绑定
    for stock_data in payload.stocks:
        stock = db.query(Stock).filter(
            Stock.symbol == stock_data.symbol,
            Stock.market == stock_data.market
        ).first()
        
        if not stock:
            stock = Stock(symbol=stock_data.symbol, name=stock_data.name, market=stock_data.market)
            db.add(stock)
            db.flush()  # 获取 stock.id
        
        if mode == "replace":
            # 删除 payload 中没有的 stock_agent 绑定
            for existing_sa in db.query(StockAgent).filter(StockAgent.stock_id == stock.id).all():
                if existing_sa.agent_name not in desired_names:
                    db.delete(existing_sa)
        
        for sa_data in stock_data.agents:
            sa = db.query(StockAgent).filter(
                StockAgent.stock_id == stock.id,
                StockAgent.agent_name == sa_data.agent_name
            ).first()
            if not sa:
                sa = StockAgent(stock_id=stock.id, agent_name=sa_data.agent_name)
                db.add(sa)
            sa.schedule = sa_data.schedule
            sa.ai_model_id = sa_data.ai_model_id
            sa.notify_channel_ids = sa_data.notify_channel_ids

    db.commit()

    # Step 4: 重载调度器使 schedule 变更立即生效
    reload_scheduler()
```

## 导出流程（代码级）

```python
def export_template(include_internal: bool, db: Session):
    # Step 1: 读取系统设置
    settings = {}
    for row in db.query(AppSettings).filter(AppSettings.key.in_(_SETTINGS_KEYS)).all():
        settings[row.key] = row.value or ""

    # Step 2: 读取 Agent 配置
    agents = []
    for agent in db.query(AgentConfig).all():
        agents.append({
            "name": agent.name,
            "kind": agent.kind,
            "enabled": agent.enabled,
            "schedule": agent.schedule,
            "execution_mode": agent.execution_mode,
            "ai_model_id": agent.ai_model_id,
            "notify_channel_ids": agent.notify_channel_ids,
            "config": agent.config or {},
        })

    # Step 3: 读取自选股和绑定
    stocks = []
    for stock in db.query(Stock).all():
        stock_agents = []
        for sa in db.query(StockAgent).filter(StockAgent.stock_id == stock.id).all():
            stock_agents.append({
                "agent_name": sa.agent_name,
                "schedule": sa.schedule or "",
                "ai_model_id": sa.ai_model_id,
                "notify_channel_ids": sa.notify_channel_ids or [],
            })
        stocks.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "market": stock.market,
            "agents": stock_agents,
        })

    return {"version": 1, "exported_at": datetime.now(timezone.utc).isoformat(),
            "settings": settings, "agents": agents, "stocks": stocks}
```

## merge vs replace 模式

| 模式 | 行为 |
|------|------|
| `merge` | 仅更新已有记录的字段，创建不存在的记录，不删除任何数据 |
| `replace` | 对 payload 涵盖的数据（Agent / 股票绑定），删除 payload 中不存在的项后重建 |

## 使用场景

- 开发/测试环境间迁移配置
- 备份当前设置
- 批量部署相同配置到多台服务器
