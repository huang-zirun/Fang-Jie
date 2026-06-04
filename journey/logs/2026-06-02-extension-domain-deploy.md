# 浏览器扩展支持域名部署（trades.zzy88.com）

> 日期: 2026-06-02
> 状态: DONE

## 背景

项目将部署到 `https://trades.zzy88.com`。用户安装浏览器扩展后通过域名访问网页，需要验证扩展能否正常工作。

## 问题分析

扩展在域名部署下存在关键障碍：

| 组件 | 问题 | 影响 |
|------|------|------|
| **content_scripts matches** | 只匹配 `localhost` / `127.0.0.1` | content.js 不会注入，前端与扩展通信完全中断 |
| **前端扩展检测** | 依赖 content script 响应 PING | 检测始终失败，显示"未检测到扩展" |
| **自动配置** | 依赖 content script 传递 serverUrl/token | 扩展 background 无法自动获取后端地址和认证信息 |
| **一键获取 Cookie** | 依赖 content script 桥接 | 按钮点击无响应 |

**仍能工作的功能**（需手动配置）：
- popup 手动获取/同步 Cookie
- background `chrome.cookies.onChanged` 自动监听（配置正确后）

**无关功能**：
- CDP 二维码登录连接的是服务器本机 Chrome，与用户本地扩展无关

## 变更内容

### 1. extension/manifest.json

content_scripts matches 加入部署域名：

```json
"content_scripts": [
  {
    "matches": [
      "http://localhost:*/*",
      "http://127.0.0.1:*/*",
      "https://trades.zzy88.com/*"
    ],
    "js": ["content.js"]
  }
]
```

### 2. 其他组件适配状态

| 组件 | 状态 | 说明 |
|------|------|------|
| 后端 CORS | ✅ 已适配 | `allow_origins=["*"]`，扩展 background fetch 不受限 |
| 前端 API 基地址 | ✅ 已适配 | 使用相对路径 `/api/v1`，域名下自动指向正确地址 |
| 后端 `/accounts/{platform}/extension` | ✅ 已存在 | 接收扩展 Cookie，无需修改 |

## 部署后操作

1. 重新打包/加载扩展（manifest 变更需刷新扩展）
2. 确认 trades.zzy88.com 启用 HTTPS
3. 扩展 popup 中 serverUrl 应自动由前端配置为 `https://trades.zzy88.com`

## 扩展生效检查清单

- [ ] 访问 `https://trades.zzy88.com`，页面显示"扩展已连接"
- [ ] 点击"获取 Cookie"，扩展 popup 或 background 成功获取并同步
- [ ] 访问小红书/抖音登录后，background 自动触发 Cookie 同步
- [ ] 后端 `/api/v1/accounts/` 列表中显示已绑定的平台账号
