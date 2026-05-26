"""调试 API 响应"""
import requests

# 测试抖音搜索 API
print("=" * 60)
print("调试抖音搜索 API")
print("=" * 60)

try:
    resp = requests.post(
        "http://localhost:8000/api/v1/scraper/douyin/search",
        params={"keyword": "袜子", "limit": 2},
        timeout=30
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Response Keys: {resp.json().keys()}")
    print(f"Full Response: {resp.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
