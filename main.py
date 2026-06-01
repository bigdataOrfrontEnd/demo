# main.py
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # 异步联合查询的关键组件
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, get_db, init_db
import models

# ---- Pydantic Schemas ----
class TodoCreate(BaseModel):
    title: str

class TodoResponse(BaseModel):
    id: int
    title: str
    is_completed: bool
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    email: str

# 联动的响应模型：返回用户信息时，顺便带上他的 todos 列表
class UserWithTodosResponse(BaseModel):
    id: int
    username: str
    email: str
    todos: List[TodoResponse] = []  # 嵌套 Todo 模型
    model_config = ConfigDict(from_attributes=True)


# ---- 生命周期 ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()

app = FastAPI(title="多表联动 Demo", lifespan=lifespan)


# ---- 接口 1: 创建用户 ----
@app.post("/users/", response_model=UserWithTodosResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = models.DBUser(username=user.username, email=user.email)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# ---- 接口 2: 给指定用户创建 Todo (联动写入) ----
@app.post("/users/{user_id}/todos/", response_model=TodoResponse)
async def create_todo_for_user(user_id: int, todo: TodoCreate, db: AsyncSession = Depends(get_db)):
    # 先检查用户是否存在
    result = await db.execute(select(models.DBUser).where(models.DBUser.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 创建并绑定 user_id
    db_todo = models.DBTodo(title=todo.title, user_id=user_id)
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo


# ---- 接口 3: 获取用户详情，并连带查出他的所有 Todo (联动读取) ----
@app.get("/users/{user_id}", response_model=UserWithTodosResponse)
async def get_user_with_todos(user_id: int, db: AsyncSession = Depends(get_db)):
    # 【异步核心注意点】：在异步 ORM 中，查询主表时若想连带查出子表，
    # 必须显式使用 options(selectinload(...)) 告诉 SQLAlchemy 预加载关联数据，
    # 否则在异步环境下会因为“懒加载（Lazy Load）”而直接报错。
    stmt = select(models.DBUser).where(models.DBUser.id == user_id).options(selectinload(models.DBUser.todos))
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user