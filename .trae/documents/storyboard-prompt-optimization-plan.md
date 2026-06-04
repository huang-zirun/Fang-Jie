# 分镜脚本提示词优化计划

## 一、问题分析

### 1.1 当前状态

**提示词复杂度**：
- 分镜脚本要求包含 **8个维度**：景别、角度、运镜方式、灯光设置、画面主体、主体动作、道具清单、声音/字幕
- 每个分镜描述至少 **30字**
- 提供了错误示例和正确示例各1个

**验证严格度**：
- 每个维度都必须包含特定关键词
- 分镜数量限制在3-5个
- 口播文案200-500字符
- 标题必须包含话题标签
- 评论必须有互动引导

**Fallback机制**：
- 只有 **1个固定的fallback内容**（`SAFE_FALLBACK_CONTENT`）
- 重试次数：2次
- 没有轮换机制
- 没有部分fallback策略（虽然有混合fallback逻辑，但只针对分镜）

### 1.2 核心问题

1. **LLM成功率低**：8维度要求过于复杂，LLM很难一次性满足所有条件
2. **验证过严**：每个维度都检查关键词，容易导致验证失败
3. **Fallback单一**：只有1个fallback，缺乏多样性，用户体验差
4. **示例不足**：只有1个正确示例，LLM难以充分理解要求

### 1.3 行业最佳实践（2026年调研结果）

根据最新的LLM结构化输出研究：

1. **简化Schema**：减少嵌套层级，只要求必要字段
2. **Few-shot Learning**：提供3-5个高质量示例
3. **渐进式验证**：先验证基础结构，再验证详细内容
4. **混合Fallback**：区分完全fallback和部分fallback
5. **Fallback池**：准备多个fallback内容并轮换
6. **JSON修复**：修复比重试更便宜（节省73% token成本）

