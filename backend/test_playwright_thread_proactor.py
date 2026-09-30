import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

def fetch_with_playwright_in_proactor_thread(url: str, timeout_ms: int = 15000) -> dict:
    """
    Runs Playwright in a dedicated worker thread with an explicit ProactorEventLoop on Windows.
    This guarantees subprocess creation ALWAYS works even if the caller loop is SelectorEventLoop.
    """
    async def _async_fetch():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                ]
            )
            try:
                page = await browser.new_page()
                res = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                status_code = res.status if res else 200
                html = await page.content()
                title = await page.title()
                text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                return {
                    "status": "fetched",
                    "status_code": status_code,
                    "html": html,
                    "title": title,
                    "text": text,
                    "fetcher_type": "browser",
                }
            finally:
                await browser.close()

    # Create explicit Proactor loop in this thread if on Windows
    if sys.platform == "win32":
        loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
    else:
        loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_async_fetch())
    finally:
        loop.close()

async def main():
    print("Testing fetch_with_playwright_in_proactor_thread...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, fetch_with_playwright_in_proactor_thread, "https://example.com")
    print("Result:", res.get("status"), res.get("title"), len(res.get("text", "")))

if __name__ == "__main__":
    asyncio.run(main())
