# CDP 爬虫热门排序修改计划

## 目标
修改 CDP 爬虫支持按热门/点赞数排序抓取数据，让用户可以获取最热门的内容。

## 背景分析

### 当前实现
- **抖音爬虫**: `DOUYIN_SEARCH_URL = "https://www.douyin.com/search/{keyword}?type=video"`
- **小红书爬虫**: `XHS_SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes&type=51"`
- 两者都使用默认排序（综合推荐），没有按热度排序

### 平台排序参数（根据用户截图确认）

**抖音** 支持 `sort_type` 参数：
- `sort_type=0` - 综合排序
- `sort_type=1` - **最多点赞**（最热）
- `sort_type=2` - 最新发布

**小红书** 支持 `sort` 参数：
- `sort=general` - 综合（默认）
- `sort=time` - 最新
- `sort=likes` - **最多点赞**
- `sort=comments` - 最多评论
- `sort=favorites` - 最多收藏

## 实施步骤

### 1. 修改抖音爬虫 [cdp_douyin_scraper.py]
**文件**: `backend/app/services/platform_scraper/cdp_douyin_scraper.py`

**修改内容**:
```python
# 修改 URL 模板，添加 sort_type 参数
DOUYIN_SEARCH_URL = "https://www.douyin.com/search/{keyword}?type=video&sort_type={sort_type}"

# 修改 search_hot_videos 方法签名，添加 sort_type 参数，默认最多点赞(1)
async def search_hot_videos(self, keyword: str, limit: int = 20, sort_type: int = 1) -> list[dict[str, Any]]:
    """
    sort_type: 0=综合排序, 1=最多点赞(默认), 2=最新发布
    """
    url = DOUYIN_SEARCH_URL.format(keyword=keyword, sort_type=sort_type)
    # ... 其余代码不变
```

### 2. 修改小红书爬虫 [cdp_xhs_scraper.py]
**文件**: `backend/app/services/platform_scraper/cdp_xhs_scraper.py`

**修改内容**:
```python
# 添加排序参数
XHS_SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes&type=51&sort={sort}"

# 修改 search_hot_notes 方法签名
async def search_hot_notes(self, keyword: str, limit: int = 20, sort: str = "likes") -> list[dict[str, Any]]:
    """
    sort: general=综合, time=最新, likes=最多点赞(默认), comments=最多评论, favorites=最多收藏
    """
    url = XHS_SEARCH_URL.format(keyword=keyword, sort=sort)
    # ... 其余代码不变
```

### 3. 修改测试文件 [test_cdp.py]
**文件**: `backend/test_cdp.py`

**修改内容**:
- 增加 `limit` 参数（默认 10 条）
- 显式传入 `sort_type=1` 和 `sort="likes"` 测试最热排序
- 添加排序结果验证（检查点赞数是否递减）

### 4. 运行测试验证
**命令**:
```bash
cd backend
uv run python test_cdp.py
```

**验证点**:
- [ ] 抖音爬虫能正常获取数据
- [ ] 数据按点赞数从高到低排列
- [ ] 小红书爬虫正常工作
- [ ] 无异常错误

## 预期结果
- 抖音：返回按点赞数排序的视频列表
- 小红书：返回按点赞数排序的笔记列表
