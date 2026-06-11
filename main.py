# main.py
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # 异步联合查询的关键组件
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from database import engine, get_db, init_db
from response import ResponseWrapperMiddleware

app = FastAPI(
    title="PanWatch API",
    version="0.1.0",
    redirect_slashes=False,  # 避免重定向丢失 Authorization header
)
# 请求的统一封装
app.add_middleware(ResponseWrapperMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
