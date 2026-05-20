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

## 风险与约束
- 平台 API 审核不确定 → MVP 不依赖
- AI 内容质量不稳定 → 校验 + 兜底
- 结构库质量依赖运营 → 需提前准备 20+ 模板
