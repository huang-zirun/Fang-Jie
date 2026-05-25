# 意图变现 (Intent Money OS) - 前端视觉重设计计划

## 项目背景

**意图选择式赚钱系统** — 面向袜子分销商的一键赚钱执行系统。用户选择赚钱目标（引流/成交/裂变/IP），系统自动基于实时爆款数据生成唯一可执行任务，形成"选择→执行→反馈→优化"的变现闭环。

## 设计方向：「霓虹赛博 + 东方水墨」融合美学

### 为什么选择这个方向？

这个系统有两个核心特质：

1. **AI 驱动的科技感** — 实时数据、智能优化、学习进化
2. **接地气的赚钱工具** — 面向宝妈、副业人群，需要亲和力和信任感

传统 SaaS 工具要么太冰冷（纯科技感），要么太廉价（纯可爱风）。本设计将**赛博朋克的未来感**与**东方水墨的人文温度**融合，创造出独一无二的品牌气质：

* **赛博元素**：霓虹光效、数据流动、动态粒子背景 — 表达 AI 智能和实时数据

* **水墨元素**：留白呼吸感、毛笔笔触边框、宣纸纹理 — 表达人文温度和可信赖感

* **融合结果**：一个既有未来科技力量、又有东方人文温度的赚钱工具

## 色彩系统

### 主色调

```
--ink-black:      #0a0a0f    // 深墨黑 - 主背景
--ink-charcoal:   #1a1a2e    // 炭墨色 - 卡片背景
--neon-cyan:      #00f5d4    // 霓虹青 - 主品牌色
--neon-magenta:   #ff006e    // 霓虹洋红 - 强调/CTA
--neon-gold:      #ffd60a    // 霓虹金 - 成功/收益
--paper-white:    #f0ece2    // 宣纸白 - 主文字
--ink-gray:       #8b8b9e    // 淡墨灰 - 次要文字
```

### 意图专属色彩（保留功能区分）

```
--intent-traffic:    #00f5d4    // 引流 - 青
--intent-deal:       #ff006e    // 成交 - 洋红
--intent-recruit:    #ffd60a    // 裂变 - 金
--intent-ip:         #9b5de5    // IP - 紫
```

### 渐变系统

```
--gradient-hero:     linear-gradient(135deg, #00f5d4 0%, #00bbf9 50%, #9b5de5 100%)
--gradient-card:     linear-gradient(180deg, rgba(26,26,46,0.9) 0%, rgba(10,10,15,0.95) 100%)
--gradient-glow:     radial-gradient(ellipse at center, rgba(0,245,212,0.15) 0%, transparent 70%)
```

## 字体系统

### 中文字体栈

```css
font-family: 'Noto Serif SC', 'Source Han Serif SC', 'STSong', 'SimSun', serif;
```

* **标题**：思源宋体 (Noto Serif SC) — 东方书卷气，有文化底蕴

* **正文**：系统默认无衬线 — 保证移动端可读性

### 英文字体栈

```css
font-family: 'Space Mono', 'JetBrains Mono', monospace;
```

* **数据/标签**：等宽字体 — 科技感、数据感

### 字体大小

```
Display:    32px / 700 / -1.5px tracking  // 首屏大标题
H1:         24px / 700 / -0.5px tracking  // 页面标题
H2:         18px / 600                     // 卡片标题
Body:       15px / 400 / 1.7 line-height   // 正文
Caption:    12px / 500                     // 标签/辅助
Mono:       13px / 500                     // 数据/代码
```

## 空间与布局

### 页面结构

* 全屏深色背景，内容区域居中

* 最大内容宽度：420px（移动端优先）

* 水平内边距：20px

* 卡片间距：16px

* 元素圆角：12px（卡片），24px（按钮），4px（标签）

### 布局原则

* **大量留白**：每个区块之间留出充足呼吸空间

* **非对称节奏**：打破完全居中的单调感，关键元素微微偏移

* **层叠深度**：通过阴影和发光创造 z 轴层次

## 动效系统

### 页面加载序列

1. 背景粒子缓慢浮现（0.5s）
2. 标题文字逐字淡入（0.8s，stagger 30ms）
3. 卡片从下方滑入（0.6s，stagger 80ms）
4. 底部按钮弹性出现（0.4s，spring easing）

### 交互反馈

