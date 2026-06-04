# Cookie 验证链路三重 Bug 修复

> 日期: 2026-06-03
> 状态: DONE

## 现象

浏览器扩展已安装，小红书 cookie 已登录，点击"获取Cookie并同步"后显示"浏览器已登录"，但点击"验证"显示"cookie已过期"。

## 根因

全链路审查发现 3 个叠加 Bug：

### Bug 1（核心）：Cookie `sameSite` 字段转换错误

`accounts.py` 中将 Chrome 扩展 API 返回的 `sameSite` 值用 `.capitalize()` 转换，但两套 API 的值域完全不同：

| Chrome 扩展 API | `.capitalize()` 结果 | Playwright 期望 |
|---|---|---|
| `"no_restriction"` | `"No_restriction"` | `"None"` |
| `"lax"` | `"Lax"` | `"Lax"` |
| `"strict"` | `"Strict"` | `"Strict"` |
| `"unspecified"` | `"Unspecified"` | 省略或 `"None"` |

小红书 `web_session` cookie 通常为 `SameSite=None; Secure`，Chrome API 返回 `"no_restriction"`，经 `.capitalize()` 变成 `"No_restriction"`，Playwright 不认识此值，导致 cookie 加载失败，验证必然返回"过期"。

### Bug 2：Cookie `expires` 字段名不匹配

Chrome 扩展 API 返回 `expirationDate`（Unix 时间戳秒），后端代码读 `expires`，永远拿到 `-1`，所有 cookie 变成 session cookie。

### Bug 3：平台名称不匹配 + 错误吞掉

扩展用 `"xiaohongshu"`，后端 `VALID_PLATFORMS` 只有 `"xhs"`，请求被 400 拒绝。同时 `syncCookiesToBackend` 函数吞掉所有错误（仅 `console.error`），弹窗显示"同步成功"但后端从未收到 cookie。

## 修复

### accounts.py

1. 新增 `_SAME_SITE_MAP` 映射表，正确转换 sameSite 值
2. `c.get("expires", -1)` → `c.get("expirationDate", -1)`
3. 新增 `_PLATFORM_ALIASES` 和 `_normalize_platform()`，所有 7 个端点入口统一调用，后端同时接受 `"xiaohongshu"` 和 `"xhs"`

### background.js

1. `syncCookiesToBackend` 不再吞错误，改为 `throw new Error()`
2. `SYNC_COOKIES` handler 捕获同步异常后返回 `success: false`

## 设计决策

- **平台别名在后端处理**而非改扩展：扩展 `PLATFORM_CONFIG` 的 key 是内部标识符，改它影响面大（所有 handler、popup、content script 都引用），在后端做别名映射更安全
- **`sameSite` 默认值选 `"None"`**：Chrome API 返回 `"unspecified"` 的 cookie 大多是跨站 cookie，Playwright 中 `SameSite=None` 是最宽松的默认值，不会导致 cookie 被拒绝
