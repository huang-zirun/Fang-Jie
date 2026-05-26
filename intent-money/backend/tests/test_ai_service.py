
from app.services.ai_service import _safe_fallback, _validate_output


def test_validate_output_valid():
    data = {
        "hook_text": "袜子乱放真的会拖慢出门",
        "storyboard": [
            {"shot": 1, "description": "近景展示早上翻抽屉找袜子的混乱场景", "duration": "3s"},
            {"shot": 2, "description": "特写展示袜口松和脚跟磨薄的旧袜子细节", "duration": "5s"},
            {"shot": 3, "description": "中景把通勤袜运动袜和居家袜分格整理", "duration": "5s"},
        ],
        "script_text": "以前我的袜子都是团成一堆，早上越急越找不到。后来我按通勤、运动和居家三个场景分格，袜口松了、脚跟磨薄的就淘汰。这样整理后，黑白灰基础款够日常，彩色款只留真正会搭的，搭配乐福鞋和运动鞋都更快，出门不用临时乱翻。",
        "title": "袜子抽屉整理方法 #收纳 #袜子搭配",
        "comment_template": "你们袜子最头疼的是滑跟、起球，还是颜色太多不好搭？评论区说下场景。",
        "why_it_works": "因为有效",
    }
    errors = _validate_output(data)
    assert len(errors) == 0


def test_validate_output_missing_hook():
    data = {
        "hook_text": "",
        "storyboard": [
            {"shot": 1, "description": "test", "duration": "3s"},
        ],
        "script_text": "短",
        "title": "",
        "comment_template": "",
        "why_it_works": "",
    }
    errors = _validate_output(data)
    assert len(errors) > 0


def test_validate_output_banned_phrase():
    data = {
        "hook_text": "全网最低价的袜子来了",
        "storyboard": [
            {"shot": 1, "description": "近景展示早上翻抽屉找袜子的混乱场景", "duration": "3s"},
            {"shot": 2, "description": "特写展示袜口松和脚跟磨薄的旧袜子细节", "duration": "5s"},
            {"shot": 3, "description": "中景把通勤袜运动袜和居家袜分格整理", "duration": "5s"},
        ],
        "script_text": "以前我的袜子都是团成一堆，后来按通勤和运动场景分格，袜口松了、脚跟磨薄的就淘汰，出门不用临时乱翻。",
        "title": "袜子抽屉整理方法 #收纳 #袜子搭配",
        "comment_template": "你们袜子最头疼的是滑跟还是起球？评论区说下场景。",
        "why_it_works": "有效",
    }
    errors = _validate_output(data)
    assert any("banned" in e for e in errors)


def test_validate_output_bans_hard_sell_comment():
    data = {
        "hook_text": "袜子抽屉终于不乱了",
        "storyboard": [
            {"shot": 1, "description": "近景展示早上翻抽屉找袜子的混乱场景", "duration": "3s"},
            {"shot": 2, "description": "特写展示袜口松和脚跟磨薄的旧袜子细节", "duration": "5s"},
            {"shot": 3, "description": "中景把通勤袜运动袜和居家袜分格整理", "duration": "5s"},
        ],
        "script_text": "以前我的袜子都是团成一堆，后来按通勤和运动场景分格，袜口松了、脚跟磨薄的就淘汰，出门不用临时乱翻。",
        "title": "袜子抽屉不乱了 #收纳 #袜子搭配",
        "comment_template": "想要同款袜子的姐妹扣1，我私信发你链接！",
        "why_it_works": "有效",
    }
    errors = _validate_output(data)
    assert any("banned" in e for e in errors)


def test_validate_output_missing_product_keyword():
    data = {
        "hook_text": "你穿的这个东西可能有问题",
        "storyboard": [
            {"shot": 1, "description": "近景展示早上翻抽屉找东西的混乱场景", "duration": "3s"},
            {"shot": 2, "description": "特写展示旧物磨损和变形的细节画面", "duration": "5s"},
            {"shot": 3, "description": "中景把不同场景会用到的物品分格整理", "duration": "5s"},
        ],
        "script_text": "这是一段口播文案，内容足够长来通过验证测试，但是没有提到产品关键词所以应该报错，多写一些内容凑够字数",
        "title": "日常抽屉整理方法 #收纳 #生活技巧",
        "comment_template": "你们最头疼的是哪种场景？评论区说一下。",
        "why_it_works": "有效",
    }
    errors = _validate_output(data)
    assert any("keyword" in e for e in errors)


def test_safe_fallback_replaces_old_hard_sell_content():
    fallback = {
        "hook_text": "你穿的袜子可能正在伤害你的脚",
        "storyboard": [
            {"shot": 1, "description": "近景展示早上翻抽屉找袜子的混乱场景", "duration": "3s"},
            {"shot": 2, "description": "特写展示袜口松和脚跟磨薄的旧袜子细节", "duration": "5s"},
            {"shot": 3, "description": "中景把通勤袜运动袜和居家袜分格整理", "duration": "5s"},
        ],
        "script_text": "以前我的袜子都是团成一堆，后来按通勤和运动场景分格，袜口松了、脚跟磨薄的就淘汰，出门不用临时乱翻。",
        "title": "袜子抽屉不乱了 #收纳 #袜子搭配",
        "comment_template": "想要同款袜子的姐妹扣1，我私信发你链接！",
        "why_it_works": "有效",
    }

    safe = _safe_fallback(fallback)

    assert safe["comment_template"] != fallback["comment_template"]
    assert not _validate_output(safe)
