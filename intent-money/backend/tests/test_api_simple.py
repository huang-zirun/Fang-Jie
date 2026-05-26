# -*- coding: utf-8 -*-
"""简单测试 API"""
import urllib.request
import json
import sys

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

# 测试抖音搜索 API
url = "http://localhost:8000/api/v1/scraper/douyin/search?keyword=袜子&limit=3"
req = urllib.request.Request(url, method='POST')

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("=" * 60)
        print("抖音搜索 API 测试结果")
        print("=" * 60)
        print(f"关键词: {data['keyword']}")
        print(f"获取数量: {data['count']}")
        print("\n前3条视频（按最多点赞排序）:")
        for i, video in enumerate(data['videos'][:3], 1):
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
url = "http://localhost:8000/api/v1/scraper/xhs/search?keyword=袜子&limit=3"
req = urllib.request.Request(url, method='POST')

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("小红书搜索 API 测试结果")
        print("=" * 60)
        print(f"关键词: {data['keyword']}")
        print(f"获取数量: {data['count']}")
        print("\n前3条笔记（按最多点赞排序）:")
        for i, note in enumerate(data['notes'][:3], 1):
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
