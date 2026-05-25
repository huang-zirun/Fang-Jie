import asyncio
import json
import logging
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)


class CdpConnectionError(Exception):
    """Raised when CDP connection to Chrome fails."""

    def __init__(self, message: str):
        super().__init__(message)


class CdpBrowser:
    """Manage a CDP connection to a Chrome instance with remote debugging enabled.

    Usage:
        browser = CdpBrowser(host="127.0.0.1", port=9222)
        await browser.navigate("https://www.xiaohongshu.com/search_result?keyword=袜子")
        result = await browser.evaluate("document.title")
        text = await await browser.get_page_text()
        await browser.close()
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9222):
        self._host = host
        self._port = port
        self._ws: websockets.ClientConnection | None = None
        self._page_id: str | None = None
        self._cmd_id = 0

    @property
    def _cdp_base(self) -> str:
        return f"http://{self._host}:{self._port}"

    async def _get_or_create_page(self) -> str:
        """Get existing page id or create a new one."""
        if self._page_id:
            return self._page_id

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self._cdp_base}/json/list")
            resp.raise_for_status()
            pages = resp.json()

        # Prefer an existing page, skip service workers and newtab
        for p in pages:
            if p.get("type") == "page" and not p.get("url", "").startswith("chrome://"):
                self._page_id = p["id"]
                return self._page_id

        # Create a new page
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self._cdp_base}/json/new")
            resp.raise_for_status()
            page = resp.json()
        self._page_id = page["id"]
        return self._page_id

    async def _connect_ws(self) -> websockets.ClientConnection:
        """Establish WebSocket connection to the page."""
        if self._ws:
            try:
                pong = await self._ws.ping()
                await asyncio.wait_for(pong, timeout=2)
                return self._ws
            except Exception:
                # Connection is dead, close it
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None

        page_id = await self._get_or_create_page()
        ws_url = f"ws://{self._host}:{self._port}/devtools/page/{page_id}"

        try:
            self._ws = await websockets.connect(ws_url, max_size=10 * 1024 * 1024)
        except Exception as e:
            raise CdpConnectionError(f"Failed to connect to Chrome CDP at {ws_url}: {e}") from e

        return self._ws

    async def _send_cmd(self, method: str, params: dict | None = None) -> dict:
        """Send a CDP command and wait for the response."""
        ws = await self._connect_ws()
        self._cmd_id += 1
        cmd = {"id": self._cmd_id, "method": method}
        if params:
            cmd["params"] = params

        await ws.send(json.dumps(cmd))

        # Read responses until we get our id
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._cmd_id:
                if "error" in data:
                    raise CdpConnectionError(f"CDP error: {data['error']}")
                return data.get("result", {})

    async def navigate(self, url: str, wait_seconds: float = 6.0) -> None:
        """Navigate to a URL and wait for page load."""
        logger.info(f"CDP navigating to: {url}")
        await self._send_cmd("Page.navigate", {"url": url})
        await self._wait(wait_seconds)

    async def evaluate(self, expression: str) -> Any:
        """Execute JavaScript in the page and return the result."""
        result = await self._send_cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
        })
        return result.get("result", {}).get("value")

    async def get_page_text(self) -> str:
        """Get the full text content of the current page."""
        text = await self.evaluate("document.body.innerText")
        return str(text) if text else ""

    async def get_html(self) -> str:
        """Get the full HTML of the current page."""
        html = await self.evaluate("document.documentElement.outerHTML")
        return str(html) if html else ""

    async def _wait(self, seconds: float) -> None:
        """Wait for page to settle."""
        await asyncio.sleep(seconds)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def check_health(self) -> bool:
        """Check if Chrome CDP is reachable."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._cdp_base}/json/version")
                return resp.status_code == 200
        except Exception:
            return False
