# 扩展Cookie同步验证误判问题修复 Spec

## Why

用户在浏览器中正常登录了小红书，使用扩展获取Cookie并同步到后端时，后端验证失败返回400错误，导致Cookie无法保存。验证器使用Playwright headless浏览器访问小红书创作者中心，判断Cookie无效，但实际上用户在浏览器中是登录状态。这是一个**验证器误判**问题——将有效的Cookie误判为无效。

## What Changes

- **BREAKING** 修改后端`extension_cookie_login`逻辑，对于扩展发送的Cookie，采用"先保存后验证"策略，而非"先验证后保存"
- 增加验证器可靠性改进：增加超时时间、改进stealth脚本、尝试多个验证端点
- 增加验证失败时的降级处理：如果验证失败但仍保存Cookie，标记为"pending"状态，后台异步重试验证

## Impact

- Affected specs: fix-extension-detection-sync, fix-cookie-domain-mismatch, fix-xhs-login-false-positive
- Affected code:
  - `backend/app/api/v1/accounts.py` — `extension_cookie_login`函数，修改验证逻辑
  - `backend/app/services/xhs_cookie_validator.py` — 改进验证可靠性
  - `backend/app/services/douyin_cookie_validator.py` — 改进验证可靠性
  - `backend/app/services/cookie_lifecycle.py` — 增加异步验证任务

## 根因分析

### 根因 1：后端在保存Cookie前强制验证

**位置**：`accounts.py` 第 162-164 行

```python
is_valid = await _validate_cookie(platform, storage_state_json)
if not is_valid:
    raise HTTPException(status_code=400, detail="Cookie 无效或已过期，请重新获取")
```

**问题**：
1. 如果验证失败，函数直接抛出异常，Cookie不会被保存
2. 即使用户在浏览器中正常登录，Cookie实际上是有效的，也可能因为验证器的问题而被误判为无效
3. 用户无法使用扩展获取的Cookie

**用户场景**：
1. 用户在浏览器中访问小红书并登录
2. 用户打开扩展popup，点击"获取Cookie并同步"
3. 扩展获取Cookie并发送到后端
4. 后端验证失败（可能因为反爬虫、网络、Cookie domain等问题）
5. 返回400错误，Cookie未保存
6. 用户看到"同步失败: Sync failed with status 400"

### 根因 2：验证器可能不可靠

**位置**：`xhs_cookie_validator.py`

**问题**：
1. 使用Playwright headless浏览器验证
2. 小红书有强反爬虫机制，可能检测到自动化特征
3. 验证器访问`https://creator.xiaohongshu.com/publish/publish`，可能被重定向到登录页
4. 即使Cookie有效，也可能因为反爬虫而被误判为无效

**验证流程**：
1. 启动Playwright headless浏览器
2. 注入stealth脚本（但可能不够完善）
3. 加载Cookie
4. 访问创作者中心发布页
5. 检查是否被重定向到登录页
6. 如果重定向，判定Cookie无效

**可能的误判原因**：
- 小红书检测到headless浏览器特征
- 小红书检测到自动化行为
- 网络问题导致页面加载失败
- Cookie domain问题（虽然已修复，但可能还有其他问题）
- 验证器超时设置过短

### 根因 3：状态更新逻辑问题

**位置**：`accounts.py` 第 231-233 行

```python
if is_valid:
    account.cookie_status = "active"
else:
    account.cookie_status = "expired"
```

**问题**：
- 在`validate_account`端点中，如果验证失败，会将状态标记为"expired"
- 用户可能在某个时候点击了"验证"按钮，验证失败，状态变成"过期"
- 即使后来Cookie实际上是有效的，状态也不会自动恢复

## ADDED Requirements

### Requirement: 扩展Cookie先保存后验证

系统 SHALL 对扩展发送的Cookie采用"先保存后验证"策略，而非"先验证后保存"。

#### Scenario: 扩展发送有效Cookie，验证成功
- **WHEN** 扩展发送Cookie到`/accounts/{platform}/extension`
- **AND** Cookie实际上是有效的
- **AND** 验证器验证成功
- **THEN** 后端保存Cookie，状态为"active"
- **AND** 返回成功响应

#### Scenario: 扩展发送有效Cookie，验证失败（误判）
- **WHEN** 扩展发送Cookie到`/accounts/{platform}/extension`
- **AND** Cookie实际上是有效的
- **BUT** 验证器验证失败（误判）
- **THEN** 后端仍然保存Cookie，状态为"pending"
- **AND** 返回成功响应，但包含警告信息"验证未通过，已保存Cookie，将在后台重试验证"
- **AND** 后台异步任务在5分钟后重新验证

#### Scenario: 扩展发送无效Cookie
- **WHEN** 扩展发送Cookie到`/accounts/{platform}/extension`
- **AND** Cookie确实是无效的（用户未登录或已退出）
- **THEN** 后端保存Cookie，状态为"pending"
- **AND** 后台验证失败后，状态更新为"expired"

### Requirement: 验证器可靠性改进

系统 SHALL 改进验证器的可靠性，减少误判。

#### Scenario: 增加验证超时时间
- **WHEN** 验证器访问小红书创作者中心
- **THEN** 页面加载超时时间从15秒增加到30秒
- **AND** 等待时间从3秒增加到5秒

#### Scenario: 改进stealth脚本
- **WHEN** 验证器启动浏览器
- **THEN** 注入更完善的stealth脚本
- **AND** 设置更多反检测参数

#### Scenario: 尝试多个验证端点
- **WHEN** 验证器验证小红书Cookie
- **THEN** 首先尝试访问创作者中心
- **AND** 如果失败，尝试访问个人主页
- **AND** 如果都失败，才判定为无效

### Requirement: 后台异步验证

系统 SHALL 提供后台异步验证任务，对标记为"pending"的Cookie进行重试验证。

#### Scenario: 后台验证任务
- **WHEN** 系统启动时
- **THEN** 启动后台任务，每5分钟检查一次"pending"状态的Cookie
- **AND** 对每个Cookie进行验证
- **AND** 验证成功后更新状态为"active"
- **AND** 验证失败后更新状态为"expired"

#### Scenario: 验证重试次数限制
- **WHEN** Cookie状态为"pending"
- **AND** 已经重试验证3次仍然失败
- **THEN** 状态更新为"expired"
- **AND** 不再重试

## MODIFIED Requirements

### Requirement: extension_cookie_login验证逻辑

修改`accounts.py`的`extension_cookie_login`函数：

1. 接收Cookie后，先进行基本格式检查（不进行浏览器验证）
2. 保存Cookie到数据库，状态设为"pending"
3. 启动后台验证任务（或立即验证，但不阻塞响应）
4. 返回成功响应，包含验证状态信息

### Requirement: xhs_cookie_validator验证器

修改`xhs_cookie_validator.py`：

1. 增加页面加载超时时间到30秒
2. 增加等待时间到5秒
3. 改进stealth脚本注入
4. 增加多个验证端点尝试
5. 增加更详细的日志记录

### Requirement: 前端状态显示

修改`AccountManage.vue`：

1. 对于"pending"状态的Cookie，显示"待验证"
2. 提供"立即验证"按钮，触发手动验证
3. 验证失败时，显示"验证失败，但Cookie已保存，可尝试使用"

## REMOVED Requirements

### Requirement: 保存前强制验证

**Reason**: 验证器可能误判，导致有效的Cookie无法保存。应改为先保存后验证。
**Migration**: 修改`extension_cookie_login`，移除保存前的验证检查，改为保存后异步验证。
