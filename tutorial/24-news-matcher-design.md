# 模块设计: 新闻撮合系统 (News Matcher)

> **状态**: 设计文档  
> **目标**: 集成 newsnow.busiyi.world 新闻源，实现「新闻 → 板块 → 个股」的撮合链路，增强 AI 分析的宏观上下文

---

## 一、现状分析：AI 当前接收的数据

在设计新模块之前，先梳理现有数据管线——AI 分析时到底收到了什么数据：

### 1.1 数据采集层 (SignalPackBuilder)

```
SignalPackBuilder.build_for_symbols()
├── quote        ← AkshareCollector (腾讯行情 API)
├── technical    ← KlineCollector.get_kline_summary() 
│                 (MACD/RSI/MA/布林/趋势/形态/支撑压力)
├── news         ← NewsCollector (东方财富资讯+公告+雪球)
│                 每只股票 5 条最新相关新闻
├── capital_flow ← CapitalFlowCollector (东方财富资金流, 仅A股)
│                 主力净流入/5日趋势
├── events       ← EventsCollector (东方财富公告结构化, 近N天)
│                 财报/分红/增减持等事件
└── position     ← 从 portfolio 读取持仓信息
                   (成本/数量/交易风格)
```

### 1.2 上下文增强层 (ContextBuilder)

```
ContextBuilder.build_symbol_contexts()
├── realtime_news  ← 12h 内新闻，rank + dedupe
├── extended_news  ← 72h 内新闻，rank + dedupe
├── history_news   ← 从 analysis_history 表回读历史分析中的新闻 (7-30天)
├── history_topic  ← summarize_news_topics(history_news) → 主题词+情绪
├── kline_history  ← 120日K线走势 (5d/20d/60d 收益率)
├── constraints    ← 账户资金约束 (总可用/单票占比/风险预算)
├── memory         ← 跨天快照 (近30天质量分趋势/历史主题)
├── events         ← 公告事件快照
└── quality_score  ← 数据覆盖度综合评分 (100分制)
```

### 1.3 Prompt 构建层 (以 DailyReportAgent 为例)

AI 收到的每只股票的 prompt 内容：

```
### 贵州茅台（600519）
- 今日：1680.50 ↑ +1.23%
- 振幅：1.5%  最高1685.00 最低1660.00
- 成交额：207.36亿
- 均线：MA5=1670.00 MA10=1650.00 MA20=1630.00
- 趋势：上涨趋势，MACD 金叉
- RSI：65.2（中性偏强）
- 布林：中轨上方（上轨1720.00 下轨1580.00）
- 资金：主力净流入，主力净流入+3.25亿（+2.1%）
- 相关新闻：
  - [14:30] ⭐茅台发布年报，净利润增长15%（东财）
- 持仓：100股 成本1600.00 浮盈+5.0%（波段）
- 资金约束：总可用500000元，单票仓位占比32.0%（strict）
- 历史上下文记忆：近30天质量均值85.0，趋势stable
```

### 1.4 当前缺口

| 缺口 | 说明 |
|------|------|
| **宏观新闻缺失** | 只有个股相关新闻，没有市场宏观/行业/政策新闻 |
| **板块概念缺失** | AI 不知道新闻涉及哪些行业板块 |
| **个股映射缺失** | 无法从宏观新闻自动关联到受影响的自选股 |
| **新闻溯源缺失** | 历史分析中的新闻不可追溯，无法回查原文 |
| **新闻持久化** | 新闻散落在各次分析的 raw_data 中，没有统一存储 |

---

## 二、设计目标

### 2.1 核心能力

```
新闻采集 → 落盘存储 → 板块识别 → 个股映射 → 上下文注入 → AI分析
```

1. **新闻采集**: 从 newsnow.busiyi.world 抓取实时新闻
2. **落盘存储**: 结构化存储到数据库，支持去重和检索
3. **板块识别**: 通过 AI + 规则引擎识别新闻涉及的行业/概念板块
4. **个股映射**: 将板块映射到对应的个股（包括用户的自选股）
5. **上下文注入**: 将撮合结果注入到 Agent 的 AI prompt 中
6. **可追溯**: 新闻和历史分析建立关联

### 2.2 新增数据表

