"""测试 API 热门排序功能"""
import asyncio
import httpx


async def test_douyin_api():
    """测试抖音搜索 API"""
    print("=" * 60)
    print("测试抖音搜索 API")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/api/v1/scraper/douyin/search?keyword=袜子&limit=5"
        )
        data = resp.json()

        print(f"关键词: {data['keyword']}")
        print(f"获取数量: {data['count']}")
        print("\n前5条视频（默认已按最多点赞排序）:")

        for i, video in enumerate(data['videos'][:5], 1):
            stats = video.get('statistics', {})
            title = video.get('title', 'N/A')[:30]
            digg_count = stats.get('digg_count', 0)
            author = video.get('author', {}).get('nickname', 'N/A')
            print(f"  [{i}] {title}... - 点赞: {digg_count:,}")
            print(f"      作者: {author}")


async def test_xhs_api():
    """测试小红书搜索 API"""
    print("\n" + "=" * 60)
    print("测试小红书搜索 API")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/api/v1/scraper/xhs/search?keyword=袜子&limit=5"
        )
        data = resp.json()

        print(f"关键词: {data['keyword']}")
        print(f"获取数量: {data['count']}")
        print("\n前5条笔记（默认已按最多点赞排序）:")

        for i, note in enumerate(data['notes'][:5], 1):
            title = note.get('title', 'N/A')[:30]
            liked_count = note.get('liked_count', 0)
            author = note.get('author', 'N/A')
            print(f"  [{i}] {title}... - 点赞: {liked_count}")
            print(f"      作者: {author}")


async def main():
    print("API 热门排序功能测试")
    print("=" * 60)

    try:
        await test_douyin_api()
        await test_xhs_api()

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n测试失败: {e}")
        print("请确保后端服务已启动: uv run uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
