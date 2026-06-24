from __future__ import annotations
import re
import time
import httpx

_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


class RateLimitedClient:
    """httpx session with per-request rate limiting and lazy CSRF acquisition."""

    def __init__(self, rps: float = 1.0):
        self._min_interval = 1.0 / max(rps, 0.1)
        self._last_request = 0.0
        self._csrf_token: str | None = None
        self._warmed_up = False
        self._client = httpx.Client(
            headers={
                "User-Agent": _CHROME_UA,
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            timeout=30.0,
        )

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        gap = self._min_interval - elapsed
        if gap > 0:
            time.sleep(gap)
        self._last_request = time.monotonic()

    def get(self, url: str, **kwargs) -> httpx.Response:
        self._throttle()
        resp = self._client.get(url, **kwargs)
        if resp.status_code == 403:
            # Cloudflare — re-warm the session first
            time.sleep(2)
            self._warmed_up = False
            self._warmup()
            self._throttle()
            time.sleep(1)
            resp = self._client.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def _warmup(self) -> None:
        """Visit the Kickstarter homepage + discover page to establish cookies.

        If either request gets a 403 the warmup is a no-op and we fall back to
        the normal retry logic in get_json()."""
        if self._warmed_up:
            return
        try:
            self._throttle()
            self._client.get(
                "https://www.kickstarter.com/",
                headers={"Accept": "text/html,application/xhtml+xml,*/*"},
            )
            time.sleep(0.5)
            self._throttle()
            self._client.get(
                "https://www.kickstarter.com/discover/advanced?category_id=52&state=live",
                headers={"Accept": "text/html,application/xhtml+xml,*/*"},
            )
        except Exception:
            # Warmup failed silently — get_json will still try with retries
            pass
        self._warmed_up = True

    def get_json(self, url: str, **kwargs) -> dict:
        self._warmup()
        headers = kwargs.pop("headers", {})
        headers.setdefault("Referer", "https://www.kickstarter.com/discover/advanced")
        headers.setdefault("Accept", "application/json")
        return self.get(url, headers=headers, **kwargs).json()

    def _fetch_csrf(self) -> str:
        resp = self.get("https://www.kickstarter.com/")
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', resp.text)
        if not m:
            raise RuntimeError("CSRF token not found on Kickstarter homepage")
        return m.group(1)

    def graphql(self, query: str) -> dict:
        if not self._csrf_token:
            self._csrf_token = self._fetch_csrf()
        self._throttle()
        resp = self._client.post(
            "https://www.kickstarter.com/graph",
            json={"query": query},
            headers={
                "X-CSRF-Token": self._csrf_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": "https://www.kickstarter.com",
                "Origin": "https://www.kickstarter.com",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RateLimitedClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