```sql
-- 新闻源原始数据表
CREATE TABLE external_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR NOT NULL DEFAULT 'newsnow',     -- 来源标识
    external_id VARCHAR NOT NULL,                   -- 来源侧唯一ID
    title VARCHAR NOT NULL,                         -- 新闻标题
    summary TEXT DEFAULT '',                        -- 新闻摘要
    content TEXT DEFAULT '',                        -- 正文内容
    url VARCHAR DEFAULT '',                         -- 原始链接
    publish_time DATETIME NOT NULL,                 -- 发布时间
    fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 抓取时间
    
    -- AI 分析结果
    sectors JSON DEFAULT '[]',                     -- 关联板块 [{code, name, confidence}]
    sentiment VARCHAR DEFAULT 'neutral',            -- 情绪: positive/negative/neutral
    importance INTEGER DEFAULT 0,                   -- 重要性 0-5
    ai_summary TEXT DEFAULT '',                     -- AI 摘要（100字以内）
    
    -- 匹配结果
    matched_stocks JSON DEFAULT '[]',              -- 匹配到的个股 [{symbol, market, name, relevance}]
    matched_watchlist JSON DEFAULT '[]',            -- 匹配到的自选股 [stock_id, ...]
    
    -- 元数据
    tags JSON DEFAULT '[]',                        -- 标签
    raw_data JSON DEFAULT '{}',                    -- 原始响应
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source, external_id)
);

CREATE INDEX idx_external_news_time ON external_news(publish_time);
CREATE INDEX idx_external_news_importance ON external_news(importance);
CREATE INDEX idx_external_news_source_time ON external_news(source, publish_time);

-- 板块-股票映射表（预置 + 可维护）
CREATE TABLE sector_stock_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_code VARCHAR NOT NULL,         -- 板块代码
    sector_name VARCHAR NOT NULL,         -- 板块名称
    stock_symbol VARCHAR NOT NULL,        -- 股票代码
    stock_market VARCHAR NOT NULL,        -- 市场 CN/HK/US
    stock_name VARCHAR DEFAULT '',        -- 股票名称
    relevance FLOAT DEFAULT 0.5,          -- 关联度 0-1
    source VARCHAR DEFAULT 'manual',      -- 来源: manual/ai/auto
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sector_code, stock_symbol, stock_market)
);

CREATE INDEX idx_sector_mapping_sector ON sector_stock_mapping(sector_code);
CREATE INDEX idx_sector_mapping_stock ON sector_stock_mapping(stock_symbol, stock_market);

-- 新闻分析记录表（关联 external_news 和 analysis_history）
CREATE TABLE news_analysis_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER NOT NULL REFERENCES external_news(id) ON DELETE CASCADE,
    analysis_history_id INTEGER REFERENCES analysis_history(id) ON DELETE SET NULL,
    stock_symbol VARCHAR NOT NULL,          -- 关联的股票
    relevance_score FLOAT DEFAULT 0.5,     -- 对该股票的相关度
    used_in_prompt BOOLEAN DEFAULT FALSE,   -- 是否已注入 AI prompt
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_nal_news (news_id),
    INDEX idx_nal_analysis (analysis_history_id),
    INDEX idx_nal_stock (stock_symbol)
);
```

### 2.3 新增文件结构

```
src/
├── collectors/
│   └── newsnow_collector.py    # newsnow.busiyi.world 采集器
├── core/
│   ├── news_matcher.py         # 新闻撮合引擎（板块识别 + 个股映射）
│   ├── sector_registry.py      # 板块注册表（板块定义 + 关键词）
│   └── news_matcher_scheduler.py # 定时调度：拉取+分析+撮合
└── web/api/
    └── external_news.py        # 新闻查询 API
```

---

## 三、核心实现设计

### 3.1 新闻采集器 (NewsNowCollector)

```python
# src/collectors/newsnow_collector.py

import httpx
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExternalNewsItem:
    source: str = "newsnow"
    external_id: str = ""
    title: str = ""
    summary: str = ""
    content: str = ""
    url: str = ""
    publish_time: datetime | None = None

class NewsNowCollector:
    """
    newsnow.busiyi.world 新闻采集器
    
    API: https://newsnow.busiyi.world/api/...
    （实际 API 端点需要根据 newsnow 的接口文档确定）
    """
    
    BASE_URL = "https://newsnow.busiyi.world"
    
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
    
    async def fetch_latest(
        self, 
        since: datetime | None = None,
        limit: int = 50,
        categories: list[str] | None = None,
    ) -> list[ExternalNewsItem]:
        """
        拉取最新新闻
        
        Args:
            since: 起始时间
            limit: 条数限制
            categories: 分类过滤（如 ["财经", "科技", "政策"]）
        """
        # Step 1: 尝试 API 接口
        # Step 2: 若 API 不可用，降级为 HTML 解析
        # Step 3: 返回标准化 ExternalNewsItem 列表
        ...
    
    async def fetch_by_keyword(
        self, 
        keyword: str, 
        limit: int = 20
    ) -> list[ExternalNewsItem]:
        """按关键词搜索新闻"""
        ...
    
    async def fetch_article(self, url: str) -> str | None:
        """获取单篇文章全文"""
        ...
```

