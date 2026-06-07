# PanWatch (盯盘侠) 项目教程 - 总览

## 项目定位

PanWatch 是一个 **AI 驱动的股票智能监控系统**，支持 A 股 (CN)、港股 (HK)、美股 (US) 三大市场。核心能力是：

- 通过多个 AI Agent 对自选股进行定时/实时分析
- 基于策略引擎生成买入/卖出/持有建议
- 多数据源聚合行情、K线、新闻、资金流向
- 通过 Telegram 等渠道推送分析结果和提醒

## 整体架构

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  React 前端   │   │  FastAPI 后端  │   │  定时调度器   │
│  (Vite+TS)   │◄─►│  (Python)     │◄─►│  (APScheduler)│
└──────────────┘   └──────┬───────┘   └──────┬───────┘
                          │                  │
                   ┌──────▼───────┐   ┌──────▼───────┐
                   │   SQLite DB  │   │  Agent 引擎   │
                   │  (数据持久化) │   │  (AI 分析)   │
                   └──────────────┘   └──────┬───────┘
                                      ┌──────▼───────┐
                                      │  数据采集器   │
                                      │ (行情/新闻/K线)│
                                      └──────────────┘
```

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | React + TypeScript + Vite + Tailwind CSS |
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy |
| 数据库 | SQLite (WAL 模式，`data/panwatch.db`) |
| AI | 支持 OpenAI/DeepSeek/智谱等任意兼容 API |
| 调度 | APScheduler + 自定义 cron 解析 |
| 推送 | Telegram Bot (可扩展) |
| 部署 | Docker 单容器，数据卷持久化 |

## 项目目录结构

```
PanWatch/
├── server.py              # 启动入口，Agent 注册与调度
├── src/
│   ├── config.py          # 环境变量配置 (Settings)
│   ├── models/market.py   # 市场定义 (CN/HK/US,交易时段)
│   ├── agents/            # Agent 实现
│   │   ├── base.py        # 抽象基类
│   │   ├── daily_report.py      # 盘后日报
│   │   ├── premarket_outlook.py # 盘前展望
│   │   ├── news_digest.py       # 新闻速递
│   │   ├── chart_analyst.py     # 图表分析师
│   │   ├── intraday_monitor.py  # 盘中监测
│   │   └── tradingagents/       # 深度分析 (多分析师辩论)
│   ├── collectors/        # 数据采集器
│   │   ├── akshare_collector.py   # 腾讯行情
│   │   ├── kline_collector.py     # K线数据
│   │   ├── news_collector.py      # 新闻采集
│   │   └── ...
│   ├── core/              # 核心工具
│   │   ├── ai_client.py         # AI 客户端统一封装
│   │   ├── notifier.py          # 通知管理器
│   │   ├── scheduler.py         # Agent 调度器
│   │   ├── strategy_engine.py   # 策略引擎
│   │   ├── suggestion_pool.py   # 建议池
│   │   └── ...
│   └── web/               # FastAPI Web 层
│       ├── app.py         # FastAPI 应用定义
│       ├── database.py    # 数据库连接
│       ├── models.py      # ORM 模型 (30+ 表)
│       ├── api/           # API 路由 (25 个模块)
│       └── ...
├── frontend/              # React 前端
├── prompts/               # AI Prompt 模板
├── config/                # YAML 配置 (watchlist 等)
└── data/                  # 运行时数据 (DB,日志,截图)
```

## Agent 架构

PanWatch 的核心是 **Agent 系统**。每个 Agent 是一个独立的分析任务：

```
BaseAgent (抽象基类)
├── collect()   → 采集数据 (行情/新闻/K线/持仓)
├── build_prompt() → 构建 AI Prompt
├── analyze()   → 调用 AI 模型分析
├── run()       → 标准流程: collect → analyze → notify
└── should_notify() → 判断是否需要通知
```

### Agent 分类

| 类型 | 说明 | 示例 |
|------|------|------|
| `workflow` | 工作流 Agent，参与定时调度 | daily_report, premarket_outlook |
| `capability` | 能力 Agent，仅手动触发 | chart_analyst |

### 已注册 Agent

| Agent 名称 | 中文名 | 触发方式 | 说明 |
|-----------|--------|---------|------|
| `daily_report` | 盘后日报 | 定时 (默认 15:30 工作日) | 批量分析所有自选股收盘情况 |
| `premarket_outlook` | 盘前展望 | 定时 (默认 08:30 工作日) | 盘前市场展望与策略 |
| `news_digest` | 新闻速递 | 定时 | 近期重要新闻汇总 |
| `chart_analyst` | K线图表分析 | 手动 (每只股票) | 技术面图表分析 |
| `intraday_monitor` | 盘中监测 | 前端手动扫描 | 实时异动扫描与 AI 分析 |
| `tradingagents` | 深度分析 | 手动 (每只股票) | 多分析师辩论式深度分析 |

## 数据流

```
用户设置自选股 → 绑定 Agent → 调度触发 / 手动触发
                                    ↓
                            Agent.collect()
                            ├── 实时行情 (腾讯API)
                            ├── K线数据 + 技术指标
                            ├── 新闻聚合 (多源)
                            ├── 资金流向
                            └── 持仓信息
                                    ↓
                            Agent.build_prompt()
                            (构建结构化提示词)
                                    ↓
                            AIClient.chat()
                            (调用 LLM 分析)
                                    ↓
                            Agent.run()
                            ├── 保存分析历史
                            ├── 写入建议池
                            ├── 通知推送 (Telegram)
                            └── 记录执行日志
```

## API 路由总览

| 前缀 | 模块 | 认证 | 说明 |
|------|------|------|------|
| `/api/auth` | auth.py | 否 | 认证（登录/注册） |
| `/api/market` | market.py | 否 | 市场指数（公共数据） |
| `/api/stocks` | stocks.py | 是 | 自选股 CRUD + 触发 |
| `/api/quotes` | quotes.py | 是 | 实时行情 |
| `/api/klines` | klines.py | 是 | K线数据 |
| `/api/insights` | insights.py | 是 | 聚合洞察（行情+K线+建议） |
| `/api/accounts` | accounts.py | 是 | 账户与持仓管理 |
| `/api/agents` | agents.py | 是 | Agent 管理与触发 |
| `/api/providers` | providers.py | 是 | AI 服务商/模型管理 |
| `/api/channels` | channels.py | 是 | 通知渠道管理 |
| `/api/datasources` | datasources.py | 是 | 数据源管理 |
| `/api/settings` | settings.py | 是 | 系统设置 |
| `/api/logs` | logs.py | 是 | 日志中心 |
| `/api/history` | history.py | 是 | 分析历史 |
| `/api/news` | news.py | 是 | 新闻查询 |
| `/api/suggestions` | suggestions.py | 是 | AI 建议池 |
| `/api/templates` | templates.py | 是 | 配置导入导出 |
| `/api/feedback` | feedback.py | 是 | 用户反馈 |
| `/api/discovery` | discovery.py | 是 | 市场发现（热门股票/板块） |
| `/api/price-alerts` | price_alerts.py | 是 | 价格提醒 |
| `/api/recommendations` | recommendations.py | 是 | 入场推荐 |
| `/api/dashboard` | dashboard.py | 是 | 首页仪表盘 |
| `/api/paper-trading` | paper_trading.py | 是 | 模拟交易 |
| `/api/chat` | chat.py | 是 | AI 对话助手 |
| `/api/health` | app.py | 否 | 健康检查 |
| `/api/version` | app.py | 否 | 版本号 |