* **按钮悬停**：霓虹光晕扩散 + 微微上浮

* **卡片点击**：缩放至 0.97 + 涟漪波纹

* **页面切换**：当前页淡出 + 新页从右滑入

* **数据加载**：骨架屏带微弱脉冲光效

### 背景效果

* **动态粒子网格**：Canvas 绘制的缓慢流动粒子，鼠标靠近时轻微扰动

* **水墨晕染**：微妙的径向渐变在背景中缓慢呼吸变化

* **扫描线**：极淡的水平扫描线纹理（opacity 0.03），增加复古科技感

## 各页面设计要点

### 1. 意图选择页 (IntentSelect)

* **背景**：深色 + 动态粒子 + 中心发光晕

* **标题**：「今天你想通过什么方式赚钱？」— 宋体大字，下方带霓虹下划线动画

* **副标题**：「选一个赚钱目标，AI 替你搞定一切」— 等宽字体，带打字机效果

* **意图卡片**：

  * 2×2 网格，每张卡片有独特霓虹边框色

  * 卡片内：意图图标（SVG 线条动画）+ 意图名称 + 描述

  * 悬停时边框发光增强，图标动画播放

* **底部**：「查看历史任务」— 水墨笔触下划线链接

### 2. 平台选择页 (PlatformSelect)

* **导航**：自定义导航栏，返回按钮带霓虹光效

* **标题**：「在哪个平台发布？」

* **平台卡片**：

  * 大尺寸卡片，平台 Logo + 名称 + 描述

  * 抖音卡片：洋红色霓虹边框

  * 小红书卡片：青色霓虹边框

* **加载状态**：生成任务时显示「AI 正在为你匹配最优内容结构...」+ 脉冲动画

### 3. 任务详情页 (TaskDetail)

* **导航**：粘性顶部导航，带毛玻璃效果

* **任务头部**：平台标签 + 状态标签（带发光效果）

* **信息横幅**：

  * 优化提示：洋红色边框卡片

  * 为什么有效：青色边框卡片

* **内容卡片**（每个模块一个卡片）：

  * 3秒钩子：大号引号装饰 + 霓虹文字

  * 分镜脚本：编号圆形 + 渐变背景

  * 口播文案：带复制按钮

  * 发布标题：带复制按钮

  * 评论区话术：带左边框装饰

* **转化话术卡片**：根据意图类型显示不同颜色边框

* **底部操作区**：

  * 「确认已发放」主按钮：洋红色渐变，带发光

  * 「自动发布」次按钮：透明 + 青色边框

  * 「换一条」次按钮：透明 + 灰色边框

### 4. 数据回填页 (DataReport)

* **任务摘要**：标题 + 平台 + 日期

* **表单卡片**：播放量/评论数/私信数输入框

  * 输入框：深色背景 + 霓虹聚焦边框

* **诊断结果卡片**：

  * 问题类型 / 优化方向 / 优化建议 — 三列图标卡片

  * AI 深度分析：紫色主题卡片，带置信度进度条

* **「获取下一条优化任务」按钮**：金色渐变

### 5. 历史任务页 (TaskHistory)

* **筛选栏**：自定义下拉筛选，带霓虹边框

* **任务列表**：

  * 每条任务卡片：顶部标签行（意图+平台+状态）+ 标题 + 底部数据

  * 状态标签带发光效果

* **空状态**：水墨风格插画 + 引导按钮

### 6. 管理后台页 (Admin)

* **标签页**：自定义标签切换，激活标签带霓虹下划线

* **统计卡片**：2×2 网格，每个卡片有不同霓虹色渐变背景

* **数据表格/卡片**：深色卡片 + 霓虹边框分隔线

* **进度条**：霓虹渐变填充

## 全局组件设计

### 自定义导航栏

```
高度：56px
背景：rgba(10,10,15,0.85) + backdrop-filter: blur(20px)
边框底部：1px solid rgba(0,245,212,0.1)
返回按钮：36×36，悬停时霓虹光晕
标题：16px / 600 / 宣纸白
```

### 按钮系统

```
主按钮：
  背景：linear-gradient(135deg, #ff006e, #ff4d6d)
  文字：#ffffff
  圆角：24px
  阴影：0 4px 20px rgba(255,0,110,0.3)
  悬停：阴影扩大 + 微微上浮

次按钮（描边）：
  背景：transparent
  边框：1px solid var(--neon-cyan)
  文字：var(--neon-cyan)
  悬停：背景填充为 rgba(0,245,212,0.1)

幽灵按钮：
  背景：transparent
  文字：var(--ink-gray)
  悬停：文字变亮 + 水墨下划线
```