### 3.2 板块注册表 (SectorRegistry)

```python
# src/core/sector_registry.py

# 板块定义：code -> {name, keywords, market_focus}
SECTOR_DEFINITIONS = {
    "ai_computing": {
        "name": "AI算力",
        "keywords": ["AI", "人工智能", "算力", "GPU", "大模型", "ChatGPT", 
                     "深度学习", "机器学习", "神经网络", "NLP", "LLM"],
        "market_focus": ["CN", "US"],
    },
    "semiconductor": {
        "name": "半导体",
        "keywords": ["芯片", "半导体", "晶圆", "光刻", "封装", "EDA", 
                     "存储", "HBM", "先进制程", "台积电", "中芯国际"],
        "market_focus": ["CN", "US", "HK"],
    },
    "new_energy": {
        "name": "新能源",
        "keywords": ["光伏", "风电", "储能", "锂电池", "钠电池", "固态电池",
                     "氢能", "碳中和", "碳达峰", "绿电", "特高压"],
        "market_focus": ["CN"],
    },
    "auto_industry": {
        "name": "汽车产业",
        "keywords": ["新能源汽车", "智能驾驶", "自动驾驶", "车规芯片",
                     "比亚迪", "特斯拉", "蔚来", "小鹏", "理想"],
        "market_focus": ["CN", "US", "HK"],
    },
    "consumer": {
        "name": "大消费",
        "keywords": ["白酒", "食品", "饮料", "家电", "服装", "零售",
                     "旅游", "餐饮", "免税", "医美"],
        "market_focus": ["CN", "HK"],
    },
    "pharma": {
        "name": "医药健康",
        "keywords": ["创新药", "仿制药", "疫苗", "CXO", "医疗器械",
                     "中药", "基因编辑", "精准医疗"],
        "market_focus": ["CN", "HK"],
    },
    # ... 更多板块
}

# 从数据库加载板块-个股映射
def load_sector_stock_mapping() -> dict[str, list[dict]]:
    """
    返回 {sector_code: [{symbol, market, name, relevance}, ...]}
    """
    ...

def match_news_to_sectors(
    title: str, 
    content: str,
    use_ai: bool = False,
) -> list[dict]:
    """
    新闻 → 板块匹配
    
    两层策略：
    1. 规则匹配（快速）：关键词匹配，返回置信度
    2. AI 匹配（精准）：调用 LLM 做语义分析
    
    返回: [{code, name, confidence}, ...]
    """
    ...
```

### 3.3 新闻撮合引擎 (NewsMatcher)

```python
# src/core/news_matcher.py

class NewsMatcher:
    """
    核心撮合引擎：实现「新闻 → 板块 → 个股 → 自选股」的完整链路
    """
    
    def __init__(self):
        self._sector_stock_map = None
    
    async def process_news_batch(
        self, 
        news_items: list[ExternalNewsItem],
        use_ai: bool = True,
    ) -> dict:
        """
        Step 1: 逐条处理新闻
        Step 2: 板块识别（规则 + AI）
        Step 3: 个股映射（查 sector_stock_mapping）
        Step 4: 自选股匹配（交集自选股列表）
        Step 5: 落盘存储
        Step 6: 返回撮合结果
        """
        ...

    def match_sector_to_stocks(
        self, 
        sector_codes: list[str],
        watchlist: list | None = None,
    ) -> dict[str, list]:
        """
        板块 → 个股映射
        
        返回: {sector_code: [{symbol, market, name, relevance}, ...]}
        如果传入 watchlist，额外标记哪些是自选股
        """
        ...
    
    def build_context_for_agent(
        self,
        matched_news: list[dict],
        max_news: int = 10,
    ) -> dict:
        """
        构建注入 AI prompt 的新闻上下文
        
        返回:
        {
            "summary": "今日宏观要闻摘要...",
            "sectors_mentioned": ["AI算力", "半导体"],
            "hot_news": [...],          # top 5 重要新闻
            "watchlist_related": [...], # 与自选股相关的新闻
            "sentiment": "偏多",
        }
        """
        ...

# 全局单例
_matcher: NewsMatcher | None = None

def get_news_matcher() -> NewsMatcher:
    global _matcher
    if _matcher is None:
        _matcher = NewsMatcher()
    return _matcher
```

