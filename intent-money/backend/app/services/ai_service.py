import json
import logging
import time

from openai import APIError, APITimeoutError, AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

BANNED_PHRASES = [
    "最便宜", "全网最低", "最低价", "史上最低", "绝对",
    "月入过万", "日赚千元", "轻松赚钱", "躺赚",
    "治疗", "治愈", "疗效", "药效", "处方",
]

HARD_SELL_PHRASES = [
    "扣1", "扣 1", "私信我", "私信【", "秒发", "秒回", "发你链接",
    "前10名", "前30名", "前50名", "隐藏福利", "手慢无",
    "今天下单", "限时优惠", "直接下单", "小黄车", "不是广",
    "闭眼入", "冲就完了", "质感完全不输大牌",
]

PRODUCT_DETAIL_KEYWORDS = [
    "纯棉", "透气", "吸汗", "弹性", "耐磨", "不起球", "不掉色",
    "软", "舒服", "舒适", "亲肤", "厚度", "季节", "搭配", "场景",
    "袜口", "脚跟", "滑跟", "勒脚", "鞋型", "通勤", "运动", "居家",
    "收纳", "洗后", "颜色", "材质",
]

INTERACTION_KEYWORDS = [
    "评论", "留言", "问", "你们", "你", "哪种", "哪个", "怎么",
    "清单", "收藏", "场景", "鞋型", "搭配", "整理", "分享",
]

TASK_OUTPUT_SCHEMA = {
    "hook_text": {"type": "string", "max_length": 30, "required": True},
    "storyboard": {"type": "list", "min_items": 3, "max_items": 5, "required": True},
    "script_text": {"type": "string", "min_length": 50, "max_length": 300, "required": True},
    "title": {"type": "string", "max_length": 50, "required": True},
    "comment_template": {"type": "string", "required": True},
    "why_it_works": {"type": "string", "required": True},
}

SAFE_FALLBACK_CONTENT = {
    "hook_text": "袜子乱放真的会拖慢出门",
    "storyboard": [
        {"shot": 1, "description": "近景：早上出门翻抽屉找袜子，连续拿出两只不同款，展示真实混乱场景", "duration": "3s", "label": "痛点开场"},
        {"shot": 2, "description": "特写：把起球、袜口松、脚跟磨薄的旧袜子单独挑出来，说明淘汰标准", "duration": "5s", "label": "问题证据"},
        {"shot": 3, "description": "中景：把通勤袜、运动袜、居家袜分成三格，并说明每类适合的鞋型", "duration": "8s", "label": "方法拆解"},
        {"shot": 4, "description": "特写：上脚展示袜口高度、脚跟贴合和鞋内不滑的细节", "duration": "7s", "label": "使用体验"},
        {"shot": 5, "description": "近景：展示整理后的抽屉和当天穿搭，结尾抛出互动问题", "duration": "5s", "label": "互动收尾"},
    ],
    "script_text": "以前我的袜子都是团成一堆，早上越急越找不到。后来我改成按场景分三格：通勤袜放最顺手的位置，运动袜单独一格，居家袜放后排。袜口松了、脚跟磨薄、穿着滑跟的就直接淘汰。这样整理后，黑白灰基础款够日常，彩色款只留真正会搭的，出门不用临时乱翻。",
    "title": "袜子抽屉不乱了｜出门30秒找到一双 #收纳 #袜子搭配",
    "comment_template": "你们袜子最头疼的是滑跟、起球，还是颜色太多不好搭？评论区说下场景，我整理一版清单。",
    "why_it_works": "用真实出门场景切入，先提供收纳和搭配价值，再用低压评论承接需求。",
}


