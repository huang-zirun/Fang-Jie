# -*- coding: utf-8 -*-
"""测试 CDP 驱动内容生成功能"""
import asyncio
import httpx
import json
import sys

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:9090"


async def get_anonymous_token():
    """获取匿名用户 token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/auth/anonymous")
        return response.json()["token"]


async def get_platforms(token: str):
    """获取平台列表"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/platforms",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()


async def get_intents(token: str):
    """获取意图列表"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/intents",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()


async def create_task(token: str, intent_id: str, platform_id: str):
    """创建任务"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"intent_id": intent_id, "platform_id": platform_id}
        )
        return response.json()


async def get_current_task(token: str):
    """获取当前任务"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/tasks/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()


async def main():
    print("=" * 60)
    print("CDP 驱动内容生成测试")
    print("=" * 60)
    
    # 1. 获取 token
    print("\n[1] 获取匿名 token...")
    token = await get_anonymous_token()
    print(f"✅ Token 获取成功: {token[:50]}...")
    
    # 2. 获取平台列表
    print("\n[2] 获取平台列表...")
    platforms = await get_platforms(token)
    if platforms:
        platform = platforms[0]
        platform_id = platform["id"]
        print(f"✅ 使用平台: {platform.get('name', 'Unknown')} (ID: {platform_id})")
    else:
        print("❌ 没有可用平台")
        return
    
    # 3. 获取意图列表
    print("\n[3] 获取意图列表...")
    intents = await get_intents(token)
    if intents:
        intent = intents[0]
        intent_id = intent["id"]
        print(f"✅ 使用意图: {intent.get('name', 'Unknown')} (ID: {intent_id})")
    else:
        print("❌ 没有可用意图")
        return
    
    # 4. 创建任务
    print("\n[4] 创建内容任务...")
    try:
        task = await create_task(token, intent_id, platform_id)
        print(f"✅ 任务创建成功!")
        print(f"   任务 ID: {task.get('id')}")
        print(f"   钩子文案: {task.get('hook_text', 'N/A')}")
        print(f"   标题: {task.get('title', 'N/A')}")
        print(f"\n   完整任务数据:")
        print(json.dumps(task, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 任务创建失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
