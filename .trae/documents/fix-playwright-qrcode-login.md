# 修复扫码登录 Playwright 浏览器未安装问题

## 问题描述

点击"扫码登录"按钮时，前端报错：
> 启动登录失败: BrowserType.launch: Executable doesn't exist at C:\Users\Admin\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe

## 根本原因

1. `backend/app/services/qrcode_login.py` 第 56 行调用 `pw.chromium.launch(headless=True)` 启动 Playwright 浏览器
2. `pyproject.toml` 中已声明 `playwright` 依赖，Python 包已安装
3. **但 Playwright 的浏览器二进制文件（Chromium）未安装**，这是两个独立的步骤：
   - `uv add playwright` → 安装 Python 包
   - `playwright install chromium` → 下载浏览器二进制（约 100MB+）
4. Windows 环境下，浏览器默认下载到 `%LOCALAPPDATA%\ms-playwright\` 目录

## 修复步骤

### 步骤 1：安装 Playwright Chromium 浏览器

在 PowerShell 中执行：

```powershell
cd e:\系统文件夹\Desktop\Channing\Fang-Jie\intent-money\backend
uv run playwright install chromium
```

验证安装：
```powershell
Test-Path "$env:LOCALAPPDATA\ms-playwright\chromium-*/chrome-win/chrome.exe"
```

### 步骤 2：增强错误提示（代码改进）

修改 `backend/app/services/qrcode_login.py`，在启动失败时给出更明确的安装指引，而非原始堆栈：

- 第 95-99 行的异常捕获中，判断错误消息是否包含 "Executable doesn't exist"
- 若是，返回友好错误：`"Playwright 浏览器未安装，请在 backend 目录下运行: uv run playwright install chromium"`
- 保留其他异常的原样返回

### 步骤 3：验证扫码登录功能

1. 启动后端服务：`uv run uvicorn app.main:app --host 127.0.0.1 --port 9090`
2. 启动前端：`npm run dev`
3. 进入"账号管理"页面
4. 点击"扫码登录"按钮
5. 预期：正常弹出二维码图片，不再报错

### 步骤 4：更新 journey 日志

创建 `journey/logs/2026-06-01-fix-playwright-qrcode-login.md`，记录：
- 问题现象
- 根因分析
- 修复命令
- 代码改进点

## 影响范围

- 仅影响 Windows 开发环境（生产环境 Docker 构建时需确保 `playwright install` 在 Dockerfile 中执行）
- 不影响 Cookie 手动导入功能
- 不影响 CDP 模式的数据抓取

## 风险

- 无风险。浏览器安装是本地环境配置操作，不修改业务逻辑。