def _build_prompt(
    intent_name: str,
    intent_description: str,
    platform_name: str,
    hook_type: str,
    emotion_structure: dict,
    conversion_structure: dict,
    optimization_prompt: str | None = None,
    task_type: str = "video",
    conversion_scripts: dict | None = None,
    market_insights: dict | None = None,
) -> str:
    _INTENT_TASK_MAP = {
        "引流拿客户": "生成一条以自然获客为目标的内容任务：先让用户愿意看、愿意评论，再产生咨询兴趣",
        "成交赚钱": "生成一条以促成购买决策为目标的内容任务：用真实细节和适用场景解释为什么值得买",
        "裂变招募分销": "生成一条以招募分销商为目标的内容任务：讲清楚适合人群、真实门槛、时间成本和限制",
        "IP长期增长": "生成一条以打造个人品牌为目标的内容任务：输出稳定观点、经验和账号记忆点",
    }
    _INTENT_AUDIENCE_MAP = {
        "引流拿客户": "对袜子有需求的普通消费者，尤其是注重性价比和实用性的群体",
        "成交赚钱": "已有购买意向但犹豫不决的消费者，需要最后的推动力促使其下单",
        "裂变招募分销": "想找副业赚钱的人群，尤其是宝妈、学生、自由职业者",
        "IP长期增长": "对袜子行业感兴趣的关注者，希望获得专业建议和生活方式灵感",
    }
    _INTENT_WHY_MAP = {
        "引流拿客户": "一句话说明为什么这条内容能吸引流量",
        "成交赚钱": "一句话说明为什么这条内容能促成购买",
        "裂变招募分销": "一句话说明为什么这条内容能吸引人加入分销",
        "IP长期增长": "一句话说明为什么这条内容能增强个人品牌影响力",
    }
    _INTENT_STRATEGY_MAP = {
        "引流拿客户": "具体痛点 -> 真实场景 -> 解决方法 -> 评论讨论。不要直接卖货，优先让用户说出自己的场景。",
        "成交赚钱": "购买犹豫 -> 细节证据 -> 使用体验 -> 适合/不适合人群 -> 温和行动。必须写出真实限制。",
        "裂变招募分销": "个人场景 -> 做法拆解 -> 时间成本 -> 风险和限制 -> 评论答疑。禁止夸大收益和零风险承诺。",
        "IP长期增长": "观点/经验 -> 细节解释 -> 示例 -> 系列预告/关注理由。优先建立专业和信任，不强卖。",
    }

    task_desc = _INTENT_TASK_MAP.get(intent_name, f"基于以下内容结构模板，生成一条完整的{'短视频' if task_type == 'video' else '图文笔记'}内容任务。")
    audience = _INTENT_AUDIENCE_MAP.get(intent_name, "对袜子有需求的普通消费者")
    why_desc = _INTENT_WHY_MAP.get(intent_name, "一句话说明为什么这条内容有效")
    intent_strategy = _INTENT_STRATEGY_MAP.get(intent_name, "具体场景 -> 实用信息 -> 真实体验 -> 温和互动。")
    content_format = "图文笔记（图片+文案，无需拍摄视频）" if task_type == "image" else "短视频（需要拍摄）"
    is_douyin = "抖音" in platform_name
    is_xhs = "小红书" in platform_name

    parts = [
        "你是一名袜子类目内容策划专家，擅长为抖音和小红书生成真实、平台原生、可执行的内容任务。",
        "你的目标不是写硬广，而是生成一条用户愿意看完、愿意收藏/评论，并自然产生购买兴趣的内容。",
        "",
        "## 基础信息",
        f"- 任务：{task_desc if task_type == 'video' else task_desc.replace('短视频', '图文笔记')}",
        f"- 用户意图：{intent_name}：{intent_description}",
        f"- 发布平台：{platform_name}",
        "- 产品类目：袜子（分销模式）",
        f"- 内容形式：{content_format}",
        f"- 目标人群：{audience}",
        "",
        "## 内容结构参考",
        f"- 钩子类型：{hook_type}",
        f"- 情绪结构：{json.dumps(emotion_structure, ensure_ascii=False)}",
        f"- 转化结构：{json.dumps(conversion_structure, ensure_ascii=False)}",
        f"- 当前意图写法：{intent_strategy}",
        "",
        "## 总原则",
        "1. 内容必须像真实用户/真实创作者发布，不要像广告脚本。",
        "2. 先解决用户问题，再自然出现产品；不要一上来卖货。",
        "3. 必须包含具体场景、具体细节、具体判断标准，避免空泛夸奖。",
        "4. 不要使用「姐妹们疯狂问」「室友惊呆了」「真的不是广」「质感完全不输大牌」「闭眼入」「冲」「秒发链接」等模板化表达。",
        "5. 不要使用夸张承诺：全网最低、最便宜、绝对、包治、月入过万、轻松赚钱、0风险、躺赚。",
        "6. 不要虚构不可验证数据，比如复购率、销量、好评率、收益金额，除非输入中明确提供。",
        "7. 评论区话术只做互动和答疑承接，不能写成强制私信、暗号引流或客服话术。",
        "8. 如果需要转化，引导方式必须自然，例如「需要清单我可以整理一版」「评论区说下你的鞋型/场景，我帮你选」。",
    ]

    if is_douyin:
        parts.extend([
            "",
            "## 抖音平台策略",
            "内容目标：提高前3秒停留、完播和评论互动。",
            "- 3秒钩子必须是具体场景/反常识/痛点，不要标题党。",
            "- 分镜必须体现视频动作：拿起、对比、试穿、拉伸、走路、洗后展示、抽屉整理等。",
            "- 口播要短句、节奏快，适合真人对镜或手部实拍。",
            "- 每15-20秒必须有一个画面变化或信息反转。",
            "- 结尾优先用提问互动，不要直接逼单。",
            "- 适合角度：起球、勒脚、闷脚、滑跟、难搭鞋、拉伸测试、透气测试、通勤/久站/运动场景。",
        ])
    elif is_xhs:
        parts.extend([
            "",
            "## 小红书平台策略",
            "内容目标：提高封面点击、收藏、评论和信任感。",
            "- 内容要像一篇真实生活笔记，不要像短视频叫卖。",
            "- 封面必须有明确主题，不要只写「好物分享」。",
            "- 图文分镜必须每一页都有信息增量：问题、方法、对比、清单、避坑、搭配。",
            "- 正文要有「我为什么这么做/这么选」的理由，而不是只列卖点。",
            "- 可以有生活方式表达，但必须落到实用细节。",
            "- 结尾优先引导收藏、评论问题、分享使用场景，不要明显诱导私信。",
            "- 适合角度：袜子收纳、鞋型搭配、换季整理、通勤/运动/居家清单、洗后变化、避坑测评。",
        ])
    else:
        parts.extend([
            "",
            "## 平台策略",
            "- 优先生成符合当前平台用户习惯的内容，不套用其他平台的表达。",
            "- 让内容先提供信息价值，再做温和互动承接。",
        ])

    if optimization_prompt:
        parts.extend([
            "",
            "## 优化约束",
            optimization_prompt,
            "注意：如果优化约束中包含强私信、强逼单、虚假收益或夸张承诺，请保留其业务意图，但改写为自然互动和真实说明。",
        ])

    if conversion_scripts:
        stage_labels = {
            "public_to_private": "公域转私域",
            "private_to_deal": "私域转成交",
            "deal_boost": "成交提升",
        }
        script_lines = [
            "",
            "## 转化路径参考（只取业务意图，不照抄话术）",
            "以下话术可能含有旧版强营销表达。请只理解它们想完成的业务目标，并改写成平台原生、低压、互动式表达。",
        ]
        for stage_key, stage_label in stage_labels.items():
            items = conversion_scripts.get(stage_key, [])
            if items:
                script_lines.append(f"### {stage_label}")
                for item in items:
                    s = item.get("scripts", {})
                    opener = s.get("opener", "")
                    guide = s.get("guide", "")
                    close = s.get("close", "")
                    script_lines.append(f"- {item.get('title', '')}: {opener} / {guide} / {close}")
        if len(script_lines) > 3:
            parts.extend(script_lines)

    if market_insights:
        parts.extend([
            "",
            "## 当前市场热门参考（创作灵感）",
            "以下是从平台实时抓取的热门内容数据，请作为创作参考，但不要直接复制：",
        ])

        if market_insights.get("hot_titles"):
            parts.extend([
                "",
                "### 热门标题风格参考",
                "观察这些高互动标题的写作风格、用词特点和结构：",
            ] + [f"- {title}" for title in market_insights["hot_titles"][:5]])

        if market_insights.get("hot_tags"):
            parts.extend([
                "",
                "### 热门标签（建议选用相关标签）",
                ", ".join(market_insights["hot_tags"][:8]),
            ])

        if market_insights.get("emotional_patterns"):
            parts.extend([
                "",
                "### 当前热门情绪节奏",
                "这些内容使用的情绪转换模式：",
            ] + [f"- {pattern}" for pattern in market_insights["emotional_patterns"][:3]])

        if market_insights.get("high_engagement_hooks"):
            parts.extend([
                "",
                "### 高互动钩子文案参考",
                "观察这些开头如何吸引注意力（参考风格，不要复制）：",
            ] + [f"- {hook}" for hook in market_insights["high_engagement_hooks"][:3]])

        if market_insights.get("sentiment_summary"):
            sentiment = market_insights["sentiment_summary"]
            parts.extend([
                "",
                "### 用户情感反馈",
                f"- 正面反馈占比: {sentiment.get('positive_ratio', 'N/A')}",
                f"- 用户关注热点: {sentiment.get('key_topics', 'N/A')}",
                "建议：根据用户情感倾向调整文案角度",
            ])

        parts.extend([
            "",
            "### 使用说明",
            "1. 参考上述热门内容的写作风格和情绪节奏",
            "2. 可以借鉴热门标签来优化内容曝光",
            "3. 根据用户情感反馈调整内容角度",
            "4. 保持原创性，不要直接复制或改写抓取的内容",
            "5. 结合产品特点和目标人群进行创作",
        ])

    if task_type == "image":
        storyboard_example = [
            {"shot": 1, "description": "封面：打开抽屉前后对比，左边袜子团成一堆，右边按通勤/运动/居家分格，封面字写“袜子抽屉30秒找到一双”", "duration": "封面", "label": "点击理由"},
            {"shot": 2, "description": "内页1：展示错误收法，袜子卷成球导致袜口变松、同色难找、早上翻乱", "duration": "内页1", "label": "痛点说明"},
            {"shot": 3, "description": "内页2：按场景分三格，通勤短袜、运动厚底袜、居家袜分别放置，并标注适合鞋型", "duration": "内页2", "label": "方法拆解"},
            {"shot": 4, "description": "内页3：展示乐福鞋、运动鞋、拖鞋分别搭配的袜长和颜色，突出好找好搭", "duration": "内页3", "label": "搭配价值"},
            {"shot": 5, "description": "尾图：列出袜子整理检查清单：淘汰变硬/松口/起球款，保留基础色和高频场景款", "duration": "尾图", "label": "收藏价值"}
        ]
    else:
        storyboard_example = [
            {"shot": 1, "description": "近景：早上出门翻抽屉找袜子，连续拿出两只不同款，直接说“袜子乱放真的会拖慢出门”", "duration": "3s", "label": "痛点开场"},
            {"shot": 2, "description": "特写：展示起球、袜口松、脚跟磨薄的旧袜子，说明哪些状态该淘汰", "duration": "5s", "label": "问题证据"},
            {"shot": 3, "description": "中景：把通勤袜、运动袜、居家袜分成三堆，边整理边说每类适合什么鞋", "duration": "8s", "label": "方法拆解"},
            {"shot": 4, "description": "特写：上脚走两步，展示袜口高度、脚跟贴合和鞋内不滑的细节", "duration": "7s", "label": "使用体验"},
            {"shot": 5, "description": "近景：整理好的抽屉和当天穿搭，结尾提问“你们最头疼的是滑跟还是起球？”", "duration": "5s", "label": "互动收尾"}
        ]

    parts.extend([
        "",
        "## 内容详细度要求（必须满足）",
        "### 分镜脚本要求（每个分镜必须包含）：",
        "- 具体的画面内容描述，包含人物动作、场景、物品细节",
        "- 清晰的展示重点，明确用户能看到什么",
        "- 图文笔记分镜需要说明图片类型（实拍/对比/特写/场景）",
        "- 短视频分镜需要说明镜头景别（近景/特写/中景/全景）",
        "",
        "### 口播文案要求（必须满足）：",
        "- 抖音写口播，小红书写笔记正文，表达都要像真实创作者。",
        "- 包含具体的产品/场景细节描述（材质、袜口、脚跟、鞋型、洗后、收纳、搭配、使用感受等）。",
        "- 有明确的信息递进：痛点或场景 -> 方法或证据 -> 体验或判断标准 -> 温和互动。",
        "- 字数控制在150-280字，信息密度适中。",
        "- 每部分内容对应分镜节奏，画面和语音同步",
        "",
        "### 标题要求：",
        "- 包含核心关键词、具体场景或利益点。",
        "- 搭配1-3个相关话题标签，不堆无关热词。",
        "- 长度控制在20-50字，符合平台推荐逻辑。",
        "",
        "### 评论区引导话术：",
        "- 优先提出互动问题，引导用户说出自己的鞋型、场景或困扰。",
        "- 可以承接清单、搭配建议、后续笔记，但不能写“私信关键词秒发”“扣1”“链接已发”。",
        "- 语气像真实作者补充说明，不像客服导购。",
        "",
        "## 禁用表达",
        "- 不得出现「最便宜」「全网最低」等绝对化用语",
        "- 不得出现医疗功效承诺",
        "- 不得出现虚假收益承诺",
        "- 不得出现「月入过万」等夸大宣传",
        "- 不得出现「扣1」「私信【关键词】」「秒发」「前X名」「隐藏福利」「手慢无」「小黄车」等强营销话术",
        "",
        "## 输出格式（严格 JSON）",
        "```json",
        json.dumps({
            "hook_text": "3秒钩子文案，15-25字，具体、有场景，不夸张",
            "storyboard": storyboard_example,
            "script_text": "完整正文或口播，150-280字。抖音写口播，小红书写笔记正文。必须自然、有细节、有真实使用场景",
            "title": "平台标题，20-50字，含1-3个相关话题标签",
            "comment_template": "评论区置顶/首评话术，以互动、补充、答疑为主，不得使用私信暗号、秒发链接、前X名福利",
            "why_it_works": why_desc
        }, ensure_ascii=False, indent=2),
        "```",
    ])

    return "\n".join(parts)


