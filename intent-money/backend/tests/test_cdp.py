"""测试 CDP (Chrome DevTools Protocol) 是否能正常获取数据"""
import asyncio
import sys
from app.services.platform_scraper.cdp_browser import CdpBrowser, CdpConnectionError
from app.services.platform_scraper.cdp_xhs_scraper import CdpXhsScraper
from app.services.platform_scraper.cdp_douyin_scraper import CdpDouyinScraper
from app.config import settings


async def test_cdp_connection():
    """测试 CDP 基础连接"""
    print("=" * 60)
    print("测试 1: CDP 基础连接")
    print("=" * 60)

    browser = CdpBrowser(
        host=settings.CDP_DEBUG_HOST,
        port=settings.CDP_DEBUG_PORT
    )

    try:
        health = await browser.check_health()
        if health:
            print(f"✅ CDP 连接正常")
            print(f"   地址: http://{settings.CDP_DEBUG_HOST}:{settings.CDP_DEBUG_PORT}")
        else:
            print(f"❌ CDP 连接失败 - Chrome 可能未启动或端口未开放")
            print(f"   请确保 Chrome 已启动并开启了远程调试端口:")
            print(f"   chrome --remote-debugging-port={settings.CDP_DEBUG_PORT}")
            return False
    except Exception as e:
        print(f"❌ CDP 连接异常: {e}")
        return False

    # 测试导航到一个简单页面
    try:
        print("\n测试页面导航...")
        await browser.navigate("https://www.baidu.com", wait_seconds=3.0)
        title = await browser.evaluate("document.title")
        print(f"✅ 页面导航成功")
        print(f"   页面标题: {title}")

        # 测试获取页面文本
        text = await browser.get_page_text()
        print(f"   页面文本长度: {len(text)} 字符")

        await browser.close()
        return True
    except CdpConnectionError as e:
        print(f"❌ 页面导航失败: {e}")
        await browser.close()
        return False
    except Exception as e:
        print(f"❌ 页面导航异常: {e}")
        await browser.close()
        return False


async def test_xhs_scraper():
    """测试小红书 CDP 爬虫"""
    print("\n" + "=" * 60)
    print("测试 2: 小红书 CDP 爬虫")
    print("=" * 60)

    scraper = CdpXhsScraper()

    # 先检查健康状态
    health = await scraper.check_health()
    if not health:
        print(f"❌ 小红书爬虫健康检查失败")
        print(f"   请确保 Chrome 已启动并登录了小红书")
        return False

    print(f"✅ 小红书爬虫健康检查通过")

    # 测试搜索
    keyword = "袜子"
    print(f"\n测试搜索关键词: '{keyword}'")
    print("请确保 Chrome 已登录小红书，否则可能无法获取数据...")

    try:
        # 使用最多点赞排序获取数据
        results = await scraper.search_hot_notes(keyword=keyword, limit=10, sort="likes")

        if results:
            print(f"✅ 搜索成功，获取到 {len(results)} 条笔记（按最多点赞排序）")
            print("\n前 5 条结果预览:")
            for i, note in enumerate(results[:5], 1):
                print(f"\n  [{i}] {note.get('title', 'N/A')[:40]}...")
                print(f"      作者: {note.get('author', 'N/A')}")
                print(f"      点赞: {note.get('liked_count', 'N/A')}")
                print(f"      链接: {note.get('link', 'N/A')[:60]}...")
            return True
        else:
            print(f"⚠️ 搜索返回空结果")
            print(f"   可能原因:")
            print(f"   1. Chrome 未登录小红书")
            print(f"   2. 小红书页面结构发生变化")
            print(f"   3. 网络问题或反爬限制")
            return False
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False


async def test_douyin_scraper():
    """测试抖音 CDP 爬虫"""
    print("\n" + "=" * 60)
    print("测试 3: 抖音 CDP 爬虫")
    print("=" * 60)

    scraper = CdpDouyinScraper()

    # 先检查健康状态
    health = await scraper.check_health()
    if not health:
        print(f"❌ 抖音爬虫健康检查失败")
        print(f"   请确保 Chrome 已启动并登录了抖音")
        return False

    print(f"✅ 抖音爬虫健康检查通过")

    # 测试搜索
    keyword = "袜子"
    print(f"\n测试搜索关键词: '{keyword}'")
    print("请确保 Chrome 已登录抖音，否则可能无法获取数据...")

    try:
        # 使用最多点赞排序获取数据 (sort_type=1)
        results = await scraper.search_hot_videos(keyword=keyword, limit=10, sort_type=1)

        if results:
            print(f"✅ 搜索成功，获取到 {len(results)} 条视频（按最多点赞排序）")
            print("\n前 5 条结果预览:")
            for i, video in enumerate(results[:5], 1):
                stats = video.get('statistics', {})
                print(f"\n  [{i}] {video.get('title', 'N/A')[:40]}...")
                print(f"      作者: {video.get('author', {}).get('nickname', 'N/A')}")
                print(f"      点赞: {stats.get('digg_count', 'N/A')}")
                print(f"      时长: {video.get('duration', 'N/A')}")
            return True
        else:
            print(f"⚠️ 搜索返回空结果")
            print(f"   可能原因:")
            print(f"   1. Chrome 未登录抖音")
            print(f"   2. 抖音页面结构发生变化")
            print(f"   3. 网络问题或反爬限制")
            return False
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False


async def main():
    print("CDP 功能测试脚本")
    print(f"配置信息:")
    print(f"  CDP_ENABLED: {settings.CDP_ENABLED}")
    print(f"  CDP_DEBUG_HOST: {settings.CDP_DEBUG_HOST}")
    print(f"  CDP_DEBUG_PORT: {settings.CDP_DEBUG_PORT}")
    print(f"  SCRAPER_ENABLED: {settings.SCRAPER_ENABLED}")

    if not settings.CDP_ENABLED:
        print("\n⚠️ 警告: CDP_ENABLED 设置为 False")
        print("   请在 .env 文件中设置 CDP_ENABLED=true 以启用 CDP")

    if not settings.SCRAPER_ENABLED:
        print("\n⚠️ 警告: SCRAPER_ENABLED 设置为 False")
        print("   请在 .env 文件中设置 SCRAPER_ENABLED=true 以启用爬虫")

    print("\n" + "=" * 60)
    print("开始测试...")
    print("=" * 60)

    # 测试 1: 基础连接
    connection_ok = await test_cdp_connection()

    if not connection_ok:
        print("\n" + "=" * 60)
        print("❌ 基础连接测试失败，跳过后续测试")
        print("=" * 60)
        print("\n请按以下步骤排查:")
        print("1. 确保 Chrome 已安装")
        print("2. 使用以下命令启动 Chrome:")
        print(f"   chrome --remote-debugging-port={settings.CDP_DEBUG_PORT} --user-data-dir=./chrome_dev")
        print("3. 登录小红书网站")
        sys.exit(1)

    # 测试 2: 小红书爬虫
    xhs_ok = await test_xhs_scraper()

    # 测试 3: 抖音爬虫
    douyin_ok = await test_douyin_scraper()

    # 总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"CDP 基础连接: {'✅ 通过' if connection_ok else '❌ 失败'}")
    print(f"小红书爬虫:   {'✅ 通过' if xhs_ok else '❌ 失败'}")
    print(f"抖音爬虫:     {'✅ 通过' if douyin_ok else '❌ 失败'}")

    if connection_ok and xhs_ok and douyin_ok:
        print("\n🎉 所有测试通过！CDP 功能正常")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试未通过，请检查配置和 Chrome 状态")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
