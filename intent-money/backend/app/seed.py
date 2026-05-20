import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.content_structure import ContentStructure
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
        Intent(id=INTENT_ID_SALE, name="成交赚钱", description="我想卖出更多袜子", sort_order=2, is_active=False),
        Intent(id=INTENT_ID_REFERRAL, name="裂变招募分销", description="我想让别人帮我赚钱", sort_order=3, is_active=False),
        Intent(id=INTENT_ID_IP, name="IP长期增长", description="我想做账号做品牌", sort_order=4, is_active=False),
    ]
    db.add_all(intents)
    await db.commit()


async def seed_platforms(db: AsyncSession):
    result = await db.execute(select(Platform))
    if result.scalars().first():
        return
    platforms = [
        Platform(id=PLATFORM_ID_DOUYIN, name="抖音", is_active=True),
        Platform(id=PLATFORM_ID_XIAOHONGSHU, name="小红书", is_active=True),
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
    ]
    db.add_all(structures)
    await db.commit()


async def seed_all():
    async with async_session_factory() as db:
        await seed_intents(db)
        await seed_platforms(db)
        await seed_optimization_rules(db)
        await seed_content_structures(db)
    print("Seed data created successfully")


if __name__ == "__main__":
    asyncio.run(seed_all())
