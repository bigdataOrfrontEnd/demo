import logging
import os
import time
from contextlib import asynccontextmanager
import uvicorn
from database import init_db
import asyncio  # 导入 asyncio
# 在所有逻辑执行前，配置一下根日志级别
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
# 1. 导入刚才创建的 app
from app import app  
def setup_playwright():
    """检查并安装 Playwright 浏览器

    本地开发时使用系统安装的 Playwright，Docker 环境下安装到 data 目录。
    通过 DOCKER 环境变量或显式设置的 PLAYWRIGHT_BROWSERS_PATH 来判断。
    """
    import subprocess

    # 允许通过环境变量跳过首次安装（例如不需要截图功能时）
    if os.environ.get("PLAYWRIGHT_SKIP_BROWSER_INSTALL") == "1":
        logger.info(
            "已设置 PLAYWRIGHT_SKIP_BROWSER_INSTALL=1，跳过 Playwright 浏览器安装"
        )
        return

    # 如果用户已显式设置 PLAYWRIGHT_BROWSERS_PATH，尊重该设置
    if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
        browser_dir = os.environ["PLAYWRIGHT_BROWSERS_PATH"]
        logger.info(f"使用自定义 Playwright 路径: {browser_dir}")
    # Docker 环境下安装到 data 目录
    elif os.environ.get("DOCKER") == "1":
        data_dir = os.environ.get("DATA_DIR", "./data")
        browser_dir = os.path.join(data_dir, "playwright")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_dir
        logger.info(f"Docker 环境，Playwright 路径: {browser_dir}")
    else:
        # 本地开发，使用系统默认路径，不做任何安装
        logger.info("本地开发环境，使用系统 Playwright")
        return

    # 检查是否已安装
    if os.path.exists(browser_dir):
        try:
            dirs = os.listdir(browser_dir)
            if any(
                d.startswith("chromium")
                for d in dirs
                if os.path.isdir(os.path.join(browser_dir, d))
            ):
                logger.info(f"Playwright 浏览器已就绪: {browser_dir}")
                return
        except Exception:
            pass

    # 首次安装
    logger.info("首次启动，正在安装 Playwright 浏览器（可能需要几分钟）...")
    os.makedirs(browser_dir, exist_ok=True)

    try:
        result = subprocess.run(
            ["playwright", "install", "chromium"],
            env={**os.environ, "PLAYWRIGHT_BROWSERS_PATH": browser_dir},
            capture_output=True,
            text=True,
            timeout=600,  # 10 分钟超时
        )
        if result.returncode == 0:
            logger.info("Playwright 浏览器安装完成")
        else:
            logger.error(f"Playwright 安装失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("Playwright 安装超时（网络问题？）")
    except FileNotFoundError:
        logger.warning("Playwright 命令不可用，K线截图功能不可用")
    except Exception as e:
        logger.error(f"Playwright 安装失败: {e}")

# 2. 正确定义 lifespan，必须包含 yield！
@asynccontextmanager
async def lifespan(app):
    """应用生命周期: 初始化 + 启动调度器"""
    print("======== 后端服务启动中 ========")
    # 这里写你的初始化逻辑（比如启动调度器、连接数据库等）
    await init_db()
    # 2. 错误修正：把同步的阻塞函数扔进线程池运行，避免卡死异步主线程
    await asyncio.to_thread(setup_playwright)
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