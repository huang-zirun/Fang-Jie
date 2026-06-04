import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.content_structure import ContentStructure
from app.models.conversion_path import ConversionPath
from app.models.intent import Intent
from app.models.optimization_rule import OptimizationRule
from app.models.platform import Platform

INTENT_ID_TRAFFIC = uuid.UUID("00000000-0000-0000-0000-000000000001")
INTENT_ID_SALE = uuid.UUID("00000000-0000-0000-0000-000000000002")
INTENT_ID_REFERRAL = uuid.UUID("00000000-0000-0000-0000-000000000003")
INTENT_ID_IP = uuid.UUID("00000000-0000-0000-0000-000000000004")

PLATFORM_ID_DOUYIN = uuid.UUID("10000000-0000-0000-0000-000000000001")
PLATFORM_ID_XIAOHONGSHU = uuid.UUID("10000000-0000-0000-0000-000000000002")


async def seed_intents(db: AsyncSession):
    result = await db.execute(select(Intent))
    if result.scalars().first():
        return
    intents = [
        Intent(id=INTENT_ID_TRAFFIC, name="引流拿客户", description="我想让更多人看到我", sort_order=1, is_active=True),
        Intent(id=INTENT_ID_SALE, name="成交赚钱", description="我想卖出更多袜子", sort_order=2, is_active=True),
        Intent(id=INTENT_ID_REFERRAL, name="裂变招募分销", description="我想让别人帮我赚钱", sort_order=3, is_active=True),
        Intent(id=INTENT_ID_IP, name="IP长期增长", description="我想做账号做品牌", sort_order=4, is_active=True),
    ]
    db.add_all(intents)
    await db.commit()


async def seed_platforms(db: AsyncSession):
    result = await db.execute(select(Platform))
    if result.scalars().first():
        return
    platforms = [
        Platform(id=PLATFORM_ID_DOUYIN, name="抖音（短视频）", is_active=True),
        Platform(id=PLATFORM_ID_XIAOHONGSHU, name="小红书（图文）", is_active=True),
    ]
    db.add_all(platforms)
    await db.commit()


async def seed_optimization_rules(db: AsyncSession):
    result = await db.execute(select(OptimizationRule))
    if result.scalars().first():
        return
    rules = [
        OptimizationRule(
            name="钩子极弱",
            problem_type="hook_weak",
            condition_expr={"field": "play_count", "operator": "lt", "value": 200, "label": "播放量低于200"},
            optimization_direction="必须更换钩子类型",
            optimization_prompt="上条内容钩子吸引力极弱，请使用反常识型或痛点型钩子，前3秒必须制造强烈反差或悬念",
            priority=100,
            is_active=True,
        ),
        OptimizationRule(
            name="标题/选题弱",
            problem_type="title_weak",
            condition_expr={"field": "play_count", "operator": "lt", "value": 500, "label": "播放量低于500"},
            optimization_direction="换钩子类型，优化标题写法",
            optimization_prompt="上条内容标题曝光不足，请使用数字+痛点组合标题，加入2个热门话题标签",
            priority=50,
            is_active=True,
        ),
        OptimizationRule(
            name="互动引导弱",
            problem_type="interaction_weak",
            condition_expr={"and": [
                {"field": "play_count", "operator": "gte", "value": 500},
                {"field": "comment_count", "operator": "lt", "value": 5},
            ], "label": "播放≥500但评论<5"},
            optimization_direction="强化评论区话术，增加互动钩子",
            optimization_prompt="上条内容互动率低，请在口播结尾增加提问式互动引导，评论区话术增加话题讨论",
            priority=30,
            is_active=True,
        ),
        OptimizationRule(
            name="转化话术弱",
            problem_type="conversion_weak",
            condition_expr={"and": [
                {"field": "comment_count", "operator": "gte", "value": 5},
                {"field": "message_count", "operator": "eq", "value": 0},
            ], "label": "评论≥5但私信=0"},
            optimization_direction="优化评论区引导私信的话术",
            optimization_prompt="上条内容私信转化低，请在评论区话术中增加具体利益点（如'私信我领XX'），口播中增加行动指令",
            priority=20,
            is_active=True,
        ),
        OptimizationRule(
            name="表现正常",
            problem_type="normal",
            condition_expr={"and": [
                {"field": "play_count", "operator": "gte", "value": 500},
                {"field": "comment_count", "operator": "gte", "value": 5},
                {"field": "message_count", "operator": "gte", "value": 1},
            ], "label": "播放≥500且评论≥5且私信≥1"},
            optimization_direction="继续当前策略，微调优化",
            optimization_prompt="上条内容表现良好，请在此基础上微调，尝试不同的情绪结构变体",
            priority=10,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_SALE,
            name="成交话术弱",
            problem_type="sale_weak",
            condition_expr={"and": [
                {"field": "play_count", "operator": "gte", "value": 500},
                {"field": "message_count", "operator": "eq", "value": 0},
            ], "label": "播放≥500但私信=0"},
            optimization_direction="成交话术弱，需要优化促单话术",
            optimization_prompt="上条内容有曝光但无私信转化，说明促单话术不够有力。请在口播中增加限时优惠话术，强化紧迫感，评论区增加'私信领专属优惠'引导，口播结尾增加明确行动指令如'现在私信我，今天下单额外送2双袜子'",
            priority=90,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_SALE,
            name="价格敏感度高",
            problem_type="price_sensitive",
            condition_expr={"and": [
                {"field": "comment_count", "operator": "gte", "value": 5},
                {"field": "message_count", "operator": "eq", "value": 0},
            ], "label": "评论≥5但私信=0"},
            optimization_direction="价格敏感度高，需要增加价值感话术",
            optimization_prompt="上条内容有评论互动但无私信，用户可能在犹豫价格。请增加价值感话术：拆解单双价格、强调品质对比、增加赠品信息。例如'一双不到8块，比奶茶还便宜，但能穿3个月不起球'，评论区引导'私信我领买5送2的隐藏福利'",
            priority=80,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_SALE,
            name="信任感不足",
            problem_type="trust_weak",
            condition_expr={"field": "play_count", "operator": "lt", "value": 500, "label": "播放量低于500"},
            optimization_direction="信任感不足，需要增加背书和真实体验",
            optimization_prompt="上条内容曝光低，信任感不足。请增加真实体验背书：展示自己长期穿着的袜子对比、增加客户反馈截图、使用场景实拍。口播中加入'我自己穿了半年'、'复购率超过60%'等信任话术，让用户感受到真实可靠",
            priority=70,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_REFERRAL,
            name="招募吸引力弱",
            problem_type="recruit_weak",
            condition_expr={"field": "play_count", "operator": "lt", "value": 500, "label": "播放量低于500"},
            optimization_direction="招募吸引力弱，需要突出收益和低门槛",
            optimization_prompt="上条内容播放量低，招募吸引力不足。请在开头直接展示收益结果，如'上个月靠卖袜子多赚了3000块'，降低入门门槛描述，强调'0库存、0风险、一部手机就能做'，让用户觉得'我也能行'",
            priority=90,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_REFERRAL,
            name="入门门槛感知高",
            problem_type="barrier_high",
            condition_expr={"and": [
                {"field": "play_count", "operator": "gte", "value": 500},
                {"field": "comment_count", "operator": "lt", "value": 5},
            ], "label": "播放≥500但评论<5"},
            optimization_direction="入门门槛感知高，需要简化流程描述",
            optimization_prompt="上条内容有曝光但互动少，用户可能觉得做分销门槛高。请简化流程描述，用3步说清楚：第一步扫码注册、第二步选品转发、第三步坐等收益。强调'不用囤货、不用发货、不用售后'，让用户感觉简单易上手",
            priority=80,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_REFERRAL,
            name="留存转化弱",
            problem_type="retention_weak",
            condition_expr={"and": [
                {"field": "comment_count", "operator": "gte", "value": 5},
                {"field": "message_count", "operator": "eq", "value": 0},
            ], "label": "评论≥5但私信=0"},
            optimization_direction="留存转化弱，需要增加团队支持话术",
            optimization_prompt="上条内容有评论但无私信，用户感兴趣但还没行动。请增加团队支持话术：'加入后有专属导师1对1带教'、'团队群每天分享爆款袜子素材'、'新手首周平均出单3单'。评论区引导'私信我【加入】，我拉你进新手群'",
            priority=70,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_IP,
            name="人设辨识度低",
            problem_type="identity_weak",
            condition_expr={"field": "play_count", "operator": "lt", "value": 500, "label": "播放量低于500"},
            optimization_direction="人设辨识度低，需要强化个人标签",
            optimization_prompt="上条内容播放量低，人设辨识度不够。请强化个人标签，打造差异化记忆点：例如'袜子测评官'、'穿了1000双袜子的男人'。在口播开头固定使用个人slogan，视觉上增加统一元素（如固定背景、固定穿搭），让观众3秒内认出你",
            priority=90,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_IP,
            name="内容互动弱",
            problem_type="content_weak",
            condition_expr={"and": [
                {"field": "play_count", "operator": "gte", "value": 500},
                {"field": "comment_count", "operator": "lt", "value": 5},
            ], "label": "播放≥500但评论<5"},
            optimization_direction="内容互动弱，需要增加话题讨论引导",
            optimization_prompt="上条内容有曝光但互动少，需要增加话题讨论引导。请在口播中设置开放性问题，如'你们买袜子最看重什么？评论区告诉我'、'你觉得一双袜子多少钱合理？'。增加争议性观点引发讨论，评论区主动回复前5条评论带动氛围",
            priority=80,
            is_active=True,
        ),
        OptimizationRule(
            intent_id=INTENT_ID_IP,
            name="粉丝转化慢",
            problem_type="growth_slow",
            condition_expr={"and": [
                {"field": "comment_count", "operator": "gte", "value": 5},
                {"field": "message_count", "operator": "lt", "value": 2},
            ], "label": "评论≥5但私信<2"},
            optimization_direction="粉丝转化慢，需要增加关注引导",
            optimization_prompt="上条内容有互动但关注转化慢，需要增加关注引导。请在口播中加入'关注我，每天分享一个袜子行业秘密'、'关注我，下周教你如何挑选不起球的袜子'。设置系列内容钩子，让用户有持续关注的理由，评论区引导'关注+私信【袜子】领选袜指南'",
            priority=70,
            is_active=True,
        ),
    ]
    db.add_all(rules)
    await db.commit()


