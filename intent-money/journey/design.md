# Intent Money OS — 项目设计快照

> 最后更新: 2026-06-04

## 项目定位

意图变现 OS — 帮助内容创作者从"意图"到"变现"的全流程工具。核心链路：爆款选题 → AI 生成脚本 → 视频发布 → 数据追踪 → 诊断优化。

## 技术栈

- **后端**: FastAPI + SQLAlchemy (async) + SQLite (aiosqlite)
- **前端**: Vue 3 + Vant UI + TypeScript
- **AI**: DeepSeek V4 Flash (via OpenRouter)
- **浏览器自动化**: Playwright
- **浏览器扩展**: Chrome Extension MV3 (cookies / tabs / storage / scripting 权限)
- **部署**: Docker Compose (FastAPI + Frontend + Nginx) → `https://trades.zzy88.com`

## 核心架构决策

### 日志系统中文化（2026-06-04 更新）

**全量中文化改造**：22 个文件共 162 条英文日志消息替换为简洁中文（每条不超过 20 汉字），去除冗余修饰词，保留关键上下文。技术术语（Cookie、AI、URL 等）保持英文。无破坏性变更。
- **详细记录**: `journey/logs/2026-06-04-localize-logging.md`

### AI内容生成优化（2026-06-04 更新）

**分镜脚本提示词优化**：
- **问题**: 8维度要求过于复杂，LLM成功率 < 20%，fallback单一缺乏多样性
- **解决方案**:
  1. 简化提示词：从8维度降低到5维度（景别、角度、主体动作、画面焦点、声音/字幕）
  2. 放宽验证：实现评分机制（评分 >= 60% 即可通过）
  3. 扩充Fallback池：80个不同的fallback（每个意图20个）
  4. 混合Fallback策略：评分 >= 60% 只替换失败部分
- **预期效果**: 成功率提升至 70-80%，用户体验显著改善
- **详细记录**: `journey/logs/2026-06-04-storyboard-prompt-optimization.md`

### 账号绑定双路径架构

系统支持两条账号绑定路径，按优先级自动选择：

1. **浏览器扩展路径** (`extension/`): 用户安装 Chrome Extension，前端页面通过 `postMessage` 与 content script 通信（content script 不得使用 `event.source === window` 过滤），background service worker 通过 `chrome.cookies` API 获取平台 Cookie 并同步到后端，同时通过 `chrome.tabs.sendMessage` 向前端广播登录状态变化。最佳用户体验，支持一键获取和后台自动同步。
2. **Playwright 路径** (`qrcode_login.py`): 未安装扩展时使用，启动 Playwright 无头浏览器完成扫码登录。

**关键约束**：
- 两条路径最终都存储为 Playwright `storage_state` 格式，确保后续数据抓取兼容。
- 扩展路径依赖 `content_scripts` 的 `matches` 包含部署域名，否则前端与扩展通信中断。

### 市场数据抓取架构（2026-06-03 更新）

系统支持**扩展优先**的市场数据抓取策略，绕过后端直接调用 API 的签名限制：

#### 抖音扩展抓取（已有）
- `douyin_content.js` 注入抖音页面，提取 SSR 数据 (`__INIT_PROPS__`) 和 X-Bogus 签名
- `background.js` 的 `SCRAPE_DOUYIN_SEARCH` 处理器实现三层降级：API 调用 → SSR 提取 → DOM 解析
- 数据通过 `POST /market/extension-scrape` 同步到后端

#### 小红书扩展抓取（新增）
- **四层降级策略**（比抖音多一层请求拦截）：
  1. **请求拦截**（最优先）: Main World 脚本 monkey-patch `fetch` 和 `XMLHttpRequest`，被动捕获用户浏览时产生的 API 响应，零签名问题
  2. **主动 API 调用**: 通过 Main World 获取 X-s/X-t 签名 + Cookie，主动调用搜索 API
  3. **SSR 数据提取**: 读取 `window.__INIT_PROPS__` 获取首屏数据
  4. **DOM 解析**: 解析页面 DOM 结构（最后降级）

- **关键文件**:
  - `xhs_main_world.js`: Main World 脚本，处理 SSR 提取、请求拦截、签名生成
  - `xhs_content.js`: Content Script，消息桥接 + DOM 解析降级
  - `background.js`: 新增 6 个处理器 (`SCRAPE_XHS_SEARCH`, `XHS_INTERCEPTED_DATA`, `XHS_SIGNATURE_CAPTURED`, `XHS_SSR_DATA`, `CHECK_XHS_TAB`, `OPEN_XHS_SEARCH`)
  - `market.py`: 新增 `POST /market/extension-scrape-xhs` 端点

