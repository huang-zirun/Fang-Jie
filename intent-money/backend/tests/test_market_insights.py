# -*- coding: utf-8 -*-
"""测试 market_insights 功能"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory
from app.services.task_service import _get_market_insights, match_content_structure
from app.models.platform import Platform
from sqlalchemy import select


async def test_get_market_insights():
    """测试 _get_market_insights 函数"""
    print("=" * 60)
    print("测试 _get_market_insights 函数")
    print("=" * 60)
    
    async with async_session_factory() as db:
        # 获取第一个平台
        result = await db.execute(select(Platform))
        platform = result.scalars().first()
        
        if not platform:
            print("❌ 没有找到平台")
            return
        
        print(f"\n测试平台: {platform.name} (ID: {platform.id})")
        
        # 测试 _get_market_insights
        insights = await _get_market_insights(db, platform.id)
        
        if insights:
            print("\n✅ 获取到 market_insights:")
            print(f"   hot_titles: {insights.get('hot_titles', [])}")
            print(f"   hot_tags: {insights.get('hot_tags', [])}")
            print(f"   emotional_patterns: {insights.get('emotional_patterns', [])}")
            print(f"   high_engagement_hooks: {insights.get('high_engagement_hooks', [])}")
            print(f"   content_themes: {insights.get('content_themes', [])}")
            print(f"   sentiment_summary: {insights.get('sentiment_summary', {})}")
        else:
            print("\n⚠️ market_insights 为空（可能 market_hots 表中没有活跃数据）")
            print("   这是正常的降级行为，系统会使用原有模板生成逻辑")


async def test_match_content_structure():
    """测试 match_content_structure 函数"""
    print("\n" + "=" * 60)
    print("测试 match_content_structure 函数")
    print("=" * 60)
    
    async with async_session_factory() as db:
        # 获取第一个平台和第一个意图
        from app.models.intent import Intent
        
        result = await db.execute(select(Platform))
        platform = result.scalars().first()
        
        result = await db.execute(select(Intent))
        intent = result.scalars().first()
        
        if not platform or not intent:
            print("❌ 没有找到平台或意图")
            return
        
        print(f"\n测试: 意图={intent.name}, 平台={platform.name}")
        
        # 测试 match_content_structure
        structure, market_insights = await match_content_structure(db, intent.id, platform.id)
        
        if structure:
            print(f"\n✅ 选择的内容结构: {structure.hook_type}")
        else:
            print("\n⚠️ 没有找到匹配的内容结构")
        
        if market_insights:
            print(f"✅ 获取到 market_insights")
        else:
            print(f"⚠️ market_insights 为空")


async def main():
    await test_get_market_insights()
    await test_match_content_structure()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
