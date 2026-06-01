# main.py
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.future import select
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
# 导入刚才封装的数据库公共模块
from database import engine, get_db, init_db
from models import DBItem
# ==========================================
# 2. Pydantic 数据校验模型 (Schemas)
# ==========================================
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 3. FastAPI 生命周期管理 (Lifespan)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 【核心修改】应用启动时：调用公共的 init_db 检查并自动创建数据库/表
    await init_db()
    yield
    # 应用关闭时：可以在这里做清理工作（例如关闭引擎，虽然异步引擎会自动管理，但显式调用更安全）
    await engine.dispose()


# 初始化 FastAPI 并挂载生命周期
app = FastAPI(title="FastAPI 异步公用连接 Demo", lifespan=lifespan)

# ==========================================
# 4. 路由接口 (直接使用公用的 get_db 依赖),后端开发要思考的重点是数据返回给前端的是什么，数据库存储的是什么
# ==========================================

# ---- 接口 1: 创建数据 ----
@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    db_item = DBItem(title=item.title, description=item.description)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

# ---- 接口 2: 获取列表 ----
@app.get("/items/", response_model=List[ItemResponse])
async def read_items(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBItem).offset(skip).limit(limit))
    items = result.scalars().all()
    return items

# ---- 接口 3: 获取单个详情 ----
@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBItem).where(DBItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item