### 卡片系统

```
背景：linear-gradient(180deg, rgba(26,26,46,0.9), rgba(10,10,15,0.95))
边框：1px solid rgba(0,245,212,0.15)
圆角：12px
阴影：0 4px 24px rgba(0,0,0,0.4)
悬停：边框发光增强 + 微微上浮
```

### 输入框

```
背景：rgba(26,26,46,0.6)
边框：1px solid rgba(139,139,158,0.2)
圆角：12px
聚焦：边框变为 var(--neon-cyan) + 外发光
```

### 标签/徽章

```
背景：rgba(0,245,212,0.1)
文字：var(--neon-cyan)
边框：1px solid rgba(0,245,212,0.3)
圆角：4px
字体：12px / 500 / Space Mono
```

## 技术实现要点

### 新增依赖

```json
{
  "dependencies": {
    "vant": "^4.9.24"  // 保持现有
  }
}
```

### 不引入新依赖的原则

* 所有动画使用 CSS @keyframes 和 Vue Transition

* 粒子背景使用原生 Canvas API

* 字体使用 Google Fonts CDN（Noto Serif SC + Space Mono）

### 字体加载

在 `index.html` 中添加：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
```

### 性能考虑

* 粒子背景在低端设备上降级为静态渐变

* 使用 `will-change` 优化动画性能

* 动画使用 `transform` 和 `opacity` 确保 GPU 加速

* 深色主题天然省电（OLED 屏幕）

## 实现步骤

### Phase 1: 基础样式系统

备份原始页面设计

1. 更新 `index.html` — 添加字体加载、更新标题
2. 重写 `global.css` — 全新 CSS 变量系统 + 基础样式
3. 更新 `App.vue` — 添加粒子背景组件 + 页面过渡动画

### Phase 2: 全局组件

1. 创建 `ParticleBackground.vue` — Canvas 粒子背景
2. 创建 `CyberNav.vue` — 自定义霓虹导航栏
3. 创建 `CyberCard.vue` — 霓虹卡片组件
4. 创建 `CyberButton.vue` — 霓虹按钮组件

### Phase 3: 页面逐个改造

1. 重写 `IntentSelect.vue` — 首屏全新设计
2. 重写 `PlatformSelect.vue` — 平台选择页
3. 重写 `TaskDetail.vue` — 任务详情页（最复杂）
4. 重写 `DataReport.vue` — 数据回填页
5. 重写 `TaskHistory.vue` — 历史任务页
6. 重写 `Admin.vue` — 管理后台页

### Phase 4: 细节打磨

1. 添加页面加载动画序列
2. 优化移动端触摸反馈
3. 添加减少动画偏好支持（prefers-reduced-motion）
4. 测试所有交互流程

## 文件变更清单

### 修改文件

* `frontend/index.html` — 添加字体加载

* `frontend/src/styles/global.css` — 全新设计系统

* `frontend/src/App.vue` — 添加背景 + 过渡动画

* `frontend/src/views/IntentSelect.vue` — 全新设计

* `frontend/src/views/PlatformSelect.vue` — 全新设计

* `frontend/src/views/TaskDetail.vue` — 全新设计

* `frontend/src/views/DataReport.vue` — 全新设计

* `frontend/src/views/TaskHistory.vue` — 全新设计

* `frontend/src/views/Admin.vue` — 全新设计

### 新增文件

* `frontend/src/components/ParticleBackground.vue`

* `frontend/src/components/CyberNav.vue`

* `frontend/src/components/CyberCard.vue`

* `frontend/src/components/CyberButton.vue`

## 设计验证清单

* [ ] 首屏 3 秒内传达核心价值

* [ ] 意图卡片在 2×2 网格中清晰可辨

* [ ] 任务详情页信息层级清晰

* [ ] 所有按钮在深色背景上有足够对比度

* [ ] 动画流畅，不卡顿（目标 60fps）

* [ ] 移动端触摸目标 ≥ 44×44px

* [ ] 支持 prefers-reduced-motion

* [ ] 文字可读性 WCAG AA 标准

