import logging
import os
import time
from contextlib import asynccontextmanager
import main
import uvicorn



if __name__ == "__main__":
    print("后端启动: http://127.0.0.1:8000")
    print("API 文档: http://127.0.0.1:8000/docs")
    uvicorn.run(
        "server:main",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # reload_dirs=["src", "."],
        reload_excludes=["data/*"],
    )