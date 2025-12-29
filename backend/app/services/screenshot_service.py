"""
Screenshot capture service using Playwright
"""
import base64
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


class ScreenshotService:
    """Service for capturing screenshots of web pages using Playwright"""

    @staticmethod
    async def capture_screenshot(url: str, width: int = 1280, height: int = 720) -> Optional[str]:
        """
        Capture a screenshot of the given URL and return as base64 string

        Args:
            url: The URL to capture
            width: Viewport width in pixels (default 1280)
            height: Viewport height in pixels (default 720)

        Returns:
            Base64 encoded PNG image with data URI prefix, or None if capture fails
        """
        try:
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(headless=True)

                # Create a new page with specified viewport
                page = await browser.new_page(viewport={"width": width, "height": height})

                # Navigate to the URL with a timeout of 30 seconds
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait a bit more to ensure everything is rendered
                await asyncio.sleep(2)

                # Take screenshot
                screenshot_bytes = await page.screenshot(type="png", full_page=False)

                # Close browser
                await browser.close()

                # Convert to base64 with data URI prefix
                base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                return f"data:image/png;base64,{base64_image}"

        except PlaywrightTimeoutError:
            print(f"ERROR: Timeout while loading {url}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to capture screenshot: {e}")
            return None

    @staticmethod
    def capture_screenshot_sync(url: str, width: int = 1280, height: int = 720) -> Optional[str]:
        """
        Synchronous wrapper for capture_screenshot

        Args:
            url: The URL to capture
            width: Viewport width in pixels (default 1280)
            height: Viewport height in pixels (default 720)

        Returns:
            Base64 encoded PNG image with data URI prefix, or None if capture fails
        """
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(
                ScreenshotService.capture_screenshot(url, width, height)
            )
        finally:
            loop.close()
