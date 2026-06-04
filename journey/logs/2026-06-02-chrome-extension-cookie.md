# Chrome Extension 同浏览器 Cookie 获取方案

> 日期: 2026-06-02
> 状态: DONE

## 背景

用户希望在前端页面打开的同一浏览器中直接获取小红书 Cookie，无需额外启动 Chrome 或配置 CDP 调试端口。核心障碍是同源策略：前端 JS 无法读取 `xiaohongshu.com` 的 Cookie，尤其是 httpOnly 的 `web_session`。

## 方案调研

对比了 5 种方案：

| 方案 | httpOnly | 用户体验 | 云兼容 | 总评 |
|------|---------|---------|--------|------|
| **A: Chrome Extension** | ✅ | ⭐⭐⭐⭐ | ✅ | **最佳** |
| B: CDP 增强 | ✅ | ⭐⭐ | ❌ | 现有方案优化 |
| C: 反向代理 | ⚠️ | ⭐⭐⭐ | ⚠️ | 安全风险高 |
| D: Bookmarklet | ❌ | ⭐⭐ | ✅ | 无法读 httpOnly |
| E: iframe | ❌ | ⭐⭐⭐ | ✅ | XHS 禁止嵌入 |

选定方案 A：Chrome Extension。

## 实施内容

### 1. Chrome Extension（`intent-money/extension/`）

- `manifest.json` — Manifest V3，声明 cookies/tabs/storage 权限
- `background.js` — Service Worker：Cookie 读取、onChanged 自动同步、与后端通信
- `content.js` — Content Script：桥接前端页面与扩展的 postMessage 通信
- `popup/` — Popup UI：显示登录状态、一键获取/同步 Cookie

### 2. 后端新增端点

- `POST /accounts/{platform}/extension` — 接收扩展发送的 Cookie
- Chrome Cookie 格式 → Playwright `storage_state` 格式转换
- 复用 CookieVault 加密存储，`bind_method = "extension"`

### 3. 前端集成

- 扩展安装检测（PING/PONG 心跳）
- 扩展已安装：显示"扩展已连接"，"扫码登录"变为"一键登录"
- 扩展未安装：显示安装引导，保留 CDP/Playwright 降级
- 登录优先级：Extension → CDP → Playwright

## 安装方式

1. 打开 Chrome，访问 `chrome://extensions`
2. 开启右上角「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `intent-money/extension/` 目录
5. 扩展图标出现在浏览器工具栏，点击可查看状态

## 验证结果

- 后端 `accounts.py` 导入正常，`ExtensionCookieRequest` schema 正确
- 前端 `vue-tsc --noEmit` 类型检查通过
- 12/13 checklist 通过，Cookie 自动续期需手动测试验证
