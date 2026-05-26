"""调试 API 响应"""
import asyncio
import httpx


async def test_api():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://localhost:8000/api/v1/scraper/douyin/search?keyword=袜子&limit=2",
                timeout=30.0
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")


asyncio.run(test_api())
