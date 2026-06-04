# 小红书 Cookie 验证架构修复

## 问题现象

用户场景：
1. 在浏览器中已登录小红书，状态正常
2. 在意图变现系统点击扫码登录，显示"已经登录"
3. 点击验证按钮，显示"验证过期"

## 根因分析

### 原验证方式（错误）

`accounts.py` 使用 httpx 直接调用小红书 API：

```python
resp = await client.get(
    "https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo",
    headers=headers,
)
return data.get("success", False)
```

### 问题根源

**小红书 API 需要动态签名，httpx 无法生成签名！**

1. **签名机制**：小红书 API 需要 `x-s` 和 `x-t` 请求头，由 JavaScript 函数 `window._webmsxyw()` 动态生成
2. **httpx 无法执行 JavaScript**：直接发送 HTTP 请求无法生成签名
3. **缺少 stealth 脚本**：小红书检测到请求来自自动化工具，返回失败

### 证据

social-auto-upload 项目在 `xhs_uploader/main.py` 中展示了签名机制：

```python
def sign_local(uri, data=None, a1="", web_session=""):
    encrypt_params = context_page.evaluate(
        "([url, data]) => window._webmsxyw(url, data)", 
        [uri, data]
    )
    return {
        "x-s": encrypt_params["X-s"],
        "x-t": str(encrypt_params["X-t"])
    }
```

## 解决方案

**使用 Playwright 浏览器验证 Cookie**（与 social-auto-upload 项目一致）

核心思路：不直接调用 API，而是用浏览器访问页面，检查是否被重定向到登录页。

### 验证流程

1. 启动 Playwright 浏览器（headless 模式）
2. 注入 stealth.min.js 隐藏自动化特征
3. 设置 Cookie
4. 访问 `https://creator.xiaohongshu.com/publish/publish`
5. 检查是否被重定向到登录页 → Cookie 无效
6. 检查是否显示登录框 → Cookie 无效
7. 否则 → Cookie 有效

## 文件变更

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/services/xhs_cookie_validator.py` | 新增 | 浏览器验证服务，注入 stealth 脚本，访问创作者中心检查登录状态 |
| `backend/app/utils/stealth.min.js` | 新增 | 隐藏自动化特征的脚本（从 social-auto-upload 复制） |
| `backend/app/api/v1/accounts.py` | 修改 | 小红书使用浏览器验证而非 httpx |
| `backend/app/services/cookie_lifecycle.py` | 修改 | 小红书使用浏览器验证而非 httpx |
| `backend/app/services/qrcode_login.py` | 修改 | 注入 stealth 脚本隐藏自动化特征 |

## 关键代码

### xhs_cookie_validator.py

```python
async def validate_xhs_cookie_via_browser(cookie_str: str) -> bool:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context()
        
        # 注入 stealth 脚本
        if stealth_js_path.exists():
            await context.add_init_script(path=str(stealth_js_path))
        
        # 设置 Cookie
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/publish/publish")
        
        # 检查是否被重定向到登录页
        if page.url.startswith("https://creator.xiaohongshu.com/login"):
            return False
        
        return True
```

## 性能影响

- 浏览器验证比 HTTP 请求慢（约 5-10 秒）
- 验证是异步操作，用户可接受短暂等待
- 每次验证需要启动浏览器实例，未来可考虑浏览器池优化

## 教训

1. 小红书 API 有严格的反爬机制，需要动态签名，httpx 无法绕过
2. 浏览器自动化验证是最可靠的方式，虽然慢但准确
3. stealth.min.js 是隐藏自动化特征的关键，必须注入
4. social-auto-upload 项目已有成熟的实现，应优先参考而非重复造轮子

## 验证方式

1. 重启后端服务
2. 进入账号管理页面
3. 点击小红书"扫码登录"
4. 使用小红书 APP 扫码
5. 登录成功后点击"验证"
6. 预期：显示"Cookie有效"
