"""
Source Fetcher — Resilient Web Extraction Engine

Architecture:
    HTTPFetcher (requests + BeautifulSoup)
        ↓ (200 OK?)
    YES → Return content
    NO / 403 / timeout / error / JS-heavy
        ↓
    BrowserFetcher (Playwright Chromium)
        ↓ (Success?)
    YES → Return browser content
    NO → Return unavailable status (blocked / timeout / failed / browser_unavailable)

No CAPTCHA / anti-bot bypass, no proxy rotation, no security evasion.
Clean logging and resilient fallback execution.
"""

import sys
import asyncio
import ipaddress
import logging
import socket
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

# Ensure Windows event loop policy supports Playwright Chromium subprocesses
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

import requests
from bs4 import BeautifulSoup

from ..config import get_settings

logger = logging.getLogger(__name__)

# SSRF Protection
BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "0", "localhost.localdomain"}

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def is_ssrf_safe_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate http/https URL and ensure no local/private network targeting."""
    if not url or not isinstance(url, str):
        return False, "Invalid or empty URL."

    url_str = url.strip()
    try:
        parsed = urlparse(url_str)
    except Exception as exc:
        return False, f"Malformed URL: {exc}"

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"Forbidden URL scheme '{scheme}'. Only http:// and https:// are allowed."

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL missing host name."

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
        return False, f"Access to local/internal network target '{hostname}' is blocked."

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False, f"Access to private/internal IP '{hostname}' is blocked."
    except ValueError:
        try:
            resolved_ip_str = socket.gethostbyname(hostname)
            resolved_ip = ipaddress.ip_address(resolved_ip_str)
            if resolved_ip.is_private or resolved_ip.is_loopback or resolved_ip.is_link_local or resolved_ip.is_unspecified:
                return False, f"Domain '{hostname}' resolves to private IP '{resolved_ip_str}' and is blocked."
        except Exception:
            pass

    return True, None


class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fetch_sync(self, url: str) -> Dict[str, Any]:
        pass


class HTTPFetcher(BaseFetcher):
    """
    Standard HTTP Content Fetcher using `requests` and `BeautifulSoup`.
    Fetches raw HTML with standard browser headers and timeout handling.
    """

    def __init__(self, timeout: Optional[int] = None, user_agent: Optional[str] = None):
        settings = get_settings()
        self.timeout = timeout or settings.fetch_timeout
        self.user_agent = user_agent or settings.user_agent or DEFAULT_USER_AGENT
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_sync(self, url: str) -> Dict[str, Any]:
        is_safe, error_reason = is_ssrf_safe_url(url)
        if not is_safe:
            logger.warning("SSRF blocked URL fetch: url=%s reason=%s", url, error_reason)
            return self._build_response(url, status="failed", status_code=400, error=error_reason or "Forbidden URL")

        session = requests.Session()

        try:
            response = session.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
            )

            status_code = response.status_code
            content_type = response.headers.get("Content-Type", "text/html").split(";")[0].strip().lower()
            html_content = response.text or ""

            # Check HTTP 403 / 401 / 429
            if status_code in (401, 403, 407, 429, 451):
                return self._build_response(
                    url=url,
                    status="blocked",
                    status_code=status_code,
                    content_type=content_type,
                    html=html_content,
                    error="Source blocked automated access",
                )

            if status_code >= 400:
                return self._build_response(
                    url=url,
                    status="failed",
                    status_code=status_code,
                    content_type=content_type,
                    html=html_content,
                    error=f"HTTP status {status_code}",
                )

            # Extract title & visible text with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)

            for element in soup(["script", "style", "head", "noscript", "svg", "header", "footer", "nav"]):
                element.decompose()

            extracted_text = soup.get_text(separator=" ", strip=True)

            return self._build_response(
                url=url,
                status="fetched",
                status_code=status_code,
                content_type=content_type,
                html=html_content,
                text=extracted_text,
                title=title,
                error=None,
            )

        except requests.exceptions.Timeout:
            return self._build_response(
                url=url,
                status="timeout",
                status_code=504,
                error=f"Fetch timeout after {self.timeout}s",
            )
        except requests.exceptions.SSLError:
            return self._build_response(url, status="failed", status_code=525, error="SSL certificate validation failed")
        except requests.exceptions.ConnectionError:
            return self._build_response(url, status="failed", status_code=502, error="Failed to connect to target server")
        except Exception as exc:
            return self._build_response(url, status="failed", status_code=500, error=f"Fetch error: {type(exc).__name__}")

    async def fetch(self, url: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self.fetch_sync, url)

    def _build_response(
        self,
        url: str,
        status: str,
        status_code: int,
        content_type: str = "text/html",
        html: str = "",
        text: str = "",
        title: str = "",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "url": url,
            "status": status,
            "status_code": status_code,
            "http_status": status_code,
            "content_type": content_type,
            "html": html,
            "text": text,
            "title": title,
            "error": error,
            "fetcher_type": "http",
        }


def _fetch_browser_worker(url: str, timeout_ms: int, user_agent: str) -> Dict[str, Any]:
    """
    Executes Playwright Chromium in a dedicated event loop with ProactorEventLoop on Windows.
    This guarantees subprocess creation (create_subprocess_exec) works reliably on Windows across all frameworks.
    """
    async def _async_browser_run():
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                ],
            )
            try:
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                )
                page = await context.new_page()
                response = await page.goto(
                    url,
                    timeout=timeout_ms,
                    wait_until="domcontentloaded",
                )
                status_code = response.status if response else 200

                if status_code in (401, 403, 407, 429, 451):
                    return {
                        "url": url,
                        "status": "blocked",
                        "status_code": status_code,
                        "http_status": status_code,
                        "content_type": "text/html",
                        "html": "",
                        "text": "",
                        "title": "",
                        "error": "Source blocked automated access",
                        "fetcher_type": "browser",
                    }

                if status_code >= 400:
                    return {
                        "url": url,
                        "status": "failed",
                        "status_code": status_code,
                        "http_status": status_code,
                        "content_type": "text/html",
                        "html": "",
                        "text": "",
                        "title": "",
                        "error": f"Browser fetch status {status_code}",
                        "fetcher_type": "browser",
                    }

                html_content = await page.content()
                title = await page.title()
                extracted_text = await page.evaluate("() => document.body ? document.body.innerText : ''")

                return {
                    "url": url,
                    "status": "fetched",
                    "status_code": status_code,
                    "http_status": status_code,
                    "content_type": "text/html",
                    "html": html_content,
                    "text": extracted_text or "",
                    "title": title or "",
                    "error": None,
                    "fetcher_type": "browser",
                }
            finally:
                await browser.close()

    if sys.platform == "win32":
        loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
    else:
        loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_async_browser_run())
    finally:
        loop.close()


class BrowserFetcher(BaseFetcher):
    """
    Headless Browser Fetcher using Playwright for single-page applications or JS-heavy sites.
    Precisely classifies errors between 'playwright_not_installed' and 'browser_startup_failed'.
    """

    def __init__(self, timeout_ms: Optional[int] = None, user_agent: Optional[str] = None):
        settings = get_settings()
        self.browser_timeout = timeout_ms or getattr(settings, "browser_timeout", 20000)
        self.user_agent = user_agent or settings.user_agent or DEFAULT_USER_AGENT

    def fetch_sync(self, url: str) -> Dict[str, Any]:
        return _fetch_browser_worker(url, self.browser_timeout, self.user_agent)

    async def fetch(self, url: str) -> Dict[str, Any]:
        is_safe, error_reason = is_ssrf_safe_url(url)
        if not is_safe:
            return self._build_response(url, status="failed", status_code=400, error=error_reason or "Forbidden URL")

        # 1. Check if playwright package is installed
        try:
            import playwright
        except (ImportError, ModuleNotFoundError) as imp_err:
            msg = "Playwright package is not installed"
            logger.warning("[BrowserFetcher] %s: %s", msg, imp_err)
            return self._build_response(url, status="playwright_not_installed", status_code=501, error=msg)

        # 2. Run browser worker in executor with Proactor loop support
        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(
                None,
                _fetch_browser_worker,
                url,
                self.browser_timeout,
                self.user_agent,
            )
            return res
        except Exception as exc:
            msg = f"Playwright browser startup failed: {type(exc).__name__} - {str(exc)[:200]}"
            logger.error("[BrowserFetcher] %s (url=%s)", msg, url)
            return self._build_response(
                url=url,
                status="browser_startup_failed",
                status_code=502,
                error=msg,
            )

    def _build_response(
        self,
        url: str,
        status: str,
        status_code: int,
        content_type: str = "text/html",
        html: str = "",
        text: str = "",
        title: str = "",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "url": url,
            "status": status,
            "status_code": status_code,
            "http_status": status_code,
            "content_type": content_type,
            "html": html,
            "text": text,
            "title": title,
            "error": error,
            "fetcher_type": "browser",
        }


class SourceFetcher:
    """
    Main source fetcher interface executing:
    HTTP GET → 200 OK? → YES: return content
    NO / 403 / timeout / error / sparse → BrowserFetcher (Playwright) → return browser content
    """

    def __init__(
        self,
        mode: Optional[str] = None,
        timeout: Optional[int] = None,
        browser_timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
    ):
        settings = get_settings()
        self.mode = (mode or getattr(settings, "fetcher_mode", "auto")).strip().lower()
        self.timeout = timeout or settings.fetch_timeout
        self.browser_timeout = browser_timeout or getattr(settings, "browser_timeout", 20000)
        self.user_agent = user_agent or settings.user_agent

        self.http_fetcher = HTTPFetcher(timeout=self.timeout, user_agent=self.user_agent)
        self.browser_fetcher = BrowserFetcher(timeout_ms=self.browser_timeout, user_agent=self.user_agent)

    async def fetch(self, url: str, force_mode: Optional[str] = None) -> Dict[str, Any]:
        active_mode = (force_mode or self.mode).lower()
        domain = urlparse(url).netloc or url

        if active_mode == "browser":
            logger.info("[Fetcher] Executing BrowserFetcher for %s", domain)
            res = await self.browser_fetcher.fetch(url)
            if res.get("status") in ("playwright_not_installed", "browser_startup_failed"):
                logger.warning("[Fetcher] Browser unavailable, falling back to HTTP for %s", domain)
                res = await self.http_fetcher.fetch(url)
            return res

        # 1. HTTP Request
        res = await self.http_fetcher.fetch(url)

        status_code = res.get("status_code", 0)
        status = res.get("status", "")
        has_text = len(res.get("text", "")) >= 100

        # YES → 200 OK with usable text content
        if status_code == 200 and status == "fetched" and has_text:
            logger.info("[Fetcher] HTTP fetch successful for %s", domain)
            return res

        # NO / 403 / timeout / JS-heavy / error
        if status == "blocked" or status_code in (401, 403, 407, 429, 451):
            logger.warning("[Fetcher] HTTP blocked: %s", domain)
        elif status == "timeout" or status_code == 504:
            logger.warning("[Fetcher] Timeout: %s", domain)
        else:
            logger.info("[Fetcher] HTTP request non-200/sparse (status %s) for %s", status_code, domain)

        # 2. BrowserFetcher Fallback
        logger.info("[Fetcher] Trying browser fallback for %s", domain)
        browser_res = await self.browser_fetcher.fetch(url)

        if browser_res.get("status") == "playwright_not_installed":
            logger.warning("[Fetcher] Browser unavailable: Playwright package is not installed")
            logger.info("[Fetcher] Skipping unavailable source: %s", domain)
            return res

        if browser_res.get("status") == "browser_startup_failed":
            logger.warning("[Fetcher] Browser startup failed for %s: %s", domain, browser_res.get("error"))
            logger.info("[Fetcher] Skipping unavailable source: %s", domain)
            return browser_res

        if browser_res.get("status") == "fetched" and browser_res.get("status_code") == 200:
            logger.info("[Fetcher] Browser fetch successful for %s", domain)
            return browser_res

        if browser_res.get("status") == "blocked":
            logger.warning("[Fetcher] Browser blocked: %s", domain)
            logger.info("[Fetcher] Skipping unavailable source: %s", domain)
            return browser_res

        if browser_res.get("status") == "timeout":
            logger.warning("[Fetcher] Timeout: %s", domain)
            logger.info("[Fetcher] Skipping unavailable source: %s", domain)
            return browser_res

        logger.warning("[Fetcher] Browser fallback failed for %s", domain)
        logger.info("[Fetcher] Skipping unavailable source: %s", domain)
        return browser_res if browser_res.get("error") else res

    def fetch_sync(self, url: str, force_mode: Optional[str] = None) -> Dict[str, Any]:
        return asyncio.run(self.fetch(url, force_mode=force_mode))
