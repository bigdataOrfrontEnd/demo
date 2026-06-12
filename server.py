import logging
import os
import time
from contextlib import asynccontextmanager
import uvicorn
from database import init_db
# 1. 导入刚才创建的 app
from app import app  

# 2. 正确定义 lifespan，必须包含 yield！
@asynccontextmanager
async def lifespan(app):
    """应用生命周期: 初始化 + 启动调度器"""
    print("======== 后端服务启动中 ========")
    # 这里写你的初始化逻辑（比如启动调度器、连接数据库等）
    await init_db()
    
    yield  # <-- 就是这行！必须要 yield，哪怕后面什么都不干
    
    print("======== 后端服务关闭中 ========")
    # 这里写你的清理逻辑

# 3. 动态注入到 app 中（这样写是完全合法的）
app.router.lifespan_context = lifespan

import uvicorn

if __name__ == "__main__":
    print("后端启动: http://127.0.0.1:8000")
    print("API 文档: http://127.0.0.1:8000/docs")
    uvicorn.run(
        "server:app",  # 明确指向 main.py 的 app
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src", "."],
        # 注意：要让排除生效，建议根据提示执行 pip install watchfiles
        reload_excludes=["data/*"], 
    )