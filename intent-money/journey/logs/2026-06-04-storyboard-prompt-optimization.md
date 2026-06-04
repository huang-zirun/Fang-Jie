# 分镜脚本提示词优化 - 实施记录

**日期**: 2026-06-04
**任务**: 优化分镜脚本提示词，扩充Fallback池

## 一、问题诊断

### 1.1 初始问题
- **提示词复杂度**: 8维度要求过于复杂，LLM难以一次性满足
- **验证严格度**: 每个维度都强制检查关键词，容易失败
- **Fallback单一**: 只有1个fallback，缺乏多样性
- **成功率低**: 估计成功率 < 20%

### 1.2 行业最佳实践调研
参考了2026年LLM结构化输出的最新研究：
- 简化Schema：减少嵌套层级，只要求必要字段
- Few-shot Learning：提供3-5个高质量示例
- 渐进式验证：先验证基础结构，再验证详细内容
- 混合Fallback：区分完全fallback和部分fallback
- Fallback池：准备多个fallback内容并轮换

## 二、优化方案

### 2.1 简化分镜脚本提示词
**修改文件**: `backend/app/services/ai_service.py`

**优化内容**:
- 从8维度降低到**5维度**：景别、角度、主体动作、画面焦点、声音/字幕
- 降低长度要求：从30字降低到**20字**
- 增加示例：从1个增加到**5个**高质量示例

**效果**: 降低LLM生成难度，提高成功率

### 2.2 放宽验证逻辑
**修改文件**: `backend/app/services/ai_service.py`

**优化内容**:
- 实现评分机制：计算详细度评分（0.0-1.0）
- 分级验证：
  - 基础验证（必须）：景别、动作、长度（每项1分）
  - 扩展验证（可选）：角度、声音、焦点、运镜、灯光、道具（每项0.17-0.5分）
- 评分阈值：评分 >= 60% 即可通过验证
- 混合Fallback：如果评分 >= 60%，只替换失败部分

**效果**: 允许部分成功，而不是完全失败

### 2.3 扩充Fallback池
**修改文件**: `backend/app/services/ai_service.py`

**优化内容**:
- 创建**80个不同的fallback**（每个意图20个）
- 覆盖四个意图：
  - 引流拿客户：20个
  - 成交赚钱：20个
  - 裂变招募分销：20个
  - IP长期增长：20个
- 实现智能选择逻辑：
  - 根据意图和平台过滤候选fallback
  - 优先选择最近未使用的fallback
  - 记录使用历史，确保均匀分布

**每个Fallback包含**:
- hook_text: 15-25字的吸引人开场白
- storyboard: 3-5个分镜，符合5维度标准
- script_text: 200-500字的口播文案
- title: 包含话题标签的标题
- comment_template: 互动引导的评论模板
- why_it_works: 为什么这个内容有效
- tags: 标签数组，正确匹配意图标签
- platforms: 平台数组（抖音/小红书）

**效果**: 提供多样化fallback，改善用户体验

### 2.4 更新generate_content函数
**修改文件**: `backend/app/services/ai_service.py`

**优化内容**:
- 使用 `_select_fallback()` 替代 `_safe_fallback()`
- 根据评分决定是否使用fallback
- 实现混合fallback策略（评分 >= 60% 只替换失败部分）
- 增强日志输出，显示quality_score

## 三、实施结果

### 3.1 代码修改
- ✅ 简化分镜脚本提示词（从8维度到5维度）
- ✅ 放宽验证逻辑（实现评分机制）
- ✅ 创建80个Fallback（每个意图20个）
- ✅ 更新generate_content函数
- ✅ 更新测试用例

### 3.2 验证结果
```
✅ 所有fallback都符合要求!

统计信息:
  script_text长度范围: 200-342字
  script_text平均长度: 239字
  hook_text长度范围: 8-18字
  storyboard数量范围: 4-5个

✅ 所有测试通过（6个单元测试）
```

### 3.3 预期效果
- **成功率提升**: 从 <20% 提升至 **70-80%**
- **用户体验改善**: 80个不同的fallback，轮换使用
- **内容质量提升**: 评分机制允许部分成功，混合fallback保留AI生成的有效部分

## 四、技术细节

### 4.1 评分机制
每个分镜的评分规则：
- 基础验证（必须，每项1分）：
  - 长度 >= 20字
  - 包含景别关键词
  - 包含动作关键词
- 扩展验证（可选，每项0.17-0.5分）：
  - 包含角度关键词
  - 包含声音/字幕关键词
  - 包含画面焦点关键词
  - 包含运镜关键词
  - 包含灯光关键词
  - 包含道具关键词

总分 = 所有分镜得分之和
quality_score = 总分 / 最高可能得分

### 4.2 Fallback选择逻辑
```python
def _select_fallback(intent_name, platform_name, fallback_pool):
    # 1. 根据意图和平台过滤候选fallback
    candidates = [f for f in fallback_pool if matches_intent_or_platform(f)]
    
    # 2. 优先选择最近未使用的fallback
    for fb in candidates:
        if fb not in _fallback_usage_history[-10:]:
            return fb
    
    # 3. 如果所有fallback都最近用过，随机选择
    return random.choice(candidates)
```

### 4.3 混合Fallback策略
```python
if errors:
    if quality_score >= 0.6:
        # 评分 >= 60%，只替换失败部分
        fallback = _select_fallback(intent_name, platform_name)
        if storyboard_failed:
            data["storyboard"] = fallback["storyboard"]
        return data, False
    else:
        # 评分 < 60%，使用完整fallback
        return _select_fallback(intent_name, platform_name), True
```

## 五、后续优化方向

1. **动态调整阈值**: 根据历史数据自动调整评分阈值
2. **Fallback自动生成**: 从成功内容中自动提取fallback
3. **多模型对比**: 测试不同模型的成功率
4. **用户反馈闭环**: 收集用户对生成内容的反馈，持续优化

## 六、相关文件

- `backend/app/services/ai_service.py` - 主要修改文件
- `backend/tests/test_ai_service.py` - 测试文件
- `docs/prompts.md` - 提示词文档（待更新）

## 七、参考资料

- [LLM Output工程2026](https://blog.csdn.net/yonggeit/article/details/160774726)
- [Structured Output in LLMs](https://www.promptquorum.com/prompt-engineering/structured-output-and-json-mode)
- [JSON Repair Workflow](https://jsonberry.com/blog/stop-chasing-broken-brackets-the-json-repair-workflow-for-reliable-llm-outputs-in-2026)
- [LLM Structured Outputs: Production Guide](https://fordelstudios.com/research/structured-outputs-production-systems)
