
from app.services.ai_service import _validate_output


def test_validate_output_valid():
    data = {
        "hook_text": "你穿的袜子可能正在伤害你的脚",
        "storyboard": [
            {"shot": 1, "description": "test", "duration": "3s"},
            {"shot": 2, "description": "test", "duration": "5s"},
            {"shot": 3, "description": "test", "duration": "5s"},
        ],
        "script_text": "这是一段关于袜子的口播文案，内容足够长来通过验证测试，需要超过五十个字才能通过校验，所以这里多写一些内容",
        "title": "测试标题 #话题",
        "comment_template": "评论区话术",
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
            {"shot": 1, "description": "test", "duration": "3s"},
            {"shot": 2, "description": "test", "duration": "5s"},
            {"shot": 3, "description": "test", "duration": "5s"},
        ],
        "script_text": "这是一段关于袜子的口播文案，内容足够长来通过验证测试，需要超过五十个字才能通过校验，所以这里多写一些内容",
        "title": "测试标题",
        "comment_template": "话术",
        "why_it_works": "有效",
    }
    errors = _validate_output(data)
    assert any("banned" in e for e in errors)


def test_validate_output_missing_product_keyword():
    data = {
        "hook_text": "你穿的这个东西可能有问题",
        "storyboard": [
            {"shot": 1, "description": "test", "duration": "3s"},
            {"shot": 2, "description": "test", "duration": "5s"},
            {"shot": 3, "description": "test", "duration": "5s"},
        ],
        "script_text": "这是一段口播文案，内容足够长来通过验证测试，但是没有提到产品关键词所以应该报错，多写一些内容凑够字数",
        "title": "测试标题",
        "comment_template": "话术",
        "why_it_works": "有效",
    }
    errors = _validate_output(data)
    assert any("keyword" in e for e in errors)
