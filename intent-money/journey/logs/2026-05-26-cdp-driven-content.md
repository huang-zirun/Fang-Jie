# CDP 驱动内容生成架构实施日志

## 背景

当前系统通过 CDP 抓取平台爆款数据（market_hots），但内容生成仅将这些数据作为"风向标"来加权选择内容结构模板，实际文案仍由 LLM 根据预定义模板生成。

**核心问题**：CDP 抓取的热门内容标题、文案、标签等原始数据未被传递到 AI 生成环节，导致生成的内容与市场热点存在断层。

## 目标

让 LLM 能够直接参考实时抓取的热门内容（标题、文案、标签、情绪结构等）进行创作，使生成的内容更贴近当前市场热点。

## 实施方案

### Phase 1: 核心链路改造（已完成）

#### 1. 修改 task_service.py

**新增 `_get_market_insights()` 函数**：
- 从 market_hots 表中获取最近 5 条活跃的热门数据
- 聚合 analysis_result 中的创作灵感数据
- 提取 comment_sentiment 作为用户情感反馈

**修改 `match_content_structure()`**：
- 返回类型从 `ContentStructure | None` 改为 `tuple[ContentStructure | None, dict | None]`
- 在选择内容结构后，调用 `_get_market_insights()` 获取市场洞察

**修改 `generate_task()`**：
- 接收 market_insights 并传递给 `generate_content()`

#### 2. 修改 ai_service.py

**修改 `_build_prompt()`**：
- 新增 `market_insights` 参数
- 在 prompt 中注入市场热门参考：
  - 热门标题风格参考
  - 热门标签建议
  - 当前热门情绪节奏
  - 高互动钩子文案参考
  - 用户情感反馈
- 添加使用说明，强调"参考但不要复制"

**修改 `generate_content()`**：
- 新增 `market_insights` 参数
- 传递给 `_build_prompt()`

### 数据流

```
CDP 抓取 → market_hots 表
                ↓
    _get_market_insights() → 聚合分析数据
                ↓
    generate_content() → AI Prompt 注入市场参考
                ↓
    生成贴近市场热点的内容
```

### market_insights 数据结构

```python
{
    "hot_titles": ["标题1", "标题2", ...],  # 热门标题列表（最多10条）
    "hot_tags": ["#标签1", "#标签2", ...],  # 热门标签（最多10条）
    "emotional_patterns": ["痛点→共鸣→解决方案", ...],  # 情绪转换模式
    "high_engagement_hooks": ["钩子1", "钩子2", ...],  # 高互动钩子
    "content_themes": ["主题1", "主题2", ...],  # 热门主题
    "sentiment_summary": {  # 评论情感分析摘要
        "positive_ratio": "60%",
        "key_topics": ["话题1", "话题2"]
    }
}
```

## 关键变更文件

| 文件 | 变更内容 |
|------|----------|
| `task_service.py` | 新增 `_get_market_insights()`，修改 `match_content_structure()` 返回元组，更新 `generate_task()` |
| `ai_service.py` | 新增 `market_insights` 参数，在 prompt 中注入市场热门数据 |
| `journey/design.md` | 新增"CDP 驱动内容生成架构"章节 |

## 降级策略

当 market_insights 为空时（无活跃热门数据），系统保持原有模板驱动生成逻辑，确保功能可用性。

## 后续计划

### Phase 2: 数据分析增强（可选）
- 创建 `market_analyzer.py` 服务
- 使用 AI 分析热门内容，自动填充 market_hots.analysis_result
- 在定时抓取任务中集成分析流程

### Phase 3: 效果验证与优化
- A/B 测试对比使用/不使用市场数据的内容效果
- 根据反馈调整 prompt 设计和数据权重

## 实施日期

2026-05-26
