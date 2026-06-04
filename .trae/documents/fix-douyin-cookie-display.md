# 修复抖音 Cookie 显示问题

## 问题描述

浏览器扩展已成功获取抖音 Cookie（popup 显示"已登录"，23 个 Cookie），但前端账号管理页面没有显示"浏览器已登录"徽章。

## 根本原因分析

**平台键名映射不一致**：

1. **扩展层** (`background.js`) 使用平台名称：`xiaohongshu`, `douyin`
2. **前端层** (`AccountManage.vue`) 使用平台键名：`xhs`, `douyin`

当扩展通过 `STATUS_UPDATE` 消息广播状态时，发送的是 `"xiaohongshu"`，但前端存储和查找时使用的是 `"xhs"`，导致数据无法正确关联。

### 代码追踪

**扩展发送状态 (background.js:50-71)**:
```javascript
await chrome.tabs.sendMessage(tab.id, {
  action: "STATUS_UPDATE",
  platform: "xiaohongshu",  // 扩展内部名称
  loggedIn: true,
  cookieCount: 23
});
```

**前端接收状态 (AccountManage.vue:264-275)**:
```javascript
const platform = event.data.platform  // "xiaohongshu"
extensionStatus[platform] = { loggedIn: true, ... }  // 存储到 extensionStatus["xiaohongshu"]
```

**前端显示判断 (AccountManage.vue:31)**:
```vue
<span v-if="extensionStatus[platform.key]?.loggedIn">  // platform.key = "xhs"
```

由于 `extensionStatus["xhs"]` 不存在，徽章不显示。

## 修复方案

### 方案：统一平台键名映射

在 `AccountManage.vue` 的 `onGlobalMessage` 函数中添加平台名称到键名的映射转换。

**修改文件**: `frontend/src/views/AccountManage.vue`

```typescript
function onGlobalMessage(event: MessageEvent) {
  if (event.data?.type === 'INTENT_MONEY_STATUS_UPDATE') {
    const platform = event.data.platform
    if (platform) {
      // 映射扩展平台名称到前端平台键名
      const platformKeyMap: Record<string, string> = {
        xiaohongshu: 'xhs',
        douyin: 'douyin'
      }
      const platformKey = platformKeyMap[platform] || platform
      extensionStatus[platformKey] = {
        loggedIn: !!event.data.loggedIn,
        cookieCount: event.data.cookieCount || 0,
        timestamp: event.data.timestamp || Date.now(),
      }
    }
  }
}
```

## 验证步骤

1. 安装浏览器扩展
2. 登录抖音网站 (douyin.com)
3. 打开扩展 popup，确认显示"已登录"
4. 打开前端账号管理页面
5. 验证抖音卡片显示"浏览器已登录"徽章

## 影响范围

- 仅影响前端状态显示，不影响 Cookie 获取和同步功能
- 小红书平台同样受益（之前也存在相同问题）