### 3.4 定时调度器 (NewsMatcherScheduler)

```python
# src/core/news_matcher_scheduler.py

class NewsMatcherScheduler:
    """
    新闻撮合定时任务
    
    执行频率：每 30 分钟（可配置）
    执行内容：
    1. 从 newsnow 拉取最新新闻
    2. 新新闻 → 板块识别 + 个股映射 + 落盘
    3. 匹配到自选股的新闻 → 写入 news_analysis_link
    """
    
    def __init__(self, interval_minutes: int = 30):
        self.interval = interval_minutes
    
    async def run_once(self) -> dict:
        """执行一次完整的新闻采集+撮合流程"""
        collector = NewsNowCollector()
        
        # Step 1: 拉取最新新闻
        news_items = await collector.fetch_latest(limit=100)
        if not news_items:
            return {"status": "empty", "count": 0}
        
        # Step 2: 去重（检查 external_news 表）
        new_items = self._filter_new(news_items)
        if not new_items:
            return {"status": "no_new", "count": 0}
        
        # Step 3: 逐条撮合
        matcher = get_news_matcher()
        result = await matcher.process_news_batch(new_items, use_ai=True)
        
        return {
            "status": "ok",
            "fetched": len(news_items),
            "new": len(new_items),
            "matched_sectors": result.get("sector_hits", 0),
            "matched_watchlist": result.get("watchlist_hits", 0),
        }

# 在 server.py 的 lifespan 中启动
```

### 3.5 API 端点

```python
# src/web/api/external_news.py

router = APIRouter(prefix="/api/external-news", tags=["external_news"])

@router.get("/latest")
def get_latest_news(
    limit: int = 20,
    min_importance: int = 0,
    sectors: str = "",           # 逗号分隔的板块代码
    symbols: str = "",           # 逗号分隔的股票代码
    since: str = "",             # ISO 时间
    db: Session = Depends(get_db),
):
    """获取最新外部新闻（支持板块/股票筛选）"""
    ...

@router.get("/{news_id}")
def get_news_detail(news_id: int, db: Session = Depends(get_db)):
    """获取单条新闻详情（含板块/个股匹配结果）"""
    ...

@router.get("/watchlist-related")
def get_watchlist_related_news(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取与当前自选股相关的外部新闻"""
    ...

@router.get("/sector-summary")
def get_sector_news_summary(
    sector_code: str,
    days: int = 7,
    db: Session = Depends(get_db),
):
    """获取某个板块近期的新闻摘要"""
    ...

@router.post("/scan")
async def trigger_scan():
    """手动触发新闻采集+撮合"""
    scheduler = get_news_matcher_scheduler()
    result = await scheduler.run_once()
    return result

@router.get("/sectors")
def list_sectors():
    """获取板块定义列表（含关键词）"""
    ...
```

---

## 四、集成方案：将撮合结果注入 AI 分析

### 4.1 在 ContextBuilder 中增加新闻上下文

在现有的 `build_symbol_contexts()` 方法中，增加一个步骤：

```python
# 在 ContextBuilder.build_symbol_contexts() 中新增：

async def build_symbol_contexts(self, ...):
    # ... 现有逻辑 ...
    
    # 新增：加载外部新闻撮合结果
    macro_news = self._load_matched_external_news(
        watchlist_symbols=[s.symbol for s in context.watchlist],
        hours=24,
    )
    
    # 注入到每个 symbol 的 context 中
    for symbol, ctx in symbol_contexts.items():
        ctx["external_news"] = macro_news.get("watchlist_related", {}).get(symbol, [])
    
    # 在 quality_overview 中增加宏观新闻摘要
    quality_overview["macro_news"] = macro_news.get("summary", {})
    
    return {
        "symbols": symbol_contexts,
        "quality_overview": quality_overview,
        "macro_news": macro_news,  # 新增
    }
```

