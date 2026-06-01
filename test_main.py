# test_main.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app 
from database import init_db, engine

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    await init_db()
    yield
    await engine.dispose()

@pytest.mark.asyncio
async def test_user_todo_relationship():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. 创建一个用户
        user_res = await ac.post("/users/", json={"username": "张三", "email": "zhangsan@colleg.com"})
        assert user_res.status_code == 201
        user_id = user_res.json()["id"]
        
        # 2. 联动创建：给张三安排一个“学多表联动”的任务
        todo_res = await ac.post(f"/users/{user_id}/todos/", json={"title": "学多表联动"})
        assert todo_res.status_code == 200
        assert todo_res.json()["user_id"] == user_id
        
        # 3. 联动查询：获取张三的资料，看任务是不是在里面
        get_res = await ac.get(f"/users/{user_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        
        assert data["username"] == "张三"
        assert len(data["todos"]) == 1  # 此时这里应该有一条关联任务了！
        assert data["todos"][0]["title"] == "学多表联动"