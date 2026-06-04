# Cookie 验证链路问题根因分析与修复计划

## 问题描述

浏览器扩展已安装，小红书 cookie 已登录，点击"获取Cookie并同步"后显示"浏览器已登录"，但点击"验证"显示"cookie已过期"。

## 根因分析

经过全链路代码审查，发现 **3 个相互叠加的 Bug**，其中前 2 个是导致"验证显示过期"的直接原因，第 3 个是导致扩展自动同步/弹窗同步静默失败的独立 Bug。

---

### Bug 1（核心）：Cookie `sameSite` 字段转换错误

**位置**: [accounts.py](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/api/v1/accounts.py#L109)

```python
"sameSite": c.get("sameSite", "Lax").capitalize(),
```

**问题**: Chrome 扩展 API (`chrome.cookies.getAll`) 返回的 `sameSite` 值与 Playwright `storage_state` 期望的值完全不同：

| Chrome 扩展 API 返回值 | `.capitalize()` 结果 | Playwright 期望值 |
|---|---|---|
| `"no_restriction"` | `"No_restriction"` | `"None"` |
| `"lax"` | `"Lax"` | `"Lax"` |
| `"strict"` | `"Strict"` | `"Strict"` |
| `"unspecified"` | `"Unspecified"` | 省略或 `"None"` |

小红书的 `web_session` cookie 通常设置为 `SameSite=None; Secure`，Chrome API 返回 `"no_restriction"`。经 `.capitalize()` 后变成 `"No_restriction"`，这是 Playwright 不认识的值。

**后果**: Playwright 在 `browser.new_context(storage_state=...)` 时遇到非法 `sameSite` 值，要么抛出异常（被外层 `except Exception` 捕获后返回 `False`），要么静默跳过该 cookie。无论哪种情况，`web_session` cookie 都无法正确加载，验证必然失败。

---

### Bug 2：Cookie `expires` 字段名不匹配

**位置**: [accounts.py](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/api/v1/accounts.py#L106)

```python
"expires": c.get("expires", -1),
```

**问题**: Chrome 扩展 API 返回的过期时间字段名是 `expirationDate`（Unix 时间戳，秒），不是 `expires`。因此 `c.get("expires", -1)` 永远返回 `-1`，所有 cookie 都变成了 Playwright 中的 session cookie。

**后果**: 虽然 session cookie 在 Playwright 中仍会被发送，但丢失了原始过期时间信息。如果 Playwright 对 `storage_state` 做严格校验（例如要求 `SameSite=None` 的 cookie 必须有 `Secure=true` 且有效 `expires`），这也可能导致 cookie 被拒绝。

---

### Bug 3：平台名称不匹配导致扩展同步静默失败

**位置**:
- 扩展: [background.js](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/extension/background.js#L2) — `PLATFORM_CONFIG` 的 key 是 `"xiaohongshu"`
- 后端: [accounts.py](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/api/v1/accounts.py#L20) — `VALID_PLATFORMS = {"douyin", "xhs"}`

**问题**: 扩展的自动同步（`chrome.cookies.onChanged`）和弹窗同步（`SYNC_COOKIES`）都使用 `"xiaohongshu"` 作为平台名，POST 到 `/api/v1/accounts/xiaohongshu/extension`。但后端 `VALID_PLATFORMS` 只有 `"xhs"`，所以请求被 400 拒绝。

同时，[syncCookiesToBackend](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/extension/background.js#L24) 函数内部吞掉了所有错误：

```javascript
async function syncCookiesToBackend(platform, cookies) {
  try {
    const response = await fetch(...);
    if (!response.ok) {
      console.error(`Intent Money: Sync failed with status ${response.status}`);
      // 仅 log，不抛出
    }
  } catch (err) {
    console.error("Intent Money: Sync error", err);
    // 仅 log，不抛出
  }
}
```

**后果**: 弹窗显示"同步成功"，扩展广播 `loggedIn: true`，前端显示"浏览器已登录"——但后端从未收到 cookie。用户完全不知道同步失败了。

> 注意：前端 AccountManage.vue 的"获取Cookie"按钮走的是另一条路径（`extensionLogin` -> `extensionCookieLogin`），它正确地将 `"xhs"` 发送给后端，所以这条路径不受 Bug 3 影响。但受 Bug 1 和 Bug 2 影响，验证仍会失败。

---

## 问题链路还原

以用户通过**前端页面**点击"获取Cookie"为例：

1. 前端发送 `INTENT_MONEY_GET_COOKIES`，扩展返回浏览器 cookie 数组
2. 前端调用 `POST /accounts/xhs/extension`（平台名正确，不受 Bug 3 影响）
3. 后端将 Chrome cookie 转换为 Playwright `storage_state`（**Bug 1 + Bug 2 导致转换错误**）
4. 后端调用 `_validate_cookie()` 启动 Playwright 验证
5. Playwright 加载 `storage_state` 时，`sameSite: "No_restriction"` 导致异常或 cookie 被跳过
6. `web_session` cookie 未正确加载，访问小红书时被重定向到登录页
7. 验证返回 `False`，后端返回 400 "Cookie 无效或已过期"
8. 前端显示错误 toast，但扩展已广播 `loggedIn: true`，所以仍显示"浏览器已登录"

如果用户通过**弹窗**点击"获取Cookie并同步"：

1. 弹窗发送 `SYNC_COOKIES`，扩展调用 `syncCookiesToBackend("xiaohongshu", cookies)`
2. POST `/accounts/xiaohongshu/extension` 返回 400（**Bug 3**）
3. `syncCookiesToBackend` 吞掉错误，弹窗显示"同步成功"
4. 扩展广播 `loggedIn: true`，前端显示"浏览器已登录"
5. 后端无账号记录，点击"验证"返回 404 "未绑定xhs账号"

---

## 修复方案

### 修复 1：正确转换 Chrome cookie → Playwright storage_state

**文件**: `backend/app/api/v1/accounts.py` 的 `extension_cookie_login` 函数

将 cookie 转换逻辑替换为正确的字段映射：

```python
# sameSite 映射表：Chrome API 值 → Playwright 值
SAME_SITE_MAP = {
    "no_restriction": "None",
    "lax": "Lax",
    "strict": "Strict",
    "unspecified": "None",
}

converted_cookies = []
for c in data.cookies:
    same_site_raw = c.get("sameSite", "unspecified").lower()
    converted = {
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c.get("path", "/"),
        "expires": c.get("expirationDate", -1),  # Chrome API 用 expirationDate
        "httpOnly": c.get("httpOnly", False),
        "secure": c.get("secure", False),
        "sameSite": SAME_SITE_MAP.get(same_site_raw, "None"),
    }
    converted_cookies.append(converted)
```

### 修复 2：统一平台名称

**文件**: `backend/app/api/v1/accounts.py`

添加平台名称别名映射，使后端同时接受 `"xhs"` 和 `"xiaohongshu"`：

```python
PLATFORM_ALIASES = {
    "xiaohongshu": "xhs",
}

def normalize_platform(platform: str) -> str:
    return PLATFORM_ALIASES.get(platform, platform)
```

在所有端点的 `platform` 参数使用前调用 `normalize_platform()`。

### 修复 3：扩展同步错误传播

**文件**: `extension/background.js` 的 `syncCookiesToBackend` 函数

让函数在同步失败时抛出异常，使调用方能够感知失败：

```javascript
async function syncCookiesToBackend(platform, cookies) {
  const config = await getConfig();
  const headers = { "Content-Type": "application/json" };
  if (config.authToken) {
    headers["Authorization"] = `Bearer ${config.authToken}`;
  }
  const response = await fetch(`${config.serverUrl}/api/v1/accounts/${platform}/extension`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({ cookies: cookies })
  });
  if (!response.ok) {
    throw new Error(`Sync failed with status ${response.status}`);
  }
  return response;
}
```

同时修改 `SYNC_COOKIES` handler，在同步失败时返回 `success: false`。

---

## 验证步骤

1. 修复后，在浏览器中登录小红书
2. 通过前端页面点击"获取Cookie"——应显示"Cookie获取成功"，状态变为"正常"
3. 点击"验证"——应显示"Cookie有效"
4. 通过弹窗点击"获取Cookie并同步"——如果后端未运行，应显示同步失败而非成功
5. 检查后端日志，确认 Playwright 验证不再抛出 `sameSite` 相关异常