def _collect_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_collect_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_collect_text(item) for item in value)
    return ""


def _validate_output(data: dict) -> list[str]:
    errors = []

    if not data.get("hook_text") or len(data["hook_text"]) > 30:
        errors.append("hook_text invalid")

    storyboard = data.get("storyboard", [])
    if not isinstance(storyboard, list) or len(storyboard) < 3 or len(storyboard) > 5:
        errors.append("storyboard invalid (must have 3-5 shots)")
    
    # 检查分镜详细度：每个分镜描述长度不少于15字
    for i, shot in enumerate(storyboard):
        desc = shot.get("description", "")
        if len(desc) < 15:
            errors.append(f"storyboard shot {i+1} description too short (min 15 characters)")

    script = data.get("script_text", "")
    if not script or len(script) < 100 or len(script) > 350:
        errors.append("script_text invalid (must be 100-350 characters)")
    
    # 检查文案详细度：是否包含至少2个产品或使用场景相关细节
    detail_count = sum(1 for keyword in PRODUCT_DETAIL_KEYWORDS if keyword in script)
    if detail_count < 2:
        errors.append("script_text lacks product details (must include at least 2 product features)")

    title = data.get("title", "")
    if not title or len(title) < 10 or len(title) > 60:
        errors.append("title invalid (must be 10-60 characters)")
    
    # 检查标题是否包含话题标签
    if "#" not in title:
        errors.append("title must include at least 1 hashtag")

    comment = data.get("comment_template", "")
    if not comment or len(comment) < 20 or len(comment) > 150:
        errors.append("comment_template invalid (must be 20-150 characters)")
    
    # 检查评论是否有互动引导，但不把强私信/购买暗号当成有效互动
    has_interaction = any(keyword in comment for keyword in INTERACTION_KEYWORDS)
    if not has_interaction:
        errors.append("comment_template must include low-pressure interaction guide")

    if not data.get("why_it_works"):
        errors.append("why_it_works invalid")

    all_text = _collect_text(data)
    for phrase in BANNED_PHRASES + HARD_SELL_PHRASES:
        if phrase in all_text:
            errors.append(f"banned phrase: {phrase}")

    if "袜子" not in all_text and "袜" not in all_text:
        errors.append("missing product keyword")

    return errors


