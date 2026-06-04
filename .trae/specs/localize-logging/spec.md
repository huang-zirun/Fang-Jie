# 日志系统中文化 Spec

## Why
当前后端日志消息全部使用英文，且部分消息冗长啰嗦，不便于中文团队快速定位问题。需要将日志消息改为简洁中文。

## What Changes
- 将 22 个文件中约 162 条英文日志消息改为简洁中文
- 精简冗余描述，保留关键信息（模块名、参数值、错误原因）
- 已有中文的日志（xhs_cookie_validator、douyin_cookie_validator、accounts.py）保持不变，仅精简过长消息

## Impact
- Affected code: `intent-money/backend/app/` 下所有使用 `logger` 的 22 个文件
- 无破坏性变更，仅修改日志文本内容

## ADDED Requirements

### Requirement: 日志消息中文化
系统 SHALL 将所有英文日志消息替换为简洁中文，遵循以下原则：
- 每条日志消息不超过 20 个汉字（不含动态参数）
- 去除冗余修饰词（如 "successfully"、"failed to" 等），用简洁动词替代
- 保留关键上下文信息（模块名、关键词、用户ID、错误详情等）

#### Scenario: AI 服务日志
- **WHEN** AI 服务产生日志
- **THEN** 日志消息使用中文，如 "AI密钥未配置，使用降级方案"、"AI超时(第N次)"、"AI请求失败: {e}"

#### Scenario: 定时任务日志
- **WHEN** 后台定时任务产生日志
- **THEN** 日志消息使用中文，如 "每日市场分析已取消"、"后台任务已全部启动"

#### Scenario: 爬虫服务日志
- **WHEN** 爬虫服务产生日志
- **THEN** 日志消息使用中文，如 "抖音搜索HTTP错误: {status}"、"XHS笔记详情请求异常: {e}"

#### Scenario: Cookie 服务日志
- **WHEN** Cookie 相关服务产生日志
- **THEN** 日志消息使用中文，如 "Cookie已过期: {platform}"、"Cookie已标记过期: {platform}_{user_id}"

### Requirement: 日志消息精简
系统 SHALL 精简日志消息长度，遵循以下映射风格：

| 英文原文风格 | 中文精简风格 |
|---|---|
| `Failed to save XHS note: {e}` | `保存小红书笔记失败: {e}` |
| `AI_API_KEY not set, using fallback` | `AI密钥未配置，使用降级方案` |
| `daily_market_analysis cancelled, exiting` | `每日市场分析已取消` |
| `All AI attempts failed, using smart fallback` | `AI全部重试失败，使用降级方案` |
| `Starting AI generation attempt {n}/2` | `AI生成第{n}次尝试` |
| `Backend scraper returned 0 videos for '{keyword}' - extension scrape may have better results` | `后端爬虫未获取到'{keyword}'视频` |
| `No extension-scraped data found. Consider triggering scrape via browser extension.` | `无扩展抓取数据，可通过浏览器扩展触发` |
