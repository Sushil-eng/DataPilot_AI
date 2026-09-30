import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def main():
    try:
        from playwright.async_api import async_playwright
        print("[Playwright] Importing async_playwright successful.")
        async with async_playwright() as p:
            print("[Playwright] Launching chromium...")
            browser = await p.chromium.launch(headless=True)
            print("[Playwright] Chromium launched successfully.")
            page = await browser.new_page()
            await page.goto("https://example.com", timeout=15000)
            title = await page.title()
            print(f"[Playwright] Page loaded! Title: {title}")
            await browser.close()
            print("[Playwright] Browser closed cleanly.")
    except Exception as e:
        print(f"[Playwright] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