参考来源：
- [LLM Output工程2026](https://blog.csdn.net/yonggeit/article/details/160774726)
- [Structured Output in LLMs](https://www.promptquorum.com/prompt-engineering/structured-output-and-json-mode)
- [JSON Repair Workflow](https://jsonberry.com/blog/stop-chasing-broken-brackets-the-json-repair-workflow-for-reliable-llm-outputs-in-2026)
- [LLM Structured Outputs: Production Guide](https://fordelstudios.com/research/structured-outputs-production-systems)

---

## 二、优化方案

### 方案概述

采用 **"简化提示词 + 增加示例 + 放宽验证 + 扩充Fallback池"** 的组合策略。

### 2.1 简化分镜脚本提示词（推荐方案）

**当前问题**：8维度要求过于复杂，LLM难以一次性满足

**优化策略**：
1. **降低维度要求**：从8维度降低到 **5维度**
   - 保留：景别、角度、主体动作、画面焦点、声音配合
   - 移除：运镜方式、灯光设置、道具清单（这些可以合并到描述中，不强制要求）

2. **降低长度要求**：从30字降低到 **20字**

3. **提供更多示例**：从1个增加到 **3-5个**正确示例

**理由**：
- 5维度已经足够指导拍摄（景别+角度+动作+焦点+声音）
- 运镜、灯光、道具可以在描述中自然提及，不强制
- 更多示例帮助LLM理解模式

### 2.2 放宽验证逻辑

**当前问题**：每个维度都强制检查关键词，容易失败

**优化策略**：
1. **分级验证**：
   - **基础验证**（必须通过）：景别、动作、长度
   - **扩展验证**（可选）：角度、声音、道具

2. **评分机制**：
   - 不再"全或无"，而是计算详细度评分
   - 评分 >= 60% 即可通过验证
   - 评分 < 60% 才使用fallback

3. **混合Fallback优化**：
   - 如果只有部分维度缺失，只替换缺失部分
   - 保留LLM生成的其他有效内容

### 2.3 扩充Fallback池（核心需求）

**当前问题**：只有1个fallback，缺乏多样性

**优化策略**：
1. **创建20个Fallback内容**：
   - 覆盖不同场景：收纳整理、搭配建议、使用体验、对比测评等
   - 覆盖不同平台：抖音、小红书
   - 覆盖不同意图：引流、成交、招募、IP

2. **轮换机制**：
   - 基于时间戳或任务ID选择fallback
   - 避免连续使用相同fallback
   - 记录使用历史，确保均匀分布

3. **智能匹配**：
   - 根据意图类型选择相关fallback
   - 根据平台类型选择适配fallback
   - 优先选择最近未使用的fallback

### 2.4 增加Few-shot示例

**当前问题**：只有1个示例，LLM难以充分理解

**优化策略**：
在提示词中增加3-5个高质量示例：

**示例1（痛点型-抖音）**：
```json
{
  "shot": 1,
  "description": "近景-平视：早上翻抽屉找袜子，拿出两只不同款，表情着急",
  "duration": "3s",
  "label": "痛点开场"
}
```

**示例2（对比型-小红书）**：
```json
{
  "shot": 1,
  "description": "特写-俯拍：新旧袜子对比，左边起球变形，右边完好如新",
  "duration": "封面",
  "label": "对比吸引"
}
```

**示例3（体验型-抖音）**：
```json
{
  "shot": 1,
  "description": "中景-45度：上脚走两步，展示袜口贴合和舒适度",
  "duration": "5s",
  "label": "使用体验"
}
```

---

## 三、实施步骤

### 步骤1：简化分镜脚本提示词

**文件**：`backend/app/services/ai_service.py`

**修改内容**：
1. 在 `_build_prompt()` 函数中：
   - 将分镜维度从8个降低到5个
   - 更新分镜脚本详细度标准说明
   - 增加3-5个示例

2. 更新错误示例和正确示例

**具体修改**：
```python
# 当前（第276-287行）
parts.extend([
    "",
    "## 内容详细度要求（必须满足）",
    "",
    "### 分镜脚本详细度标准（每个分镜必须包含8个维度）：",
    "1. **景别**：远景/全景/中景/近景/特写/大特写",
    "2. **角度**：俯拍/平视/仰拍/45度侧拍/正面/侧面/背面",
    "3. **运镜方式**：固定/推/拉/摇/移/跟/升降",
    "4. **灯光设置**：自然光/柔光/侧光/逆光/顶光/补光",
    "5. **画面主体**：人物/手部/产品/场景，具体位置和姿态",
    "6. **主体动作**：具体动作细节（拿起、对比、按压、试穿、整理、拉伸、翻转等）",
    "7. **道具清单**：需要出现的具体道具（袜子、鞋、抽屉、标签等）",
    "8. **声音/字幕**：口播内容、音效提示、字幕样式和位置",
    ...
])

# 优化后
parts.extend([
    "",
    "## 内容详细度要求（必须满足）",
    "",
    "### 分镜脚本详细度标准（每个分镜必须包含5个核心维度）：",
    "1. **景别**：远景/全景/中景/近景/特写/大特写",
    "2. **角度**：俯拍/平视/仰拍/45度侧拍/正面/侧面/背面",
    "3. **主体动作**：具体动作细节（拿起、对比、按压、试穿、整理、拉伸、翻转等）",
    "4. **画面焦点**：视线集中点（厚度、贴合度、材质细节等）",
    "5. **声音/字幕**：口播内容、音效提示、字幕样式和位置",
    "",
    "**可选补充**：运镜方式、灯光设置、道具清单可在描述中自然提及",
    "",
    "**错误示例**：'特写：袜子的缓震和透气设计'（太笼统，缺少角度、动作等关键信息）",
    "",
    "**正确示例1（痛点型）**：",
    "'近景-平视：早上翻抽屉找袜子，拿出两只不同款，表情着急，同期声：袜子乱放真的会拖慢出门'",
    "",
    "**正确示例2（对比型）**：",
    "'特写-俯拍：新旧袜子对比，左边起球变形，右边完好如新，画面左侧配字幕\"淘汰标准\"'",
    "",
    "**正确示例3（体验型）**：",
    "'中景-45度：上脚走两步，展示袜口贴合和舒适度，背景虚化，同期声：确实舒服多了'",
    ...
])
```

### 步骤2：放宽验证逻辑

**文件**：`backend/app/services/ai_service.py`

**修改内容**：
1. 在 `_validate_output()` 函数中：
   - 降低分镜描述长度要求：30字 → 20字
   - 实现分级验证：基础验证 + 扩展验证
   - 实现评分机制：计算详细度评分

2. 修改验证逻辑：
   - 基础验证（必须）：景别、动作、长度
   - 扩展验证（可选）：角度、声音、道具
   - 评分 >= 60% 即可通过

**具体修改**：
```python
def _validate_output(data: dict) -> tuple[list[str], bool, float]:
    """Validate AI output. Returns (errors, storyboard_failed, quality_score).

    quality_score: 0.0-1.0, 表示内容详细度评分
    """
    errors = []
    storyboard_failed = False
    quality_score = 0.0

    # ... 基础验证 ...

    storyboard = data.get("storyboard", [])
    if not isinstance(storyboard, list) or len(storyboard) < 3 or len(storyboard) > 5:
        errors.append("storyboard invalid (must have 3-5 shots)")
        storyboard_failed = True
    else:
        # 计算详细度评分
        total_score = 0
        max_score = len(storyboard) * 5  # 每个分镜最多5分

        for i, shot in enumerate(storyboard):
            desc = shot.get("description", "")
            shot_score = 0

            # 基础验证（必须，每项1分）
            if len(desc) >= 20:  # 降低到20字
                shot_score += 1
            else:
                errors.append(f"storyboard shot {i+1} description too short (min 20 characters)")

            if any(keyword in desc for keyword in shot_keywords):
                shot_score += 1
            else:
                errors.append(f"storyboard shot {i+1} lacks shot type")

            if any(keyword in desc for keyword in action_keywords):
                shot_score += 1
            else:
                errors.append(f"storyboard shot {i+1} lacks action description")

            # 扩展验证（可选，每项0.5分）
            if any(keyword in desc for keyword in angle_keywords):
                shot_score += 0.5

            if any(keyword in desc for keyword in ["字幕", "同期声", "音效"]):
                shot_score += 0.5

            if any(keyword in desc for keyword in prop_keywords):
                shot_score += 0.5

            if any(keyword in desc for keyword in light_keywords):
                shot_score += 0.5

            total_score += shot_score

        quality_score = total_score / max_score if max_score > 0 else 0.0

        # 如果评分低于60%，标记为失败
        if quality_score < 0.6:
            storyboard_failed = True
            errors.append(f"storyboard quality score too low: {quality_score:.2f} (min 0.60)")

    # ... 其他验证 ...

    return errors, storyboard_failed, quality_score
```

### 步骤3：创建Fallback池

**文件**：`backend/app/services/ai_service.py`

**修改内容**：
1. 创建 `FALLBACK_POOL` 常量，包含20个不同的fallback内容

2. 实现 `_select_fallback()` 函数：
   - 基于时间戳或任务ID选择fallback
   - 记录使用历史
   - 智能匹配意图和平台

**具体实现**：
```python
FALLBACK_POOL = [
    # Fallback 1: 收纳整理场景
    {
        "hook_text": "袜子乱放真的会拖慢出门",
        "storyboard": [...],
        "script_text": "...",
        "title": "袜子抽屉不乱了｜出门30秒找到一双 #收纳 #袜子搭配",
        "comment_template": "你们袜子最头疼的是滑跟、起球，还是颜色太多不好搭？评论区说下场景，我整理一版清单。",
        "why_it_works": "用真实出门场景切入，先提供收纳和搭配价值，再用低压评论承接需求。",
        "tags": ["收纳", "整理", "引流"],
        "platforms": ["抖音", "小红书"]
    },
    # Fallback 2: 对比测评场景
    {
        "hook_text": "新旧袜子对比，差距太明显了",
        "storyboard": [...],
        "script_text": "...",
        "title": "袜子穿多久该换？对比图告诉你 #测评 #袜子",
        "comment_template": "你们袜子一般穿多久？评论区说下，我整理个更换周期参考。",
        "why_it_works": "用对比视觉冲击，提供实用判断标准，引导分享经验。",
        "tags": ["测评", "对比", "成交"],
        "platforms": ["抖音", "小红书"]
    },
    # ... 继续添加到20个 ...
]

# 使用历史记录（简单的内存缓存）
_fallback_usage_history = []

def _select_fallback(
    intent_name: str,
    platform_name: str,
    fallback_pool: list[dict] = FALLBACK_POOL
) -> dict:
    """智能选择fallback内容.

    策略：
    1. 根据意图和平台过滤候选fallback
    2. 优先选择最近未使用的fallback
    3. 记录使用历史
    """
    import time

    # 过滤候选fallback
    candidates = []
    for fb in fallback_pool:
        # 匹配意图
        intent_match = any(tag in intent_name for tag in fb.get("tags", []))
        # 匹配平台
        platform_match = any(platform in platform_name for platform in fb.get("platforms", []))

        if intent_match or platform_match:
            candidates.append(fb)

    # 如果没有匹配的，使用全部fallback
    if not candidates:
        candidates = fallback_pool

    # 优先选择最近未使用的fallback
    current_time = time.time()
    for fb in candidates:
        if fb not in _fallback_usage_history[-10:]:  # 避免最近10次使用过的
            _fallback_usage_history.append(fb)
            # 保持历史记录在合理范围
            if len(_fallback_usage_history) > 100:
                _fallback_usage_history.pop(0)
            return fb.copy()

    # 如果所有fallback都最近用过，随机选择一个
    import random
    selected = random.choice(candidates)
    _fallback_usage_history.append(selected)
    return selected.copy()
```

### 步骤4：更新generate_content函数

**文件**：`backend/app/services/ai_service.py`

**修改内容**：
1. 使用 `_select_fallback()` 替代 `_safe_fallback()`
2. 根据评分决定是否使用fallback
3. 实现混合fallback策略

**具体修改**：
```python
async def generate_content(
    intent_name: str,
    intent_description: str,
    platform_name: str,
    hook_type: str,
    emotion_structure: dict,
    conversion_structure: dict,
    optimization_prompt: str | None = None,
    fallback_content: dict | None = None,
    task_type: str = "video",
    conversion_scripts: dict | None = None,
    market_insights: dict | None = None,
) -> tuple[dict, bool]:
    # ... 构建提示词 ...

    for attempt in range(2):
        try:
            # ... 调用AI ...

            data = json.loads(text.strip())
            errors, storyboard_failed, quality_score = _validate_output(data)

            if errors:
                # 如果评分 >= 60%，只修复错误部分
                if quality_score >= 0.6:
                    logger.warning(f"AI output has issues but quality score acceptable ({quality_score:.2f}), using hybrid fallback")
                    fallback = _select_fallback(intent_name, platform_name)

                    # 只替换失败的部分
                    if storyboard_failed:
                        data["storyboard"] = fallback["storyboard"]

                    return data, False

                # 如果评分 < 60%，使用完整fallback
                logger.warning(f"AI output quality too low ({quality_score:.2f}), using full fallback")
                if attempt == 0:
                    continue
                return _select_fallback(intent_name, platform_name), True

            # 验证通过
            return data, False

        except Exception as e:
            # ... 异常处理 ...

    # 所有尝试失败，使用智能选择的fallback
    logger.warning("All AI attempts failed, using smart fallback")
    return _select_fallback(intent_name, platform_name), True
```

### 步骤5：更新文档

**文件**：`docs/prompts.md`

**修改内容**：
1. 更新分镜脚本详细度标准（8维度 → 5维度）
2. 增加更多示例
3. 说明Fallback池机制

---

## 四、预期效果

### 4.1 成功率提升

**当前**：估计成功率 < 20%（基于用户反馈"一致使用fallback"）

**优化后**：
- 简化提示词：成功率提升至 **40-50%**
- 放宽验证：成功率提升至 **60-70%**
- 增加示例：成功率提升至 **70-80%**

### 4.2 用户体验改善

**当前**：每次都看到相同的fallback内容

**优化后**：
- 20个不同的fallback，轮换使用
- 智能匹配意图和平台
- 即使失败也能看到多样化的内容

### 4.3 内容质量

**当前**：要么完全成功，要么完全fallback

**优化后**：
- 评分机制允许部分成功
- 混合fallback保留AI生成的有效部分
- 内容详细度更可控

---

## 五、风险与缓解

### 5.1 简化导致质量下降

**风险**：5维度可能不足以指导拍摄

**缓解**：
- 5维度已包含核心信息（景别+角度+动作+焦点+声音）
- 运镜、灯光、道具可在描述中自然提及
- 如果LLM能力强，仍会生成完整8维度内容

### 5.2 Fallback池维护成本

**风险**：20个fallback需要持续维护

**缓解**：
- 初期创建20个高质量fallback
- 后续根据用户反馈逐步优化
- 可以从现有成功内容中提取fallback

### 5.3 评分机制调优

**风险**：60%阈值可能不合适

**缓解**：
- 初期设置60%，后续根据数据调整
- 记录评分分布，优化阈值
- 可以针对不同意图设置不同阈值

---

## 六、验证步骤

### 6.1 单元测试

**文件**：`backend/tests/test_ai_service.py`

**测试内容**：
1. 测试简化后的验证逻辑
2. 测试评分机制
3. 测试Fallback选择逻辑
4. 测试混合Fallback策略

### 6.2 集成测试

**测试内容**：
1. 生成10个不同意图的内容，统计成功率
2. 验证Fallback轮换机制
3. 验证内容质量评分分布

### 6.3 手动验证

**验证内容**：
1. 检查生成的分镜脚本是否符合5维度要求
2. 检查Fallback内容是否多样化
3. 检查用户体验是否改善

---

## 七、后续优化方向

1. **动态调整阈值**：根据历史数据自动调整评分阈值
2. **Fallback自动生成**：从成功内容中自动提取fallback
3. **多模型对比**：测试不同模型（GPT-4、Claude、DeepSeek）的成功率
4. **用户反馈闭环**：收集用户对生成内容的反馈，持续优化

---

## 八、实施优先级

### 高优先级（立即实施）
1. ✅ 简化分镜脚本提示词（步骤1）
2. ✅ 放宽验证逻辑（步骤2）
3. ✅ 创建Fallback池（步骤3）

### 中优先级（后续实施）
4. ⏳ 更新文档（步骤5）
5. ⏳ 增加单元测试（步骤6.1）

### 低优先级（可选实施）
6. ⏸ 集成测试（步骤6.2）
7. ⏸ 后续优化方向

---

**计划创建时间**：2026-06-04
**预计实施时间**：2-3小时
**预期成功率提升**：从 <20% 提升至 70-80%