def _safe_fallback(fallback_content: dict | None) -> dict:
    if fallback_content and not _validate_output(fallback_content):
        return fallback_content
    return SAFE_FALLBACK_CONTENT.copy()


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
    prompt = _build_prompt(
        intent_name=intent_name,
        intent_description=intent_description,
        platform_name=platform_name,
        hook_type=hook_type,
        emotion_structure=emotion_structure,
        conversion_structure=conversion_structure,
        optimization_prompt=optimization_prompt,
        task_type=task_type,
        conversion_scripts=conversion_scripts,
        market_insights=market_insights,
    )

    if not settings.AI_API_KEY:
        logger.warning("AI_API_KEY not set, using fallback")
        return _safe_fallback(fallback_content), True

    client = AsyncOpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
    )

    for attempt in range(2):
        start_time = time.time()
        try:
            response = await client.chat.completions.create(
                model=settings.AI_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                timeout=10.0,
            )

            elapsed = time.time() - start_time

            text = response.choices[0].message.content or ""

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())

            errors = _validate_output(data)
            if errors:
                logger.warning(f"AI output validation failed (attempt {attempt + 1}): {errors}")
                if attempt == 0:
                    continue
                return _safe_fallback(fallback_content), True

            usage = response.usage
            logger.info(
                f"AI generation succeeded in {elapsed:.2f}s, "
                f"input_tokens={usage.prompt_tokens if usage else 0}, "
                f"output_tokens={usage.completion_tokens if usage else 0}"
            )
            return data, False

        except APITimeoutError:
            logger.warning(f"AI timeout (attempt {attempt + 1})")
            if attempt == 0:
                continue
        except APIError as e:
            logger.error(f"AI API error: {e}")
            if attempt == 0:
                continue
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"AI output parse error (attempt {attempt + 1}): {e}")
            if attempt == 0:
                continue

    logger.warning("All AI attempts failed, using fallback")
    return _safe_fallback(fallback_content), True
