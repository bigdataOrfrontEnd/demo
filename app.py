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
from sqlalchemy import text # 记得导入 text 组件
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



# 1. 在 main.py（或 schemas 目录）中定义这个接口专属的 Data 结构
class DbTestResponse(BaseModel):
    result: str  # 明确告诉前端和文档，返回的数据里包含一个 string 类型的 result

# 2. 修改路由，使用 response_model 约束返回
@app.get("/api/test-db", response_model=DbTestResponse)  # <-- 绑定 Schema
async def test_db(db: AsyncSession = Depends(get_db)):
    """测试数据库是否能正常连接并执行查询"""
    try:
        result = await db.execute(text("SELECT 1"))
        val = result.scalar()
        
        # 💡 这里直接返回契约规定的字典，干净、纯粹
        return {"result": f"数据库连接正常，测试返回值: {val}"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库连接失败: {str(e)}"
        )