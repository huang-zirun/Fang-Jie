"""最终 API 测试 - 使用正确端口 9090"""
import requests

BASE_URL = "http://localhost:9090/api/v1"

# 测试健康检查
print("=" * 60)
print("1. 健康检查")
print("=" * 60)
try:
    resp = requests.get(f"{BASE_URL}/scraper/health", timeout=5)
    data = resp.json()
    print(f"抖音: healthy={data['douyin']['healthy']}")
    print(f"小红书: healthy={data['xhs']['healthy']}")
except Exception as e:
    print(f"Error: {e}")

# 测试抖音搜索 API
print("\n" + "=" * 60)
print("2. 抖音搜索 API（按最多点赞排序）")
print("=" * 60)

try:
    resp = requests.post(
        f"{BASE_URL}/scraper/douyin/search",
        params={"keyword": "袜子", "limit": 5},
        timeout=30
    )
    data = resp.json()
    print(f"关键词: {data['keyword']}")
    print(f"获取数量: {data['count']}")
    print("\n前5条视频:")
    for i, video in enumerate(data['videos'][:5], 1):
        stats = video.get('statistics', {})
        title = video.get('title', 'N/A')[:35]
        digg_count = stats.get('digg_count', 0)
        author = video.get('author', {}).get('nickname', 'N/A')
        print(f"\n  [{i}] {title}...")
        print(f"      点赞: {digg_count:,} | 作者: {author}")
except Exception as e:
    print(f"Error: {e}")

# 测试小红书搜索 API
print("\n" + "=" * 60)
print("3. 小红书搜索 API（按最多点赞排序）")
print("=" * 60)

try:
    resp = requests.post(
        f"{BASE_URL}/scraper/xhs/search",
        params={"keyword": "袜子", "limit": 5},
        timeout=30
    )
    data = resp.json()
    print(f"关键词: {data['keyword']}")
    print(f"获取数量: {data['count']}")
    print("\n前5条笔记:")
    for i, note in enumerate(data['notes'][:5], 1):
        title = note.get('title', 'N/A')[:35]
        liked_count = note.get('liked_count', 0)
        author = note.get('author', 'N/A')
        print(f"\n  [{i}] {title}...")
        print(f"      点赞: {liked_count} | 作者: {author}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("API 测试完成！")
print("=" * 60)
