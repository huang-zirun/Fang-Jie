# 小红书扫码登录验证过期问题根因分析与修复计划

## 问题描述

用户场景：
1. 在浏览器中已登录小红书，状态正常
2. 在意图变现系统点击扫码登录，显示"已经登录"
3. 点击验证按钮，显示"验证过期"

## 根因分析

### 当前验证方式（错误）

[accounts.py:224-255](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/api/v1/accounts.py#L224-L255) 使用 httpx 直接发送 HTTP 请求：

```python
resp = await client.get(
    "https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo",
    headers=headers,
)
return data.get("success", False)
```

### 问题根源

**小红书 API 需要动态签名，httpx 无法生成签名！**

1. **签名机制**：小红书 API 需要 `x-s` 和 `x-t` 请求头，这些是由 JavaScript 函数 `window._webmsxyw()` 动态生成的
2. **httpx 无法执行 JavaScript**：直接发送 HTTP 请求无法生成签名
3. **缺少 stealth 脚本**：小红书检测到请求来自自动化工具，返回失败

### 证据

在 [xhs_uploader/main.py:15-43](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/social-auto-upload/uploader/xhs_uploader/main.py#L15-L43) 中，social-auto-upload 项目明确展示了签名机制：

```python
def sign_local(uri, data=None, a1="", web_session=""):
    # 启动浏览器执行 JavaScript 生成签名
    encrypt_params = context_page.evaluate(
        "([url, data]) => window._webmsxyw(url, data)", 
        [uri, data]
    )
    return {
        "x-s": encrypt_params["X-s"],
        "x-t": str(encrypt_params["X-t"])
    }
```

### 正确的验证方式

在 [xiaohongshu_uploader/main.py:148-183](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/social-auto-upload/uploader/xiaohongshu_uploader/main.py#L148-L183) 中，social-auto-upload 使用浏览器验证：

```python
async def cookie_auth(account_file):
    # 1. 启动浏览器
    browser = await playwright.chromium.launch(headless=True, channel="chrome")
    # 2. 加载 cookie（storage_state）
    context = await browser.new_context(storage_state=account_file)
    # 3. 注入 stealth 脚本隐藏自动化特征
    context = await set_init_script(context)
    # 4. 访问实际页面
    page = await context.new_page()
    await page.goto(XHS_PUBLISH_VIDEO_URL)
    # 5. 检查是否被重定向到登录页
    if page.url.startswith(XHS_LOGIN_URL):
        return False
    return True
```

## 解决方案

### 方案：使用 Playwright 浏览器验证 Cookie

**核心思路**：不直接调用 API，而是用浏览器访问页面，检查是否被重定向到登录页。

### 实现步骤

#### Step 1: 创建 Cookie 验证服务

创建 `backend/app/services/xhs_cookie_validator.py`，实现基于浏览器的 Cookie 验证：

```python
async def validate_xhs_cookie_via_browser(cookie_str: str) -> bool:
    """
    使用 Playwright 浏览器验证小红书 Cookie
    
    流程：
    1. 启动浏览器，注入 stealth 脚本
    2. 设置 Cookie
    3. 访问小红书创作者中心
    4. 检查是否被重定向到登录页
    """
    from playwright.async_api import async_playwright
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            channel="chrome",
        )
        context = await browser.new_context()
        
        # 注入 stealth 脚本
        stealth_js = Path("utils/stealth.min.js")
        await context.add_init_script(path=stealth_js)
        
        # 解析并设置 Cookie
        cookies = parse_cookie_string(cookie_str)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/publish/publish")
        await page.wait_for_timeout(3000)
        
        # 检查是否被重定向到登录页
        if page.url.startswith("https://creator.xiaohongshu.com/login"):
            return False
        
        return True
```

#### Step 2: 修改验证 API

修改 `backend/app/api/v1/accounts.py` 的 `_validate_cookie()` 函数：

```python
async def _validate_cookie(platform: str, cookie_data: str) -> bool:
    if platform == "xhs":
        from app.services.xhs_cookie_validator import validate_xhs_cookie_via_browser
        return await validate_xhs_cookie_via_browser(cookie_data)
    # ... 其他平台
```

#### Step 3: 同步修改 cookie_lifecycle.py

修改 `backend/app/services/cookie_lifecycle.py` 的 `_check_platform_login()` 函数，使用相同的浏览器验证方式。

#### Step 4: 添加 stealth.min.js

将 `social-auto-upload/utils/stealth.min.js` 复制到 `backend/utils/` 目录。

#### Step 5: 修改 Cookie 存储格式

当前 Cookie 存储为字符串格式，需要改为 Playwright 的 `storage_state` 格式（JSON），包含：
- cookies: 数组，每个包含 name, value, domain, path 等
- origins: localStorage 数据

## 文件变更

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/services/xhs_cookie_validator.py` | 新增 | 浏览器验证服务 |
| `backend/app/api/v1/accounts.py` | 修改 | 使用浏览器验证 |
| `backend/app/services/cookie_lifecycle.py` | 修改 | 使用浏览器验证 |
| `backend/app/services/qrcode_login.py` | 修改 | 保存 storage_state 格式 |
| `backend/utils/stealth.min.js` | 新增 | 隐藏自动化特征脚本 |

## 风险评估

### 性能影响

- 浏览器验证比 HTTP 请求慢（约 5-10 秒）
- 解决方案：验证是异步操作，用户可接受短暂等待

### 资源消耗

- 每次验证需要启动浏览器实例
- 解决方案：考虑使用浏览器池或复用实例

## 验证方式

1. 启动后端服务
2. 进入账号管理页面
3. 点击小红书"扫码登录"
4. 使用小红书 APP 扫码
5. 登录成功后点击"验证"
6. 预期：显示"Cookie有效"