async def seed_content_structures(db: AsyncSession):
    result = await db.execute(select(ContentStructure))
    if result.scalars().first():
        return
    structures = [
        ContentStructure(
            intent_id=INTENT_ID_TRAFFIC,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="痛点型",
            emotion_structure={
                "type": "problem_agitation",
                "flow": "痛点唤醒 → 痛点放大 → 解决方案展示 → 利益点强调"
            },
            conversion_structure={
                "type": "comment_to_dm",
                "flow": "评论区引导 → 私信破冰 → 产品介绍 → 成交话术"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}",
            fallback_content={
                "hook_text": "你穿的袜子可能正在伤害你的脚",
                "storyboard": [
                    {"shot": 1, "description": "特写：劣质袜子起球、变形的画面", "duration": "3s"},
                    {"shot": 2, "description": "对比：展示我们的袜子弹性和质感", "duration": "5s"},
                    {"shot": 3, "description": "近景：穿袜子的脚部舒适展示", "duration": "5s"},
                    {"shot": 4, "description": "中景：手持多双袜子展示颜色选择", "duration": "5s"},
                    {"shot": 5, "description": "近景：手指指向评论区引导私信", "duration": "2s"}
                ],
                "script_text": "你知道吗？市面上80%的袜子穿一个月就变形起球。我之前也是这样，直到我发现了这款袜子。纯棉面料，弹力不勒脚，穿了三个月还像新的一样。关键是价格，5双只要39块9，比超市便宜一半。想了解的评论区扣1，我私信你。",
                "title": "袜子别乱买！这款穿了3个月还像新的 #好物推荐 #袜子推荐",
                "comment_template": "想要同款袜子的姐妹扣1，我私信发你链接！前10名还有额外优惠哦~",
                "why_it_works": "痛点切入+对比展示+低价诱惑+评论区引导私信，完整转化链路"
            },
            priority=100,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_TRAFFIC,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="反常识型",
            emotion_structure={
                "type": "curiosity_gap",
                "flow": "反常识陈述 → 好奇心激发 → 揭示真相 → 产品关联"
            },
            conversion_structure={
                "type": "comment_to_dm",
                "flow": "评论区提问 → 回答引导私信 → 产品详情"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}",
            fallback_content={
                "hook_text": "99%的人选袜子都看错了这一点",
                "storyboard": [
                    {"shot": 1, "description": "手持一双普通袜子，表情疑惑", "duration": "3s"},
                    {"shot": 2, "description": "快速切换到我们的产品，表情惊喜", "duration": "3s"},
                    {"shot": 3, "description": "特写：面料细节、弹力测试", "duration": "5s"},
                    {"shot": 4, "description": "中景：穿着走动展示舒适度", "duration": "5s"},
                    {"shot": 5, "description": "近景：手持价格标签+评论引导", "duration": "4s"}
                ],
                "script_text": "选袜子别只看颜色！关键看这三点：第一，是不是纯棉精梳；第二，罗口弹力够不够；第三，脚后跟有没有加厚。我卖的这个牌子全占齐了。而且一包5双，平均下来不到8块钱。想知道怎么分辨好坏？评论区留言'分辨'，我私聊教你。",
                "title": "选袜子别只看颜色！这3点才是关键 #生活技巧 #好物分享",
                "comment_template": "想学分辨袜子好坏的扣1，我私聊发你详细教程！还有内部价哦~",
                "why_it_works": "反常识标题制造好奇心 + 实用干货建立信任 + 评论区互动引导"
            },
            priority=90,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_TRAFFIC,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="身份识别型",
            emotion_structure={
                "type": "identity_resonance",
                "flow": "身份标签 → 共鸣场景 → 产品解决方案 → 行动号召"
            },
            conversion_structure={
                "type": "comment_to_dm",
                "flow": "身份认同 → 评论互动 → 私信转化"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}",
            fallback_content={
                "hook_text": "如果你是每天站8小时以上的女生，这条视频一定要看完",
                "storyboard": [
                    {"shot": 1, "description": "人物疲惫地揉脚的画面", "duration": "3s"},
                    {"shot": 2, "description": "换上我们的袜子后轻松的表情", "duration": "4s"},
                    {"shot": 3, "description": "特写：袜子的缓震和透气设计", "duration": "5s"},
                    {"shot": 4, "description": "多场景切换（上班/运动/居家）", "duration": "5s"},
                    {"shot": 5, "description": "手持多色展示 + 价格信息", "duration": "3s"}
                ],
                "script_text": "姐妹们，如果你也是那种一天要站很久的，听我说一句——一双好的袜子真的能救命。我之前脚底板疼得不行，换了这个牌子的袜子之后，真的舒服太多了。它是专门给久站人群设计的，足弓有支撑，脚跟有缓冲。一盒10双才59块9。同款在评论区，需要的自己拿。",
                "title": "久站党必看！这双袜子救了我的脚 #打工人必备 #好物推荐",
                "comment_template": "同款链接放评论区了！需要团购价的姐妹私信我'团购'哦~",
                "why_it_works": "精准人群定位+情感共鸣+实用价值+直接转化路径"
            },
            priority=80,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_TRAFFIC,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="场景切入型",
            emotion_structure={
                "type": "scenario_immersion",
                "flow": "具体场景 → 痛点触发 → 产品出现 → 效果展示"
            },
            conversion_structure={
                "type": "comment_to_dm",
                "flow": "场景共鸣 → 评论互动 → 私信成交"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}",
            fallback_content={
                "hook_text": "早上出门发现袜子又破了，我真的受够了",
                "storyboard": [
                    {"shot": 1, "description": "人物拿着破袜子的无奈表情", "duration": "3s"},
                    {"shot": 2, "description": "翻抽屉找袜子的混乱场景", "duration": "4s"},
                    {"shot": 3, "description": "拿出我们产品的包装展示", "duration": "3s"},
                    {"shot": 4, "description": "试穿后的满意表情+动作", "duration": "5s"},
                    {"shot": 5, "description": "整理好的袜子收纳画面", "duration": "3s"}
                ],
                "script_text": "谁懂啊家人们，每次出门找袜子都要翻半天，找到的还是破的。后来我干脆一次买了这个牌子的20双，颜色分类，质量还好，穿了半年都没怎么坏。算下来一双才3块多。真的，与其天天买烂袜子，不如一次性搞定。想要的评论区说一声。",
                "title": "终于不用每天早上翻箱倒柜找袜子了 #生活好物 #平价好物",
                "comment_template": "同款20组合装链接在主页，私信我'袜子'发你专属优惠码~",
                "why_it_works": "日常场景引发共鸣 + 痛点真实可感 + 性价比突出 + 低门槛行动"
            },
            priority=70,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_TRAFFIC,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="痛点型",
            emotion_structure={
                "type": "problem_agitation_xhs",
                "flow": "封面大字痛点 → 详细问题描述 → 对比图 → 解决方案"
            },
            conversion_structure={
                "type": "xhs_comment_guide",
                "flow": "笔记正文引导 → 评论区置顶 → 私信回复模板"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，注意小红书用户喜欢图文并茂、种草风格",
            fallback_content={
                "hook_text": "穿了一年的袜子居然还在穿？快看看你的脚",
                "storyboard": [
                    {"shot": 1, "description": "首图：文字'袜子穿多久该扔'配破旧袜子图", "duration": "封面"},
                    {"shot": 2, "description": "内页1：旧袜子vs新袜子对比实拍", "duration": "图文"},
                    {"shot": 3, "description": "内页2：材质细节特写（纯棉标识、弹性测试）", "duration": "图文"},
                    {"shot": 4, "description": "内页3：上脚效果实拍（不同角度）", "duration": "图文"},
                    {"shot": 5, "description": "尾图：价格+购买方式引导", "duration": "图文"}
                ],
                "script_text": "姐妹们！你们知道袜子最多能穿多久吗？答案是3个月！超过这个时间，细菌超标、弹性消失、还会磨脚。我自己之前就是那种一双袜子穿到破才换的类型，直到被闺蜜安利了这个牌子。\n\n✅ 纯棉精梳，亲肤不闷\n✅ 足弓支撑，久站不累\n✅ 一包5双，39块9包邮\n\n真的不是广，是真心觉得好用才分享。需要的姐妹评论区扣1，我私你链接～",
                "title": "🧦袜子穿多久该扔？90%的人都不知道｜附自用款推荐",
                "comment_template": "📌置顶：姐妹们问的链接在这里啦～\n需要的直接私信我【袜子】就行，我手把手教你怎么挑！\n前50名还有隐藏福利哦🎁",
                "why_it_works": "小红书爆款公式：封面吸睛+实用科普+真实测评+评论区引导"
            },
            priority=100,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_TRAFFIC,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="场景切入型",
            emotion_structure={
                "type": "lifestyle_vibe",
                "flow": "氛围感封面 → 生活化场景 → 产品自然植入 → 种草收尾"
            },
            conversion_structure={
                "type": "xhs_soft_sell",
                "flow": "软性种草 → 评论区答疑 → 自然引流"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，注重生活美学和种草感",
            fallback_content={
                "hook_text": "我的袜子收纳术让室友都惊呆了",
                "storyboard": [
                    {"shot": 1, "description": "封面：整齐的袜子收纳盒+ins风摆拍", "duration": "封面"},
                    {"shot": 2, "description": "内页1：收纳前后对比", "duration": "图文"},
                    {"shot": 3, "description": "内页2：每款袜子的搭配建议", "duration": "图文"},
                    {"shot": 4, "description": "内页3：上脚效果OOTD", "duration": "图文"},
                    {"shot": 5, "description": "尾图：购买清单+总结", "duration": "图文"}
                ],
                "script_text": "作为一个收纳控+强迫症患者，我的袜子必须按颜色、按季节、按用途分类收纳。今天分享一下我的袜子收纳心得和最近超爱的几款袜子💕\n\n🏷️ 收纳tips：\n• 按颜色分：白/灰/黑/彩色各一格\n• 按用途分：运动/通勤/家居\n• 定期清理：3个月一轮换\n\n🧦 最近回购的这几款：\n• 白色通勤款：百搭不挑鞋\n• 彩色周末款：心情up up\n• 运动款：防滑又吸汗\n\n均价不到10块，质感完全不输大牌。有姐妹问链接的，评论区告诉我，我整理好了发你们～",
                "title": "🧦我的袜子收纳术｜均价10块的快乐谁能懂",
                "comment_template": "📌统一回复：\n问链接的姐妹看这里👇\n白色通勤款→私信【白】\n彩色款→私信【彩】\n运动款→私信【运动】\n我都整理好啦，秒回！",
                "why_it_works": "小红书生活方式赛道：收纳美学+实用价值+低客单价+自然引流"
            },
            priority=85,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_SALE,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="紧迫型",
            emotion_structure={
                "type": "urgency_drive",
                "flow": "限时信息 → 稀缺感营造 → 产品价值 → 立即行动"
            },
            conversion_structure={
                "type": "direct_sale",
                "flow": "限时优惠 → 产品展示 → 价格锚点 → 私信下单"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦促单转化",
            fallback_content={
                "hook_text": "最后200单！这批袜子卖完就恢复原价了",
                "storyboard": [
                    {"shot": 1, "description": "手持手机显示库存数字，表情紧迫", "duration": "3s"},
                    {"shot": 2, "description": "快速展示袜子品质：拉扯弹性、揉搓不起球", "duration": "5s"},
                    {"shot": 3, "description": "对比展示：超市同款价格标签 vs 我们的价格", "duration": "4s"},
                    {"shot": 4, "description": "买家好评截图快速翻页", "duration": "3s"},
                    {"shot": 5, "description": "手指指向评论区，口播催促下单", "duration": "2s"}
                ],
                "script_text": "注意了！这批纯棉袜子只剩最后200单，卖完直接恢复59块9的原价。现在5双只要29块9，还包邮。你自己看这个弹性、这个面料，超市同品质至少翻一倍。已经有3000多人买了，好评率98%。别犹豫了，私信我'下单'，今天下单额外送1双。",
                "title": "最后200单！纯棉袜子5双29.9包邮 #限时优惠 #袜子特卖",
                "comment_template": "🔥最后200单！私信我【下单】立享29.9/5双，今天下单额外送1双！手慢无！",
                "why_it_works": "限时紧迫感+库存稀缺+价格锚点对比+额外赠品促单"
            },
            priority=100,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_SALE,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="对比型",
            emotion_structure={
                "type": "contrast_persuasion",
                "flow": "对比引入 → 差异放大 → 价值凸显 → 行动号召"
            },
            conversion_structure={
                "type": "contrast_sale",
                "flow": "竞品对比 → 优势罗列 → 价格对比 → 私信成交"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦对比促单",
            fallback_content={
                "hook_text": "同样买袜子，为什么有人花50有人花15？",
                "storyboard": [
                    {"shot": 1, "description": "左右分屏：50元袜子 vs 15元袜子外包装", "duration": "3s"},
                    {"shot": 2, "description": "同时拉扯两款袜子对比弹性", "duration": "4s"},
                    {"shot": 3, "description": "同时揉搓对比起球情况", "duration": "4s"},
                    {"shot": 4, "description": "上脚试穿对比舒适度", "duration": "4s"},
                    {"shot": 5, "description": "价格对比图+私信引导", "duration": "3s"}
                ],
                "script_text": "同样买袜子，有人花50块买一双，有人15块买了5双还更好穿。来，我给你比一下。左边这个是商场50块一双的，右边是我们家15块5双的。弹性一样好，面料一样是纯棉精梳，穿了一个月都没起球。区别在哪？区别就是我们没有中间商。想省钱的私信我'袜子'，我发你链接。",
                "title": "同样买袜子，为什么有人花50有人花15？ #省钱攻略 #袜子测评",
                "comment_template": "想省钱的私信我【袜子】，5双只要15块，和商场50的品质一模一样！",
                "why_it_works": "强对比制造冲击+直观差异展示+消除价格疑虑+直接转化"
            },
            priority=90,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_SALE,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="痛点型",
            emotion_structure={
                "type": "pain_push",
                "flow": "痛点直击 → 后果放大 → 解决方案 → 逼单成交"
            },
            conversion_structure={
                "type": "pain_to_sale",
                "flow": "痛点共鸣 → 方案呈现 → 限时逼单 → 私信下单"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦痛点逼单",
            fallback_content={
                "hook_text": "你的脚臭可能不是你的问题，是袜子的问题",
                "storyboard": [
                    {"shot": 1, "description": "人物脱鞋皱眉的尴尬场景", "duration": "3s"},
                    {"shot": 2, "description": "特写：化纤袜子不透气的微观示意", "duration": "4s"},
                    {"shot": 3, "description": "换上纯棉袜子后的轻松表情", "duration": "4s"},
                    {"shot": 4, "description": "透气性测试：袜子覆盖热水蒸汽对比", "duration": "4s"},
                    {"shot": 5, "description": "产品展示+限时价格+私信引导", "duration": "3s"}
                ],
                "script_text": "脚臭真的不是你的问题，是你穿的袜子不行。化纤面料不透气，汗排不出去，细菌一滋生就臭。换成纯棉精梳的袜子，透气吸汗，穿一天脚都是干的。我们家这款，7双一盒49块9，平均一双7块钱。今天下单再送1双除臭袜。私信我'换袜子'，别再让烂袜子坑你了。",
                "title": "脚臭不是你的错！换双袜子就好了 #脚臭解决方案 #纯棉袜子",
                "comment_template": "别再被烂袜子坑了！私信我【换袜子】，7双49.9今天下单还送1双除臭袜！",
                "why_it_works": "痛点直击引发共鸣+科学解释建立信任+解决方案+限时赠品逼单"
            },
            priority=80,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_SALE,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="测评型",
            emotion_structure={
                "type": "review_persuasion",
                "flow": "测评引入 → 多维度对比 → 真实体验 → 购买引导"
            },
            conversion_structure={
                "type": "xhs_review_sale",
                "flow": "测评笔记 → 评论区答疑 → 私信下单"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，聚焦种草转化",
            fallback_content={
                "hook_text": "买了8款网红袜子实测，只有这1款值得回购",
                "storyboard": [
                    {"shot": 1, "description": "封面：8双袜子排排站+文字'实测8款袜子'", "duration": "封面"},
                    {"shot": 2, "description": "内页1：8款袜子外观对比图", "duration": "图文"},
                    {"shot": 3, "description": "内页2：弹性/透气/起球3项测试结果", "duration": "图文"},
                    {"shot": 4, "description": "内页3：上脚实拍+穿着感受", "duration": "图文"},
                    {"shot": 5, "description": "尾图：推荐款+价格+购买方式", "duration": "图文"}
                ],
                "script_text": "姐妹们！我花了200块买了8款网红袜子，穿了2周实测，只有1款值得无限回购！\n\n📊 测评维度：\n• 弹性：拉伸后是否变形\n• 透气：穿一天脚闷不闷\n• 耐磨：穿2周是否起球\n\n🏆 冠军款：纯棉精梳运动袜\n✅ 弹性满分，穿脱不勒\n✅ 透气性TOP1，夏天也OK\n✅ 2周0起球，太绝了\n\n💰 5双39.9，一双不到8块\n想入手的姐妹私信我【测评】，我发你专属链接～",
                "title": "🧦实测8款网红袜子｜只有这1款值得无限回购",
                "comment_template": "📌测评冠军款链接在这！\n私信我【测评】秒发链接\n前30名下单送1双同款袜子🎁",
                "why_it_works": "测评权威感+数据化对比+真实体验+专属优惠促转化"
            },
            priority=95,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_SALE,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="套餐型",
            emotion_structure={
                "type": "bundle_value",
                "flow": "套餐展示 → 价值拆解 → 超值感营造 → 购买引导"
            },
            conversion_structure={
                "type": "xhs_bundle_sale",
                "flow": "套餐种草 → 评论区互动 → 私信下单"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，聚焦套餐引导转化",
            fallback_content={
                "hook_text": "一年袜子预算200块够了！我的省钱攻略",
                "storyboard": [
                    {"shot": 1, "description": "封面：全年袜子套餐全家福+文字'一年袜子200块搞定'", "duration": "封面"},
                    {"shot": 2, "description": "内页1：春夏款3双展示+搭配建议", "duration": "图文"},
                    {"shot": 3, "description": "内页2：秋冬款3双展示+搭配建议", "duration": "图文"},
                    {"shot": 4, "description": "内页3：运动款2双+家居款2双", "duration": "图文"},
                    {"shot": 5, "description": "尾图：套餐价格拆解+购买方式", "duration": "图文"}
                ],
                "script_text": "姐妹们！算了一笔账，一年买袜子其实200块就够了！\n\n🧦 我的年度袜子套餐：\n🌸 春夏薄款 × 3双 → 29.9\n🍂 秋冬加厚 × 3双 → 39.9\n🏃 运动款 × 2双 → 19.9\n🏠 家居款 × 2双 → 19.9\n\n📦 全年10双 = 109.6！\n比单买省了60多块！\n\n而且这个牌子的质量，穿一季完全没问题。我已经回购3年了，每季换新不心疼。\n\n想要同款套餐的姐妹私信我【套餐】，我发你组合链接～",
                "title": "🧦一年袜子200块搞定｜我的省钱攻略+搭配指南",
                "comment_template": "📌年度省钱套餐来啦！\n私信我【套餐】发你组合链接\n全年10双只要109.6，比单买省60+！",
                "why_it_works": "预算拆解降低决策门槛+套餐组合提升客单价+复购背书+私信转化"
            },
            priority=85,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_REFERRAL,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="收益型",
            emotion_structure={
                "type": "income_showcase",
                "flow": "收益结果 → 过程揭秘 → 门槛说明 → 行动号召"
            },
            conversion_structure={
                "type": "recruit_income",
                "flow": "收益展示 → 模式讲解 → 加入引导 → 私信报名"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦招募分销",
            fallback_content={
                "hook_text": "上个月卖袜子多赚了3000块，方法其实很简单",
                "storyboard": [
                    {"shot": 1, "description": "展示手机收益截图，表情自信", "duration": "3s"},
                    {"shot": 2, "description": "操作演示：手机转发袜子商品链接", "duration": "5s"},
                    {"shot": 3, "description": "展示客户下单通知弹窗", "duration": "3s"},
                    {"shot": 4, "description": "打包发货场景（平台代发）", "duration": "4s"},
                    {"shot": 5, "description": "手指指向评论区引导私信", "duration": "2s"}
                ],
                "script_text": "上个月靠卖袜子多赚了3000块，方法真的超简单。不用囤货，不用发货，就是把我家袜子的链接转发出去，有人买我就有佣金。一单赚5到15块，一天出个三五单，一个月下来就3000多了。零风险，零投入，一部手机就能做。想了解的私信我'加入'，我教你从0开始。",
                "title": "卖袜子月赚3000+，0库存0风险 #副业分享 #在家赚钱",
                "comment_template": "想跟我一样卖袜子赚零花钱的私信我【加入】，0门槛上手，我手把手教你！",
                "why_it_works": "真实收益展示+低门槛描述+零风险承诺+私信引导报名"
            },
            priority=100,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_REFERRAL,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="低门槛型",
            emotion_structure={
                "type": "easy_start",
                "flow": "门槛拆解 → 简单步骤 → 收益预期 → 立即行动"
            },
            conversion_structure={
                "type": "recruit_easy",
                "flow": "三步讲解 → 案例展示 → 保障承诺 → 私信加入"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦低门槛招募",
            fallback_content={
                "hook_text": "3步开始卖袜子，不用花一分钱",
                "storyboard": [
                    {"shot": 1, "description": "手持手机展示注册页面", "duration": "3s"},
                    {"shot": 2, "description": "选品页面：浏览袜子商品列表", "duration": "4s"},
                    {"shot": 3, "description": "一键转发到朋友圈/群聊", "duration": "4s"},
                    {"shot": 4, "description": "收益到账通知+提现页面", "duration": "4s"},
                    {"shot": 5, "description": "团队群聊截图+私信引导", "duration": "3s"}
                ],
                "script_text": "卖袜子真的不用花一分钱，3步就能开始。第一步，扫码注册，30秒搞定；第二步，选一款你觉得好看的袜子，一键转发；第三步，等别人下单，佣金自动到账。不用囤货，不用打包，不用售后，平台全包了。我团队里有个宝妈，第一个月就出了20多单。私信我'开始'，我拉你进新手群。",
                "title": "0成本卖袜子！3步上手月入3000+ #副业项目 #零投入创业",
                "comment_template": "0成本0门槛！私信我【开始】加入新手群，我带你从第一步做起！",
                "why_it_works": "三步拆解降低心理门槛+零投入消除顾虑+真实案例+社群支持"
            },
            priority=90,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_REFERRAL,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="裂变型",
            emotion_structure={
                "type": "team_growth",
                "flow": "团队成果 → 裂变机制 → 共赢理念 → 招募号召"
            },
            conversion_structure={
                "type": "recruit_team",
                "flow": "团队展示 → 分润讲解 → 培训承诺 → 私信报名"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦团队裂变招募",
            fallback_content={
                "hook_text": "我一个人卖袜子月赚3000，带上团队月赚过万",
                "storyboard": [
                    {"shot": 1, "description": "个人收益截图展示", "duration": "3s"},
                    {"shot": 2, "description": "团队群聊热闹场景截图", "duration": "4s"},
                    {"shot": 3, "description": "分润机制图解动画", "duration": "5s"},
                    {"shot": 4, "description": "团队成员晒单截图合集", "duration": "4s"},
                    {"shot": 5, "description": "招募海报+私信引导", "duration": "2s"}
                ],
                "script_text": "我一个人卖袜子一个月赚3000，但带上团队就不一样了。你卖袜子赚佣金，你拉的人卖袜子你也拿提成，这就是裂变。我们团队现在200多人，每个人都在赚钱。我提供货源、素材、培训，你只管卖。不用囤货，不用发货，每天花1小时转发就行。想加入的私信我'团队'，名额有限。",
                "title": "从月赚3000到团队裂变，袜子分销怎么做 #团队裂变 #分销招募",
                "comment_template": "想加入200人袜子分销团队的私信我【团队】！货源+素材+培训全包，你只管卖！",
                "why_it_works": "个人到团队的增长故事+裂变机制可视化+全套支持承诺+稀缺名额"
            },
            priority=80,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_REFERRAL,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="副业型",
            emotion_structure={
                "type": "mom_side_hustle",
                "flow": "宝妈共鸣 → 副业需求 → 方案展示 → 收入预期"
            },
            conversion_structure={
                "type": "xhs_side_hustle",
                "flow": "副业种草 → 评论区答疑 → 私信报名"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，聚焦宝妈副业招募",
            fallback_content={
                "hook_text": "带娃两年0收入，直到我开始卖袜子",
                "storyboard": [
                    {"shot": 1, "description": "封面：带娃日常+文字'宝妈副业实测'", "duration": "封面"},
                    {"shot": 2, "description": "内页1：带娃间隙用手机操作的截图", "duration": "图文"},
                    {"shot": 3, "description": "内页2：袜子选品+转发流程截图", "duration": "图文"},
                    {"shot": 4, "description": "内页3：收益记录+提现截图", "duration": "图文"},
                    {"shot": 5, "description": "尾图：加入方式+新手福利", "duration": "图文"}
                ],
                "script_text": "带娃两年没收入，伸手要钱的感觉真的不好受。直到闺蜜带我卖袜子，一切都不一样了。\n\n🧦 我的一天：\n• 早上送娃上学后，花20分钟选品转发\n• 午休时回复几个客户消息\n• 晚上看看今天的收益\n\n💰 第一个月：800+\n💰 第三个月：2000+\n\n不用囤货、不用发货、不用客服，平台全包了。一部手机，碎片时间就能做。\n\n想了解的宝妈私信我【副业】，我分享我的经验～",
                "title": "🧦带娃两年0收入｜卖袜子让我找回了自己",
                "comment_template": "📌宝妈们看这里！\n私信我【副业】分享0门槛卖袜子攻略\n不用囤货不用发货，碎片时间就能做💕",
                "why_it_works": "宝妈痛点共鸣+碎片时间适配+真实收入递增+零门槛承诺"
            },
            priority=95,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_REFERRAL,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="分享型",
            emotion_structure={
                "type": "share_earn",
                "flow": "分享场景 → 收益惊喜 → 方法揭秘 → 邀请加入"
            },
            conversion_structure={
                "type": "xhs_share_recruit",
                "flow": "好物分享 → 分销介绍 → 评论区互动 → 私信加入"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，聚焦分享赚钱招募",
            fallback_content={
                "hook_text": "只是分享了下我买的袜子，竟然赚了500块",
                "storyboard": [
                    {"shot": 1, "description": "封面：袜子实拍+文字'分享就赚钱'", "duration": "封面"},
                    {"shot": 2, "description": "内页1：原来发的好物分享笔记截图", "duration": "图文"},
                    {"shot": 3, "description": "内页2：分销佣金到账截图", "duration": "图文"},
                    {"shot": 4, "description": "内页3：操作流程3步图解", "duration": "图文"},
                    {"shot": 5, "description": "尾图：加入方式+收益预期", "duration": "图文"}
                ],
                "script_text": "姐妹们！我之前只是正常分享我买的袜子，结果发现可以赚佣金！\n\n事情是这样的👇\n我买了一家袜子的分销资格，然后把好穿的袜子分享出去，有人通过我的链接下单，我就拿佣金。\n\n📊 我的收益：\n• 第1周：出了5单，赚了50块\n• 第2周：出了12单，赚了150块\n• 一个月下来：500+\n\n关键是不用囤货不用发货，就是分享好东西就能赚钱。跟发朋友圈一样简单！\n\n想试试的姐妹私信我【分享】，我教你如何开始～",
                "title": "🧦分享袜子竟然赚了500+｜0门槛副业实测",
                "comment_template": "📌想跟我一样分享赚钱的姐妹\n私信我【分享】教你0门槛开始\n就是发好物笔记那么简单！",
                "why_it_works": "意外收益引发好奇+操作极简+真实数据+社交分享属性"
            },
            priority=85,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_IP,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="人设型",
            emotion_structure={
                "type": "persona_building",
                "flow": "人设标签 → 差异化展示 → 价值输出 → 关注引导"
            },
            conversion_structure={
                "type": "ip_follow",
                "flow": "人设记忆点 → 专业内容 → 系列预告 → 关注转化"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦品牌建设",
            fallback_content={
                "hook_text": "我是穿了1000双袜子的测评官，今天告诉你真相",
                "storyboard": [
                    {"shot": 1, "description": "人物标志性出场+固定slogan", "duration": "3s"},
                    {"shot": 2, "description": "展示过往测评过的袜子合集", "duration": "4s"},
                    {"shot": 3, "description": "本期测评核心观点展示", "duration": "5s"},
                    {"shot": 4, "description": "专业测试画面（弹性/透气/耐磨）", "duration": "5s"},
                    {"shot": 5, "description": "固定结尾slogan+关注引导", "duration": "3s"}
                ],
                "script_text": "我是穿了1000双袜子的测评官，只说真话。今天聊聊为什么你的袜子总是穿一个月就坏。市面上90%的袜子含棉量不足60%，却标着纯棉。教你一招：看水洗标，含棉量85%以上的才值得买。关注我，下期教你3秒辨别袜子好坏的方法。我是袜子测评官，只说真话。",
                "title": "穿了1000双袜子的测评官：为什么你的袜子总坏 #袜子测评 #好物测评",
                "comment_template": "关注我，每周测评一款袜子，只说真话！下期教你3秒辨别袜子好坏🔥",
                "why_it_works": "强人设标签+专业权威+系列内容钩子+固定记忆点"
            },
            priority=100,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_IP,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="专业型",
            emotion_structure={
                "type": "expert_output",
                "flow": "专业身份 → 知识输出 → 实用价值 → 信任建立"
            },
            conversion_structure={
                "type": "ip_expert",
                "flow": "专业观点 → 干货分享 → 互动引导 → 关注沉淀"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦专业输出",
            fallback_content={
                "hook_text": "做袜子行业8年，这3个内幕你一定要知道",
                "storyboard": [
                    {"shot": 1, "description": "人物在工厂/仓库的专业场景", "duration": "3s"},
                    {"shot": 2, "description": "展示袜子生产线或质检流程", "duration": "5s"},
                    {"shot": 3, "description": "内幕1：含棉量猫腻图解", "duration": "4s"},
                    {"shot": 4, "description": "内幕2：染色工艺差异对比", "duration": "4s"},
                    {"shot": 5, "description": "内幕3：罗口工艺区别+关注引导", "duration": "4s"}
                ],
                "script_text": "做袜子行业8年，今天说3个内幕。第一，标着纯棉的袜子，含棉量可能只有50%，剩下的都是涤纶，所以容易起球。第二，深色袜子比浅色更容易掉色，因为染色工艺不同。第三，袜子的寿命主要看罗口，包纱罗口比普通罗口耐用3倍。关注我，了解更多袜子行业的真相。",
                "title": "袜子行业8年老兵揭秘3个内幕 #行业揭秘 #袜子知识",
                "comment_template": "做袜子8年，只分享真实经验。关注我，下期讲怎么挑到不起球的袜子！",
                "why_it_works": "行业权威+独家内幕+实用知识+持续关注理由"
            },
            priority=90,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_IP,
            platform_id=PLATFORM_ID_DOUYIN,
            hook_type="故事型",
            emotion_structure={
                "type": "story_resonance",
                "flow": "故事开场 → 情感共鸣 → 价值升华 → 品牌关联"
            },
            conversion_structure={
                "type": "ip_story",
                "flow": "个人故事 → 价值观传递 → 品牌理念 → 关注引导"
            },
            prompt_template="使用{hook_type}钩子类型，情绪结构为{emotion_structure}，转化结构为{conversion_structure}，聚焦故事共鸣",
            fallback_content={
                "hook_text": "从工厂女工到袜子品牌创始人，我走了5年",
                "storyboard": [
                    {"shot": 1, "description": "老照片/旧场景：工厂流水线工作画面", "duration": "4s"},
                    {"shot": 2, "description": "转折点：第一次创业的场景", "duration": "4s"},
                    {"shot": 3, "description": "困难时刻：堆积的库存、疲惫的表情", "duration": "4s"},
                    {"shot": 4, "description": "突破：第一批忠实客户的故事", "duration": "4s"},
                    {"shot": 5, "description": "现在：品牌展示+理念表达+关注引导", "duration": "4s"}
                ],
                "script_text": "5年前我还在工厂流水线上缝袜子，每天站10个小时，一个月3000块。那时候我就想，为什么我做的袜子质量这么好，却卖不上价？后来我辞职创业，自己跑面料、找工厂、做品牌。最难的时候，仓库堆了一万双袜子卖不出去。但我没放弃，一双一双地卖，一个客户一个客户地聊。现在我们的袜子复购率超过60%。关注我，我想把好袜子带给更多人。",
                "title": "从工厂女工到袜子品牌创始人 #创业故事 #女性创业",
                "comment_template": "每一个穿过我们袜子的人，都是我坚持的理由。关注我，一起见证好袜子的诞生❤️",
                "why_it_works": "真实故事引发共鸣+创业精神传递+品牌理念植入+情感连接"
            },
            priority=80,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_IP,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="生活方式型",
            emotion_structure={
                "type": "lifestyle_brand",
                "flow": "生活美学 → 品味展示 → 产品融入 → 品牌调性"
            },
            conversion_structure={
                "type": "xhs_lifestyle_ip",
                "flow": "生活方式种草 → 品牌理念传递 → 评论区互动 → 关注沉淀"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，聚焦个人品牌",
            fallback_content={
                "hook_text": "一个袜子控的精致生活，从脚下开始",
                "storyboard": [
                    {"shot": 1, "description": "封面：ins风袜子收纳+咖啡+杂志摆拍", "duration": "封面"},
                    {"shot": 2, "description": "内页1：晨间穿搭OOTD（袜子特写）", "duration": "图文"},
                    {"shot": 3, "description": "内页2：不同场景袜子搭配（办公/运动/约会）", "duration": "图文"},
                    {"shot": 4, "description": "内页3：袜子护理小技巧", "duration": "图文"},
                    {"shot": 5, "description": "尾图：个人品牌slogan+关注引导", "duration": "图文"}
                ],
                "script_text": "有人问我为什么对袜子这么讲究，因为我觉得精致生活从脚下开始💕\n\n🧦 我的袜子哲学：\n• 通勤日：纯色简约款，低调有质感\n• 运动日：专业运动袜，功能优先\n• 约会日：小心机设计款，细节加分\n• 居家日：毛绒厚底袜，舒适至上\n\n✨ 袜子护理tips：\n• 翻面洗，保护外观\n• 自然晾干，避免烘干\n• 3个月更换一轮\n\n一双好袜子，是对自己最基本的温柔。关注我，分享更多精致生活小细节～",
                "title": "🧦一个袜子控的精致生活｜从脚下开始的仪式感",
                "comment_template": "精致生活从脚下开始💕\n关注我，每周分享袜子搭配和护理小技巧\n你最喜欢哪种风格的袜子？评论区告诉我～",
                "why_it_works": "生活美学定位+场景化种草+护理干货+品牌调性输出"
            },
            priority=95,
            is_active=True,
        ),
        ContentStructure(
            intent_id=INTENT_ID_IP,
            platform_id=PLATFORM_ID_XIAOHONGSHU,
            hook_type="干货型",
            emotion_structure={
                "type": "knowledge_sharing",
                "flow": "痛点引入 → 知识输出 → 实操方法 → 专家定位"
            },
            conversion_structure={
                "type": "xhs_expert_ip",
                "flow": "干货分享 → 评论区答疑 → 系列预告 → 关注转化"
            },
            prompt_template="小红书风格：{hook_type}钩子，情绪结构{emotion_structure}，转化结构{conversion_structure}，聚焦干货分享",
            fallback_content={
                "hook_text": "买袜子前必看！5个参数教你挑到好袜子",
                "storyboard": [
                    {"shot": 1, "description": "封面：文字'买袜子必看5个参数'+袜子特写", "duration": "封面"},
                    {"shot": 2, "description": "内页1：参数1-2 含棉量+支数图解", "duration": "图文"},
                    {"shot": 3, "description": "内页2：参数3-4 罗口+脚跟工艺", "duration": "图文"},
                    {"shot": 4, "description": "内页3：参数5 尺码选择指南", "duration": "图文"},
                    {"shot": 5, "description": "尾图：总结清单+关注引导", "duration": "图文"}
                ],
                "script_text": "买袜子别再只看颜值了！5个参数教你挑到真正好穿的袜子👇\n\n📋 买袜子必看5参数：\n\n1️⃣ 含棉量：≥80%才舒适透气\n2️⃣ 纱线支数：40支以上才细腻\n3️⃣ 罗口工艺：包纱罗口不勒腿\n4️⃣ 脚跟设计：Y字跟更贴合不滑\n5️⃣ 尺码选择：按脚长选不按码数\n\n💡 避坑提醒：\n• 标'纯棉'但含棉量<70%的别买\n• 罗口太紧的会勒出痕\n• 买回家先洗一次，掉色严重的赶紧退\n\n收藏这篇，下次买袜子照着挑！关注我，下期分享不同季节怎么选袜子～",
                "title": "🧦买袜子必看！5个参数教你挑到好袜子｜干货收藏",
                "comment_template": "📌收藏这篇买袜子不踩坑！\n关注我，下期分享【不同季节袜子选购指南】\n有问题评论区问，我一个个答～",
                "why_it_works": "干货权威感+参数化标准+避坑指南+系列内容钩子"
            },
            priority=85,
            is_active=True,
        ),
    ]
    db.add_all(structures)
    await db.commit()


async def seed_conversion_paths(db: AsyncSession):
    result = await db.execute(select(ConversionPath))
    if result.scalars().first():
        return
    paths = [
        ConversionPath(
            intent_id=INTENT_ID_TRAFFIC,
            stage="public_to_private",
            title="评论引导私信",
            scripts={"opener": "想要同款的姐妹扣1", "guide": "我私信你链接和优惠码", "close": "前10名还有额外福利哦"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_TRAFFIC,
            stage="public_to_private",
            title="关键词触发",
            scripts={"opener": "评论区回复'袜子'自动发链接", "guide": "已私信，注意查收哦", "close": "数量有限先到先得"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_TRAFFIC,
            stage="private_to_deal",
            title="破冰话术",
            scripts={"opener": "嗨，看到你对袜子感兴趣", "guide": "我们这款是纯棉精梳的，5双39.9包邮", "close": "现在下单还送1双试用装"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_TRAFFIC,
            stage="private_to_deal",
            title="需求判断",
            scripts={"opener": "你是自己穿还是送人呢", "guide": "根据你的需求推荐最合适的款", "close": "今天下单有专属折扣"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_TRAFFIC,
            stage="deal_boost",
            title="限时催单",
            scripts={"opener": "库存只剩最后50单了", "guide": "这个价格下次不一定有", "close": "现在下单明天就能收到"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_TRAFFIC,
            stage="deal_boost",
            title="对比话术",
            scripts={"opener": "超市同品质至少要15块一双", "guide": "我们平均不到8块，品质一样", "close": "不满意7天无理由退"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_SALE,
            stage="public_to_private",
            title="优惠引导",
            scripts={"opener": "限时活动价，比平时便宜30%", "guide": "私信我'优惠'获取专属折扣码", "close": "活动今天结束"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_SALE,
            stage="public_to_private",
            title="套餐推荐",
            scripts={"opener": "买3组送1组，算下来一双才5块", "guide": "私信我'套餐'看详细组合", "close": "套餐限量100份"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_SALE,
            stage="private_to_deal",
            title="促单话术",
            scripts={"opener": "这款是我们回购率最高的", "guide": "现在下单立减10元，还送运费险", "close": "支持货到付款，不满意直接退"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_SALE,
            stage="private_to_deal",
            title="套餐推荐",
            scripts={"opener": "推荐你买家庭装，10双59.9", "guide": "男女款都有，全家都够穿", "close": "家庭装还额外送2双儿童款"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_SALE,
            stage="deal_boost",
            title="紧迫催单",
            scripts={"opener": "你选的款式只剩最后8单", "guide": "现在锁单还来得及", "close": "付款后24小时内发货"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_SALE,
            stage="deal_boost",
            title="信任背书",
            scripts={"opener": "我们已卖出10万+双，好评率98%", "guide": "这是真实买家反馈截图", "close": "7天无理由+运费险双重保障"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_REFERRAL,
            stage="public_to_private",
            title="收益吸引",
            scripts={"opener": "0门槛加入，卖一双赚5块", "guide": "私信我'加入'获取分销资格", "close": "前100名还有额外奖励"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_REFERRAL,
            stage="public_to_private",
            title="低门槛",
            scripts={"opener": "不用囤货不用发货，转发就能赚", "guide": "私信我'分销'了解详情", "close": "零风险，随时可退出"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_REFERRAL,
            stage="private_to_deal",
            title="招募话术",
            scripts={"opener": "我们的分销体系很简单", "guide": "你只需要转发内容，成交后自动结算佣金", "close": "月入3000+的分销商已有200+人"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_REFERRAL,
            stage="private_to_deal",
            title="支持体系",
            scripts={"opener": "加入后我会手把手教你", "guide": "提供素材包+话术包+一对一指导", "close": "前3个月免平台服务费"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_REFERRAL,
            stage="deal_boost",
            title="稀缺催促",
            scripts={"opener": "目前只开放50个分销名额", "guide": "先到先得，满额即止", "close": "现在加入还能享受首月双倍佣金"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_REFERRAL,
            stage="deal_boost",
            title="成功案例",
            scripts={"opener": "宝妈小李第一个月就赚了2800", "guide": "她每天只花1小时发3条内容", "close": "你也可以，现在就加入试试"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_IP,
            stage="public_to_private",
            title="价值吸引",
            scripts={"opener": "关注我，每周分享袜子行业干货", "guide": "私信我'干货'获取行业报告", "close": "关注不迷路"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_IP,
            stage="public_to_private",
            title="互动引导",
            scripts={"opener": "你觉得什么样的袜子最舒服？评论区聊聊", "guide": "关注我获取更多穿搭技巧", "close": "每周抽奖送袜子"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_IP,
            stage="private_to_deal",
            title="粉丝运营",
            scripts={"opener": "感谢关注！送你一份袜子选购指南", "guide": "有任何问题随时私信我", "close": "粉丝专属9折优惠码已发送"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_IP,
            stage="private_to_deal",
            title="社群引导",
            scripts={"opener": "我们有个袜子爱好者社群", "guide": "群里每天分享好物和优惠", "close": "社群成员享受内部价"},
            sort_order=2,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_IP,
            stage="deal_boost",
            title="持续价值",
            scripts={"opener": "这周又测了5款新袜子", "guide": "关注我不错过每期测评", "close": "长期关注有惊喜"},
            sort_order=1,
            is_active=True,
        ),
        ConversionPath(
            intent_id=INTENT_ID_IP,
            stage="deal_boost",
            title="品牌背书",
            scripts={"opener": "3年袜子行业经验，帮10万+人选对袜子", "guide": "关注我，让你不再踩坑", "close": "专业选品，值得信赖"},
            sort_order=2,
            is_active=True,
        ),
    ]
    db.add_all(paths)
    await db.commit()


async def seed_all():
    async with async_session_factory() as db:
        await seed_intents(db)
        await seed_platforms(db)
        await seed_optimization_rules(db)
        await seed_content_structures(db)
        await seed_conversion_paths(db)
    print("种子数据初始化完成")


if __name__ == "__main__":
    asyncio.run(seed_all())
