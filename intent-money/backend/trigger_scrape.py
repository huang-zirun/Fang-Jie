import asyncio
import sys
import uuid
sys.path.insert(0, '.')

from app.database import async_session_factory
from app.services.market_service import scrape_and_save_hot_videos
from app.seed import PLATFORM_ID_DOUYIN
from sqlalchemy import select
from app.models.user_platform_account import UserPlatformAccount


async def main():
    print("开始抓取抖音市场热门数据...")

    async with async_session_factory() as db:
        # 查询活跃的抖音账号
        result = await db.execute(
            select(UserPlatformAccount).where(
                UserPlatformAccount.platform == "douyin",
                UserPlatformAccount.cookie_status == "active"
            )
        )
        accounts = result.scalars().all()

        if not accounts:
            print("没有找到活跃的抖音账号")
            return

        print(f"找到 {len(accounts)} 个活跃的抖音账号")
        for acc in accounts:
            print(f"  - 用户ID: {acc.user_id}, 状态: {acc.cookie_status}")

        # 使用第一个活跃账号
        user_id = accounts[0].user_id  # 直接使用 UUID 对象
        print(f"\n使用用户 {user_id} 的 cookie 进行抓取...")

        keywords = ["袜子", "好物推荐", "穿搭", "生活好物"]
        total_saved = 0

        for keyword in keywords:
            print(f"\n正在抓取关键词: {keyword}")
            try:
                saved_count = await scrape_and_save_hot_videos(
                    db,
                    PLATFORM_ID_DOUYIN,
                    keyword,
                    user_id=str(user_id)  # 转换为字符串
                )
                total_saved += saved_count
                print(f"  保存了 {saved_count} 条数据")
            except Exception as e:
                print(f"  抓取失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n总计保存了 {total_saved} 条市场热门数据")


if __name__ == "__main__":
    asyncio.run(main())
