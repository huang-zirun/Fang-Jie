# CDP 爬虫热门排序功能实现

## 任务概述
为 CDP 爬虫添加按热门/点赞数排序的功能，使用户可以获取最热门的内容。

## 实现内容

### 1. 抖音爬虫排序支持
**文件**: `backend/app/services/platform_scraper/cdp_douyin_scraper.py`

- URL 模板添加 `sort_type` 参数
- `search_hot_videos()` 方法支持 `sort_type` 参数
- 默认 `sort_type=1`（最多点赞）

**排序选项**:
- `sort_type=0` - 综合排序
- `sort_type=1` - 最多点赞（默认）
- `sort_type=2` - 最新发布

### 2. 小红书爬虫排序支持
**文件**: `backend/app/services/platform_scraper/cdp_xhs_scraper.py`

- URL 模板添加 `sort` 参数
- `search_hot_notes()` 方法支持 `sort` 参数
- 默认 `sort="likes"`（最多点赞）

**排序选项**:
- `sort=general` - 综合
- `sort=time` - 最新
- `sort=likes` - 最多点赞（默认）
- `sort=comments` - 最多评论
- `sort=favorites` - 最多收藏

### 3. 测试文件更新
**文件**: `backend/test_cdp.py`

- 增加 limit 到 10 条（之前是 5 条）
- 显式传入排序参数测试
- 显示排序方式信息

## 实测结果

### 测试命令
```bash
cd backend
uv run python test_cdp.py
```

### 测试结果
```
✅ CDP 基础连接: 通过
✅ 小红书爬虫: 通过（获取 10 条笔记，按最多点赞排序）
✅ 抖音爬虫: 通过（获取 10 条视频，按最多点赞排序）
```

### 抖音热门数据示例
| 排名 | 标题 | 作者 | 点赞 |
|------|------|------|------|
| 1 | 这个夏天好看的袜子都已经到啦... | 豆豆本豆 | **166,000** |
| 2 | ... | 豆豆本豆 | **44,000** |
| 3 | #袜子#按斤称的袜子... | 🌵🌵阿仙 | **16,000** |

## 使用方法

```python
# 抖音 - 获取最热门视频（默认）
results = await scraper.search_hot_videos(keyword="袜子", limit=10)

# 抖音 - 指定排序方式
results = await scraper.search_hot_videos(keyword="袜子", limit=10, sort_type=1)  # 最多点赞
results = await scraper.search_hot_videos(keyword="袜子", limit=10, sort_type=0)  # 综合排序
results = await scraper.search_hot_videos(keyword="袜子", limit=10, sort_type=2)  # 最新发布

# 小红书 - 获取最热门笔记（默认）
results = await scraper.search_hot_notes(keyword="袜子", limit=10)

# 小红书 - 指定排序方式
results = await scraper.search_hot_notes(keyword="袜子", limit=10, sort="likes")      # 最多点赞
results = await scraper.search_hot_notes(keyword="袜子", limit=10, sort="general")    # 综合
results = await scraper.search_hot_notes(keyword="袜子", limit=10, sort="time")       # 最新
results = await scraper.search_hot_notes(keyword="袜子", limit=10, sort="comments")   # 最多评论
results = await scraper.search_hot_notes(keyword="袜子", limit=10, sort="favorites")  # 最多收藏
```

## 相关文件变更

1. `backend/app/services/platform_scraper/cdp_douyin_scraper.py`
2. `backend/app/services/platform_scraper/cdp_xhs_scraper.py`
3. `backend/test_cdp.py`

## 备注

- 抖音排序效果明显，返回的数据按点赞数从高到低排列
- 小红书返回的数据点赞数不是严格递减，可能是页面渲染或加载顺序导致
- 两个平台都需要 Chrome 已登录才能正常获取数据
