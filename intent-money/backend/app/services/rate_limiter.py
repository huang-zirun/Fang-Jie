import time
from collections import defaultdict


class RateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._limits: dict[str, dict[str, int]] = {
            "xhs": {"rpm": 10, "burst": 3},
            "douyin": {"rpm": 15, "burst": 5},
        }

    async def check(self, user_id: str, platform: str) -> bool:
        limit = self._limits.get(platform, {"rpm": 10})
        key = f"{user_id}:{platform}"
        now = time.monotonic()
        cutoff = now - 60.0
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= limit["rpm"]:
            return False
        self._requests[key].append(now)
        return True


rate_limiter = RateLimiter()
