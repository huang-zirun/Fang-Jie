# 修复扫码登录 Playwright 浏览器未安装问题

## 问题现象

点击"扫码登录"按钮时，前端报错：
> 启动登录失败: BrowserType.launch: Executable doesn't exist at C:\Users\Admin\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe

## 根因分析

1. `backend/app/services/qrcode_login.py` 第 56 行调用 `pw.chromium.launch(headless=True)` 启动 Playwright 浏览器
2. `pyproject.toml` 中已声明 `playwright` 依赖，Python 包已安装
3. **但 Playwright 的浏览器二进制文件（Chromium）未安装**，这是两个独立的步骤：
   - `uv add playwright` → 安装 Python 包
   - `playwright install chromium` → 下载浏览器二进制（约 181MB）
4. Windows 环境下，浏览器默认下载到 `%LOCALAPPDATA%\ms-playwright\` 目录

## 修复方案

### 方案 A：使用系统已安装的 Chrome（最终采用 ✅）

Playwright 支持通过 `channel="chrome"` 直接使用系统已安装的 Google Chrome，无需下载 Chromium。

修改 `backend/app/services/qrcode_login.py` 第 56 行：
```python
browser = await pw.chromium.launch(
    headless=True,
    channel="chrome",  # 新增：使用系统 Chrome
    args=["--disable-blink-features=AutomationControlled"],
)
```

验证结果：✅ `Chrome launched OK`

### 方案 B：下载 Playwright Chromium（未采用 ❌）

```powershell
uv run playwright install chromium
```

未采用原因：官方 CDN 在国内速度极慢（约 1-2 小时），国内镜像（npmmirror、azureedge）均返回 404/400，无可用镜像源。

### 代码改进（异常提示增强）

修改 `qrcode_login.py` 异常捕获块，当检测到浏览器未安装时返回友好提示：
```python
if "Executable doesn't exist" in error_msg:
    return {
        "success": False,
        "error": "Playwright 浏览器未安装，请在 backend 目录下运行: uv run playwright install chromium",
    }
```

## 影响范围

- Windows 开发环境：直接使用系统 Chrome，无需额外安装
- 生产环境 Docker：如系统无 Chrome，仍需在 Dockerfile 中执行 `playwright install chromium`
- 不影响 Cookie 手动导入功能
- 不影响 CDP 模式的数据抓取

## 验证方式

1. 启动后端：`uv run uvicorn app.main:app --host 127.0.0.1 --port 9090`
2. 启动前端：`npm run dev`
3. 进入"账号管理"页面
4. 点击"扫码登录"按钮
5. 预期：正常弹出二维码图片，不再报错

## 教训

1. Playwright 的 Python 包安装 ≠ 浏览器二进制安装。这是两个独立步骤，文档中有明确说明但容易被忽略。
2. 在 Windows 开发环境且用户已安装 Chrome 的情况下，优先使用 `channel="chrome"` 直接使用系统浏览器，避免下载 181MB 的 Chromium。
3. 国内网络环境下，Playwright 浏览器下载镜像不完善，应避免依赖在线下载。
