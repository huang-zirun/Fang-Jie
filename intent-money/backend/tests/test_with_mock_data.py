# -*- coding: utf-8 -*-
"""测试带模拟数据的内容生成"""
import asyncio
import sys
import uuid
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select
from app.database import async_session_factory
from app.models.platform import Platform
from app.models.intent import Intent
from app.models.market_hot import MarketHot
from app.services.task_service import match_content_structure
from app.services.ai_service import _build_prompt


async def insert_mock_market_hots():
    """插入模拟的 market_hots 数据"""
    print("=" * 60)
    print("插入模拟 market_hots 数据")
    print("=" * 60)
    
    async with async_session_factory() as db:
        # 获取第一个平台
        result = await db.execute(select(Platform))
        platform = result.scalars().first()
        
        if not platform:
            print("❌ 没有找到平台")
            return None
        
        # 创建模拟数据
        mock_data = MarketHot(
            id=uuid.uuid4(),
            platform_id=platform.id,
            keyword="袜子",
            hot_type="video",
            analysis_result={
                "hot_titles": [
                    "这款袜子穿了3个月还像新的！",
                    "终于找到不臭脚的袜子了",
                    "便宜又好穿的袜子推荐"
                ],
                "hot_tags": ["#袜子推荐", "#好物分享", "#穿搭", "#平价好物"],
                "emotional_patterns": ["痛点→解决方案→效果展示", "好奇→揭秘→推荐"],
                "high_engagement_hooks": [
                    "你穿的袜子可能正在伤害你的脚",
                    "为什么你的袜子总是臭臭的？",
                    "这款袜子我回购了10次"
                ],
                "content_themes": ["防臭袜", "纯棉袜", "运动袜"]
            },
            recommended_structures=["痛点直击", "反常识型"],
            priority_boost=1.5,
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True,
            comment_sentiment={
                "positive_ratio": "65%",
                "key_topics": ["舒适度", "防臭效果", "价格"]
            }
        )
        
        db.add(mock_data)
        await db.commit()
        print(f"✅ 插入模拟数据成功 (ID: {mock_data.id})")
        return platform.id


async def test_with_mock_data(platform_id):
    """使用模拟数据测试"""
    print("\n" + "=" * 60)
    print("使用模拟数据测试")
    print("=" * 60)
    
    async with async_session_factory() as db:
        # 获取第一个意图
        result = await db.execute(select(Intent))
        intent = result.scalars().first()
        
        if not intent:
            print("❌ 没有找到意图")
            return
        
        print(f"\n测试: 意图={intent.name}, 平台ID={platform_id}")
        
        # 测试 match_content_structure
        structure, market_insights = await match_content_structure(db, intent.id, platform_id)
        
        if structure:
            print(f"\n✅ 选择的内容结构: {structure.hook_type}")
        else:
            print("\n⚠️ 没有找到匹配的内容结构")
        
        if market_insights:
            print(f"✅ 获取到 market_insights:")
            print(f"   hot_titles: {market_insights.get('hot_titles', [])}")
            print(f"   hot_tags: {market_insights.get('hot_tags', [])}")
            print(f"   emotional_patterns: {market_insights.get('emotional_patterns', [])}")
            print(f"   high_engagement_hooks: {market_insights.get('high_engagement_hooks', [])}")
            print(f"   sentiment_summary: {market_insights.get('sentiment_summary', {})}")
            
            # 测试 prompt 生成
            print("\n" + "=" * 60)
            print("测试 AI Prompt 生成（带 market_insights）")
            print("=" * 60)
            
            prompt = _build_prompt(
                intent_name=intent.name,
                intent_description=intent.description,
                platform_name="抖音",
                hook_type=structure.hook_type if structure else "痛点直击",
                emotion_structure={"curve": "上升-下降-上升"},
                conversion_structure={"steps": ["吸引", "信任", "行动"]},
                market_insights=market_insights
            )
            
            print("\n生成的 Prompt 片段（市场热门参考部分）:")
            print("-" * 60)
            
            # 只打印市场热门参考部分
            if "## 当前市场热门参考" in prompt:
                market_section = prompt.split("## 当前市场热门参考")[1]
                if "## 禁用表达" in market_section:
                    market_section = market_section.split("## 禁用表达")[0]
                print("## 当前市场热门参考" + market_section[:2000] + "...")
            else:
                print("⚠️ Prompt 中没有找到市场热门参考部分")
                print(prompt[:1000])
        else:
            print(f"⚠️ market_insights 为空")


async def cleanup_mock_data():
    """清理模拟数据"""
    print("\n" + "=" * 60)
    print("清理模拟数据")
    print("=" * 60)
    
    async with async_session_factory() as db:
        from sqlalchemy import delete
        
        # 删除 keyword="袜子" 的测试数据
        result = await db.execute(
            delete(MarketHot).where(MarketHot.keyword == "袜子")
        )
        await db.commit()
        print(f"✅ 清理完成")


async def main():
    try:
        platform_id = await insert_mock_market_hots()
        if platform_id:
            await test_with_mock_data(platform_id)
    finally:
        await cleanup_mock_data()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
