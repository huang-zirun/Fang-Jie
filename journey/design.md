# Intent Money OS - 项目设计快照

## 项目概述
意图选择式赚钱系统 MVP，面向袜子分销商的"一键赚钱执行系统"。

## 核心闭环
选择意图 → 获取唯一任务 → 用户发布 → 手动回传数据 → 规则诊断 → 生成下一条优化任务

## 技术栈
- 前端：Vue 3 + TypeScript + Vant 4 + Pinia + Vite
- 后端：FastAPI (Python 3.11+) + SQLAlchemy + Alembic
- 数据库：SQLite (aiosqlite 异步驱动)
- AI：DeepSeek V4 Flash via OpenRouter API（openai SDK AsyncOpenAI）
- 部署：Docker Compose (FastAPI + Nginx，无独立数据库容器)
- 包管理：uv (Python), pnpm (前端)
- 端口：后端 9090，前端 5173/5174

## MVP 范围
- 仅"引流拿客户"意图
- 仅抖音 + 小红书平台
- 手动数据回填（不接平台 API）
- 规则诊断（非 AI 学习）
- H5 单页应用（微信内嵌 / 浏览器）

## 关键设计决策
1. 单体架构，不引入微服务/消息队列
2. 匿名用户可完成完整闭环，JWT 7 天有效期
3. AI 仅负责文案填充，诊断由规则模块负责
4. AI 失败时使用 fallback_content 兜底
5. 换一条每天限 1 次
6. 任务状态机：PENDING → PUBLISHED → REPORTED → DIAGNOSED → (下一条)

## 数据模型
9 张核心表：users, user_sessions, intents, platforms, content_structures, content_tasks, performance_reports, diagnosis_results, optimization_rules

## 项目目录
代码位于 `intent-money/` 目录下，结构为 frontend / backend / docker

## 当前阶段
Phase 1 - 闭环骨架开发

## UI 设计系统（2026-05-21 更新）

### 视觉风格
小红书风格：温暖、生活化、杂志感的移动内容创作工具

### 设计 Token
- 品牌色：`#FF2442`（小红书红）
- 背景色：纯白 `#FFFFFF` / 次级 `#F7F7F7` / 输入框 `#F2F2F2`
- 文字色：主 `#333333` / 次 `#666666` / 辅助 `#999999`
- 圆角：卡片 16px / 按钮 24px（全圆角胶囊）/ 输入框 12px
- 阴影：`0 2px 12px rgba(0,0,0,0.04)` / `0 4px 20px rgba(0,0,0,0.08)`
- 字体：`-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', 'Helvetica Neue', sans-serif`

### 页面结构
- 意图选择页：纯白底 + 左对齐标题 + 2 列竖版卡片网格（stagger 入场动画）
- 任务详情页：自定义导航栏 + 卡片化内容区（左侧彩色竖条）+ 悬浮底部操作区
- 数据报告页：任务摘要卡片 + 表单卡片 + 诊断结果卡片（图标 + 卡片式展示）

### 动效规范
- 页面过渡：opacity 0→1 + translateY(20px→0)，300ms ease-out
- 卡片交互：hover translateY(-2px) / active scale(0.98)

## 风险与约束
- 平台 API 审核不确定 → MVP 不依赖
- AI 内容质量不稳定 → 校验 + 兜底
- 结构库质量依赖运营 → 需提前准备 20+ 模板
