import asyncio
import json
import logging
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)

# ── DOM 域 & Network 域 常量 ──────────────────────────────────────────────
_DEFAULT_WAIT_SELECTOR_TIMEOUT = 10  # seconds
_DEFAULT_POLL_INTERVAL = 0.5  # seconds


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
        self.__init_event_system()

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
        """Send a CDP command and wait for the response.

        Distinguishes between *command responses* (have ``id``) and
        *event notifications* (no ``id``).  Event notifications are
        dispatched to ``_event_handlers`` keyed by CDP event name.
        """
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

            # ── Event notification (no id) ────────────────────────
            if "id" not in data and "method" in data:
                self._dispatch_event(data["method"], data.get("params", {}))
                continue

            # ── Command response ──────────────────────────────────
            if data.get("id") == self._cmd_id:
                if "error" in data:
                    raise CdpConnectionError(f"CDP error: {data['error']}")
                return data.get("result", {})

    # ── Event handling infrastructure ────────────────────────────────────

    def __init_event_system(self) -> None:
        """(Called inside __init__) Initialise event handler storage."""
        self._event_handlers: dict[str, list] = {}

    def on(self, event: str, handler) -> None:
        """Register a callback for a CDP event (e.g. ``Network.requestWillBeSent``)."""
        self._event_handlers.setdefault(event, []).append(handler)

    def off(self, event: str, handler) -> None:
        """Remove a previously registered event callback."""
        handlers = self._event_handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    def _dispatch_event(self, event: str, params: dict) -> None:
        """Dispatch an incoming CDP event to registered handlers."""
        for handler in self._event_handlers.get(event, []):
            try:
                handler(params)
            except Exception:
                logger.exception("Error in CDP event handler for %s", event)

    # ── DOM domain methods ──────────────────────────────────────────────

    async def dom_enable(self) -> None:
        """Enable the DOM domain (required before DOM.querySelector etc.)."""
        await self._send_cmd("DOM.enable")

    async def dom_get_document(self) -> int:
        """Return the root ``nodeId`` of the DOM tree."""
        result = await self._send_cmd("DOM.getDocument", {"depth": 0})
        return result["root"]["nodeId"]

    async def query_selector(self, selector: str, node_id: int | None = None) -> int | None:
        """Run ``DOM.querySelector`` and return the *nodeId* (or ``None``)."""
        if node_id is None:
            node_id = await self.dom_get_document()
        result = await self._send_cmd("DOM.querySelector", {
            "nodeId": node_id,
            "selector": selector,
        })
        nid = result.get("nodeId", 0)
        return nid if nid else None

    async def set_file_input_files(
        self,
        selector: str,
        file_paths: list[str],
    ) -> bool:
        """Set files on an ``<input type="file">`` element.

        Flow: ``DOM.getDocument`` → ``DOM.querySelector`` →
        ``DOM.setFileInputFiles``.

        Returns ``True`` on success, ``False`` if the element was not found.
        """
        await self.dom_enable()
        node_id = await self.query_selector(selector)
        if node_id is None:
            logger.warning("set_file_input_files: element not found: %s", selector)
            return False
        await self._send_cmd("DOM.setFileInputFiles", {
            "files": file_paths,
            "nodeId": node_id,
        })
        logger.info("set_file_input_files: set %d file(s) on %s", len(file_paths), selector)
        return True

    async def wait_for_selector(
        self,
        selector: str,
        timeout: float = _DEFAULT_WAIT_SELECTOR_TIMEOUT,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
    ) -> bool:
        """Poll until ``document.querySelector(selector)`` finds an element.

        Returns ``True`` if found within *timeout*, ``False`` otherwise.
        """
        js = f'document.querySelector({json.dumps(selector)}) !== null'
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            found = await self.evaluate(js)
            if found:
                return True
            await asyncio.sleep(poll_interval)
        logger.warning("wait_for_selector: timed out (%.1fs) for %s", timeout, selector)
        return False

    async def click_element(self, selector: str) -> bool:
        """Click an element found by *selector*.

        Uses ``DOM.querySelector`` to locate, then ``Runtime.evaluate``
        to dispatch click events (mousedown → mouseup → click) for
        maximum compatibility.
        """
        if not await self.wait_for_selector(selector, timeout=5):
            logger.warning("click_element: element not found: %s", selector)
            return False
        js = f"""
        (function() {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            ['mousedown','mouseup','click'].forEach(type => {{
                el.dispatchEvent(new MouseEvent(type, {{bubbles: true, cancelable: true}}));
            }});
            return true;
        }})()
        """
        return bool(await self.evaluate(js))

    async def fill_input(
        self,
        selector: str,
        value: str,
        react_compat: bool = True,
    ) -> bool:
        """Fill an ``<input>`` or ``<textarea>`` element.

        When *react_compat* is ``True`` (default), the native React-
        compatible value setter is used so that ``onChange`` fires.
        """
        if not await self.wait_for_selector(selector, timeout=5):
            logger.warning("fill_input: element not found: %s", selector)
            return False

        escaped = json.dumps(value)  # properly quoted JSON string
        if react_compat:
            js = f"""
            (function() {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                const nativeSet = Object.getOwnPropertyDescriptor(
                    HTMLInputElement.prototype, 'value'
                )?.set || Object.getOwnPropertyDescriptor(
                    HTMLTextAreaElement.prototype, 'value'
                )?.set;
                if (nativeSet) {{
                    nativeSet.call(el, {escaped});
                }} else {{
                    el.value = {escaped};
                }}
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }})()
            """
        else:
            js = f"""
            (function() {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.value = {escaped};
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }})()
            """
        return bool(await self.evaluate(js))

    async def fill_contenteditable(self, selector: str, text: str) -> bool:
        """Fill a ``div[contenteditable]`` element (used by XHS editor).

        Sets ``innerText`` and fires an ``InputEvent``.
        """
        if not await self.wait_for_selector(selector, timeout=5):
            logger.warning("fill_contenteditable: element not found: %s", selector)
            return False
        escaped = json.dumps(text)
        js = f"""
        (function() {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.focus();
            el.innerText = {escaped};
            el.dispatchEvent(new InputEvent('input', {{
                bubbles: true,
                inputType: 'insertText',
                data: {escaped}
            }}));
            return true;
        }})()
        """
        return bool(await self.evaluate(js))

    # ── Network domain methods ──────────────────────────────────────────

    async def network_enable(self) -> None:
        """Enable the Network domain for request / response monitoring."""
        await self._send_cmd("Network.enable")

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
