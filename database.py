# database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# 1. 公用的数据库连接配置
DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 2. 封装公用的异步引擎 (Engine)
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. 封装公用的异步会话工厂 (Session Factory)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 4. 公用的 ORM 基类
class Base(DeclarativeBase):
    pass

# 5. 封装公用的依赖项 (Dependency) 获取数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    公用的数据库连接会话生成器。
    FastAPI 的 Depends 会在请求进来时调用它创建会话，并在请求结束时自动关闭。
    """
    async with AsyncSessionLocal() as session:
        yield session

# 6. 封装自动创建数据库和表的函数
async def init_db():
    """
    如果数据库文件或表不存在，则自动创建它们。
    """
    async with engine.begin() as conn:
        # Base.metadata.create_all 会检查表是否存在，不存在则创建
        await conn.run_sync(Base.metadata.create_all)