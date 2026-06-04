# 日志系统中文化

> 日期: 2026-06-04

## 背景

后端所有日志消息均为英文，且部分消息冗长啰嗦，不便于中文团队快速定位问题。

## 变更内容

将 `backend/app/` 下 22 个文件共 162 条英文日志消息替换为简洁中文。

### 改造原则

- 每条日志消息不超过 20 个汉字（不含动态参数）
- 去除冗余修饰词（如 "successfully"、"failed to"），用简洁动词替代
- 保留关键上下文信息（模块名、参数值、错误原因）
- 技术术语（Cookie、AI、URL、Playwright 等）保持英文原样

### 典型替换示例

| 英文原文 | 中文替换 |
|---|---|
| `AI_API_KEY not set, using fallback` | `AI密钥未配置，使用降级方案` |
| `All AI attempts failed, using smart fallback` | `AI全部重试失败，使用降级方案` |
| `daily_market_analysis cancelled, exiting` | `每日市场分析已取消` |
| `Failed to save XHS note: {e}` | `保存小红书笔记失败: {e}` |
| `Douyin search HTTP error: {status}` | `抖音搜索HTTP错误: {status}` |
| `Cookie decrypt error: {e}` | `Cookie解密失败: {e}` |
| `Backend scraper returned 0 videos for '{keyword}' - extension scrape may have better results` | `后端爬虫未获取到'{keyword}'视频` |

### 涉及文件

- `main.py` (28条)
- `ai_service.py` (12条)
- `market_service.py` (19条)
- `api/v1/market.py` (4条)
- `platform_scraper/douyin_scraper.py` (14条)
- `platform_scraper/xhs_scraper.py` (13条)
- `cookie_lifecycle.py` (4条)
- `cookie_manager.py` (3条)
- `cookie_vault.py` (1条)
- `diagnosis_service.py` (12条)
- `structure_extractor.py` (8条)
- `auto_publisher.py` (5条)
- `qrcode_login.py` (4条)
- `per_user_scraper.py` (4条)
- `snapshot_scheduler.py`、`task_service.py`、`task_cleanup.py`、`sentiment_service.py`、`evolution_service.py` (各1条)
- `xhs_cookie_validator.py`、`douyin_cookie_validator.py`、`accounts.py` — 已有中文，保持不变

## 结果

- 162 条日志全部中文化，验证扫描无英文遗漏
- 无破坏性变更，仅修改日志文本内容

## 补充：第三方库日志抑制

终端中仍有大量英文日志来自第三方库，非应用代码：

1. **SQLAlchemy Engine** — `echo=True` 导致打印每条 SQL 语句（BEGIN/SELECT/COMMIT 等），极其冗长
2. **Uvicorn Access** — 每个 HTTP 请求的访问日志（`GET /api/v1/platforms HTTP/1.1 200 OK`）
3. **seed.py** — `print("Seed data created successfully")`

修复措施：
- `database.py`: `echo=True` → `echo=False`，关闭 SQLAlchemy SQL 日志
- `main.py`: 添加 `logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)` 和 `logging.getLogger("uvicorn.access").setLevel(logging.WARNING)`，将第三方库日志级别设为 WARNING
- `seed.py`: `print("Seed data created successfully")` → `print("种子数据初始化完成")`