### 4.2 在 Agent Prompt 中增加宏观新闻段

在 `DailyReportAgent.build_prompt()` 中，增加一个新闻段落：

```python
def build_prompt(self, data, context):
    lines = []
    
    # ... 现有内容 ...
    
    # 新增：宏观新闻摘要
    macro_news = data.get("macro_news", {})
    if macro_news:
        lines.append("\n## 今日宏观要闻")
        lines.append(f"- 整体情绪: {macro_news.get('sentiment', 'neutral')}")
        lines.append(f"- 热点板块: {', '.join(macro_news.get('sectors_mentioned', []))}")
        for news in macro_news.get("hot_news", [])[:8]:
            lines.append(
                f"- [{news['importance']}★] {news['title']} "
                f"（板块: {', '.join(s['name'] for s in news.get('sectors', []))}"
                f"{' 🔗关联自选' if news.get('has_watchlist') else ''}）"
            )
    
    # 在每只股票的分析中，增加该股票相关的宏观新闻
    for w in context.watchlist:
        # ... 现有股票分析内容 ...
        ctx = symbol_contexts.get(w.symbol, {})
        matched_news = ctx.get("external_news", [])
        if matched_news:
            lines.append("- 📰 相关宏观新闻：")
            for n in matched_news[:3]:
                lines.append(f"  - {n['title']}")
```

### 4.3 AI 收到的增强版 Prompt 示例

```
## 今日宏观要闻
- 整体情绪: 偏多
- 热点板块: AI算力, 半导体, 新能源
- [5★] 国务院发布人工智能产业发展新政策（板块: AI算力, 半导体 🔗关联自选）
- [4★] 英伟达发布新一代GPU芯片，算力提升300%（板块: AI算力, 半导体 🔗关联自选）
- [3★] 光伏行业迎来新一轮涨价周期（板块: 新能源）

## 大盘指数
- 上证指数: 3350.67 ↑ +0.35%
...

### 昆仑万维（300418）
- 今日：48.50 ↑ +3.23%
...
- 📰 相关宏观新闻：
  - 国务院发布人工智能产业发展新政策
  - 英伟达发布新一代GPU芯片，算力提升300%
```

---

## 五、实施步骤（分阶段）

### Phase 1: 基础设施（1-2天）

- [ ] 创建 `external_news`、`sector_stock_mapping`、`news_analysis_link` 三张表
- [ ] 创建 `src/core/sector_registry.py`：预置 8-12 个核心板块定义和关键词
- [ ] 创建 `src/collectors/newsnow_collector.py`：实现新闻拉取和解析
- [ ] 预置基础的板块-个股映射数据（50+ 个股）

### Phase 2: 撮合引擎（2-3天）

- [ ] 创建 `src/core/news_matcher.py`：实现规则匹配（关键词）
- [ ] 实现 AI 匹配：调用 LLM 做新闻 → 板块语义分析
- [ ] 实现板块 → 个股映射（查表 + AI 补充）
- [ ] 实现自选股交集匹配
- [ ] 落盘逻辑：去重 + 写入 external_news 表

### Phase 3: 调度与 API（1-2天）

- [ ] 创建 `src/core/news_matcher_scheduler.py`：定时拉取+撮合
- [ ] 在 `server.py` lifespan 中启动调度器
- [ ] 创建 `src/web/api/external_news.py`：查询 API
- [ ] 实现新闻检索（按板块/股票/时间/重要性）

### Phase 4: AI 集成（1-2天）

- [ ] 修改 `ContextBuilder.build_symbol_contexts()`：加载外部新闻
- [ ] 修改 `DailyReportAgent.build_prompt()`：注入宏观新闻段
- [ ] 修改 `IntradayMonitorAgent.build_prompt()`：注入实时新闻
- [ ] 修改 `PremarketOutlookAgent.build_prompt()`：注入隔夜新闻

### Phase 5: 数据积累与优化（持续）

- [ ] 积累板块-个股映射数据
- [ ] 优化关键词匹配准确率
- [ ] 增加新闻追溯：从分析结果跳转到原文
- [ ] 新增 DataSource 类型 `external_news` 用于 UI 管理

---

## 六、板块分类体系设计

### 6.1 预置板块

