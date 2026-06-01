# test_main.py
import pytest
from httpx import AsyncClient, ASGITransport  # 1. 额外导入 ASGITransport
from main import app 

@pytest.mark.asyncio
async def test_create_and_read_item():
    # 2. 将 app 封装进 ASGITransport 中
    transport = ASGITransport(app=app)
    
    # 3. 将 transport 传给 AsyncClient
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 下面的测试逻辑保持完全不变
        # 1. 测试 POST (创建)
        payload = {"title": "测试商品", "description": "这是一个自动化测试生成的商品"}
        response = await ac.post("/items/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试商品"
        assert "id" in data
        item_id = data["id"]

        # 2. 测试 GET (获取单个详情)
        response_get = await ac.get(f"/items/{item_id}")
        assert response_get.status_code == 200
        assert response_get.json()["title"] == "测试商品"