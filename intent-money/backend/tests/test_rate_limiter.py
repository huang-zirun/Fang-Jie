import pytest

from app.services.rate_limiter import RateLimiter


@pytest.fixture
def limiter():
    return RateLimiter()


@pytest.mark.asyncio
async def test_allows_requests_under_limit(limiter):
    for _ in range(5):
        result = await limiter.check("user1", "xhs")
        assert result is True


@pytest.mark.asyncio
async def test_blocks_requests_over_limit(limiter):
    for _ in range(10):
        await limiter.check("user2", "xhs")
    result = await limiter.check("user2", "xhs")
    assert result is False


@pytest.mark.asyncio
async def test_different_platforms_independent(limiter):
    for _ in range(10):
        await limiter.check("user3", "xhs")
    result = await limiter.check("user3", "douyin")
    assert result is True


@pytest.mark.asyncio
async def test_different_users_independent(limiter):
    for _ in range(10):
        await limiter.check("user4", "xhs")
    result = await limiter.check("user5", "xhs")
    assert result is True