- **消息传递链路**:
  ```
  XHS 页面 (Main World) 
    → postMessage (source: "intent-money-xhs")
    → Content Script (Isolated World) 
    → chrome.runtime.sendMessage
    → Background Service Worker 
    → fetch() 同步到后端
  ```

- **关键约束**:
  - Main World 脚本通过 `web_accessible_resources` 暴露，content script 通过 `<script src>` 注入
  - 小红书 API 需要 X-s/X-t 签名（比抖音的 X-Bogus 更复杂），请求拦截是最可靠的获取方式
  - 签名函数位置不固定，需要在多个候选位置搜索 (`window.__xhsSign`, `window._webmsxyw`, webpack chunks 等)

### Cookie 存储格式

扫码登录保存的是 Playwright `storage_state` JSON 格式（`{"cookies": [...], "origins": [...]}`），而非传统的 `name=value; name=value` 字符串。手动导入 Cookie 仍使用字符串格式。验证器需要同时支持两种格式。

### Cookie 验证统一入口

所有平台的 Cookie 验证通过 `cookie_lifecycle.validate_platform_cookie()` 统一入口分发：
- XHS → `xhs_cookie_validator.validate_xhs_cookie()` (Playwright 浏览器验证)
- 抖音 → `douyin_cookie_validator.validate_douyin_cookie()` (Playwright 浏览器验证)

`accounts.py` 和 `cookie_lifecycle.py` 不再各自实现验证逻辑。

## 已知约束与权衡

- **SQLite**: 不支持并发写入，使用 `render_as_batch=True` 兼容 Alembic 迁移
- **Alembic 数据库路径**: `env.py` 必须支持 `DATABASE_URL` 环境变量覆盖 `alembic.ini`，否则 Docker 中 Alembic 和 App 使用不同数据库文件
- **Alembic 迁移错误处理**: `entrypoint.sh` 必须 `set -e`，迁移失败时阻止应用启动
- **PRAGMA foreign_keys**: SQLite 中 PRAGMA 在迁移 `batch_alter_table` 模式（DROP/RECREATE）下会冲突，仅在应用层连接时启用，不在 Alembic 迁移过程中启用
- **扩展域名限制**: `content_scripts` 的 `matches` 必须显式包含部署域名（如 `https://trades.zzy88.com/*`），否则前端无法检测扩展
- **扩展消息过滤**: Chrome MV3 content script 运行在隔离世界，`window` 是代理对象，**禁止使用 `event.source === window`** 过滤 `postMessage`，否则页面消息会被静默丢弃。正确做法是通过 `event.data.source === 'intent-money-extension'` 防止消息循环。
- **扩展检测可靠性**: content script 加载时机晚于前端 `onMounted`，检测机制必须实现重试（指数退避，最多 5 次）+ `visibilitychange` 重检。
- **平台反爬**: 小红书和抖音都有反自动化检测，需要注入 stealth.js 脚本
- **Cookie 有效期**: 平台 Cookie 会过期，需要定期验证和重新登录
- **XHS 签名复杂性**: 小红书 X-s/X-t 签名算法比抖音 X-Bogus 更复杂且更新频繁，请求拦截是最可靠的绕过方式

## 关键模块

| 模块 | 职责 |
|------|------|
| `extension/` | Chrome Extension MV3：content script 桥接、background Cookie 监听与同步、市场数据抓取 |
| `extension/xhs_main_world.js` | 小红书 Main World 脚本：SSR 提取、fetch/XHR 拦截、签名生成 |
| `extension/xhs_content.js` | 小红书 Content Script：消息桥接、DOM 解析降级 |
| `extension/douyin_content.js` | 抖音 Content Script：SSR 提取、X-Bogus 签名、DOM 解析 |
| `accounts.py` | 账号管理 REST API（含扩展 Cookie 接收端点 `/extension`） |
| `qrcode_login.py` | Playwright 路径扫码登录 |
| `xhs_cookie_validator.py` | 小红书 Cookie 浏览器验证 |
| `douyin_cookie_validator.py` | 抖音 Cookie 浏览器验证 |
| `cookie_lifecycle.py` | Cookie 生命周期管理 + 统一验证入口 |
| `cookie_vault.py` | Cookie AES-GCM 加密存储 |
| `market.py` | 市场数据 API（含扩展抓取数据接收端点） |
| `market_service.py` | 市场数据服务（含 `scrape_xhs_via_extension()`） |
