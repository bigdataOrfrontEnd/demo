# models.py
from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# 1. 用户表
class DBUser(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True)

    # 联动配置：一个用户拥有多个 todos
    # back_populates 用于双向绑定，告诉 SQLAlchemy 对方表里的属性叫 'owner'
    todos: Mapped[List["DBTodo"]] = relationship("DBTodo", back_populates="owner", cascade="all, delete-orphan")


# 2. Todo任务表
class DBTodo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 核心：外键，绑定到 users 表的 id 字段
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 联动配置：属于某一个用户
    owner: Mapped["DBUser"] = relationship("DBUser", back_populates="todos")