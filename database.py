import os
import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)
# 无论 database.py 放在哪，都先找到当前工作目录，或者明确指定到根
# 最直接的方法：直接基于当前运行脚本的根目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 如果 database.py 在根目录：
DB_PATH = os.path.join(BASE_DIR, "data", "storewatch.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
print(f"👉 数据库文件绝对路径应该是: {os.path.abspath(DB_PATH)}") # 打印出来看看它到底在哪里！
# 2. 封装公用的【异步】引擎 (Engine)
# 核心变化：使用 create_async_engine 并且协议头改为 sqlite+aiosqlite
engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=False,
    connect_args={
        "timeout": 30,
    },
    poolclass=NullPool,
)


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
    # 此时 engine 是异步的，begin() 能够被 async with 正常解析
    async with engine.begin() as conn:
        # Base.metadata.create_all 是同步建表方法，必须通过 run_sync 在异步连接中执行
        await conn.run_sync(Base.metadata.create_all)