# Platform-Native Prompt Rewrite

## Goal
Improve Douyin and Xiaohongshu content generation so output feels native to each platform instead of looking like hard-sell distribution copy.

## Current Problem
- The main generation prompt asks for explicit private-message and purchase guidance.
- Validation accepts and encourages DM/link/claim wording.
- Fallback templates use "扣1", "私信", discounts, and direct link language.
- Platform differences are shallow, so Xiaohongshu notes inherit short-video selling patterns.

## Implementation Plan
1. Rewrite `ai_service._build_prompt()` around platform-native behavior:
   - Douyin: retention, video action, short spoken rhythm, visual changes.
   - Xiaohongshu: cover click, collection value, real-life note style, page-by-page information gain.
2. Add authenticity and compliance constraints:
   - Avoid hard-sell phrases, keyword DM funnels, fake urgency, and unverifiable claims.
   - Make conversion soft: comments, questions, checklists, and follow-up content.
3. Adjust output validation:
   - Require interaction, not DM/purchase wording.
   - Ban common hard-sell and keyword-funnel phrases.
4. Refresh default fallback content in `task_service.py`.
5. Update focused tests for the new validation behavior.

## Verification
- Run `uv run pytest tests/test_ai_service.py`.