| 板块代码 | 名称 | 市场 | 关键词数量 |
|---------|------|------|----------|
| ai_computing | AI算力 | CN/US | 12 |
| semiconductor | 半导体 | CN/US/HK | 14 |
| new_energy | 新能源 | CN | 10 |
| auto_industry | 汽车产业 | CN/US/HK | 10 |
| consumer | 大消费 | CN/HK | 10 |
| pharma | 医药健康 | CN/HK | 10 |
| fintech | 金融科技 | CN/US/HK | 8 |
| real_estate | 房地产 | CN/HK | 8 |
| military | 军工 | CN | 8 |
| metals | 有色/稀土 | CN | 8 |
| infra | 基建/建材 | CN/HK | 8 |
| digital_economy | 数字经济 | CN | 8 |

### 6.2 板块识别规则

```
优先级从高到低：
1. 精确匹配：标题含板块核心词 + 正文字数 > 200 → confidence 0.9
2. 模糊匹配：标题含板块扩展词 → confidence 0.7
3. AI 匹配：标题+摘要发给 LLM 做分类 → confidence 0.6-0.9
4. 相关匹配：仅正文含关键词 → confidence 0.4
```

### 6.3 板块 → 个股映射示例

```json
{
  "ai_computing": [
    {"symbol": "300418", "market": "CN", "name": "昆仑万维", "relevance": 0.92},
    {"symbol": "300033", "market": "CN", "name": "同花顺", "relevance": 0.78},
    {"symbol": "002230", "market": "CN", "name": "科大讯飞", "relevance": 0.95},
    {"symbol": "688111", "market": "CN", "name": "金山办公", "relevance": 0.85},
    {"symbol": "NVDA", "market": "US", "name": "英伟达", "relevance": 0.98},
    {"symbol": "MSFT", "market": "US", "name": "微软", "relevance": 0.90}
  ],
  "semiconductor": [
    {"symbol": "688981", "market": "CN", "name": "中芯国际", "relevance": 0.98},
    {"symbol": "002371", "market": "CN", "name": "北方华创", "relevance": 0.95},
    {"symbol": "603986", "market": "CN", "name": "兆易创新", "relevance": 0.88}
  ]
}
```

---

## 七、数据流全貌（集成后）

```
NewsNowCollector (每30分钟)
  ↓
external_news 表 (落盘+去重)
  ↓
NewsMatcher.process_news_batch()
├── 规则匹配 → sector_registry.py (关键词匹配)
├── AI 匹配   → LLM (语义分析)
├── 板块→个股  → sector_stock_mapping 表
└── 自选股交集 → stocks 表
  ↓
external_news.matched_stocks / matched_watchlist 更新
news_analysis_link 写入（关联分析记录）
  ↓
────────────────── Agent 执行时 ──────────────────
  ↓
ContextBuilder._load_matched_external_news()
  ↓
Agent.build_prompt() 注入
  ↓
AI 收到增强版 Prompt（含宏观新闻+板块上下文）
  ↓
AI 分析结果 → analysis_history 表
  ↓
news_analysis_link.analysis_history_id 回填
```

---

## 八、API 响应示例

### GET /api/external-news/latest?limit=5

```json
[
  {
    "id": 123,
    "title": "国务院发布人工智能产业发展新政策",
    "summary": "国务院办公厅印发《关于加快人工智能产业发展的若干意见》...",
    "url": "https://newsnow.busiyi.world/...",
    "publish_time": "2026-05-21 09:30:00",
    "importance": 5,
    "sentiment": "positive",
    "sectors": [
      {"code": "ai_computing", "name": "AI算力", "confidence": 0.95},
      {"code": "semiconductor", "name": "半导体", "confidence": 0.72}
    ],
    "matched_stocks": [
      {"symbol": "300418", "market": "CN", "name": "昆仑万维", "relevance": 0.88},
      {"symbol": "002230", "market": "CN", "name": "科大讯飞", "relevance": 0.92}
    ],
    "matched_watchlist": [5, 12]
  }
]
```

### GET /api/external-news/watchlist-related

返回与当前自选股直接相关的外部新闻，按相关股票分组：

```json
{
  "300418": [
    {"id": 123, "title": "国务院发布人工智能产业发展新政策", "importance": 5},
    {"id": 120, "title": "AI大模型市场规模预计突破千亿", "importance": 4}
  ],
  "002230": [
    {"id": 123, "title": "国务院发布人工智能产业发展新政策", "importance": 5}
  ]
}
```
