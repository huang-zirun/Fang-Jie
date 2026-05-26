# Platform-Native Prompt Rewrite Log

## 2026-05-26
- Started rewriting the AI content generation prompt for Douyin and Xiaohongshu.
- Scope is limited to prompt construction, validation, fallback content, and focused tests.
- Replaced hard-sell prompt framing with platform-native rules:
  - Douyin focuses on retention, video action, and low-pressure comments.
  - Xiaohongshu focuses on cover click, note realism, collection value, and page-by-page information gain.
- Updated validation to reject hard-sell phrases such as "扣1", "私信【", "秒发", and "小黄车".
- Replaced default fallback content with a soft收纳/搭配 example.
- Added a safe fallback guard so old structure fallback content is rejected if it fails the new validation.
- Verified with `uv run pytest tests/test_ai_service.py` (6 passed).
