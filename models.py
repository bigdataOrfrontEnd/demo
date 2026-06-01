from pydantic import BaseModel, ConfigDict
from sqlalchemy import String, Boolean

from sqlalchemy.orm import Mapped, mapped_column
from typing import List, Optional
from database import Base
# ==========================================
# 1. 定义 SQLAlchemy ORM 模型 (绑定公用的 Base)
# ==========================================
class DBItem(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


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

#定义一个TODOLISt的数据库模型，增加一个字段is_completed，表示是否完成

class DBTodo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False) # 新增：是否完成

