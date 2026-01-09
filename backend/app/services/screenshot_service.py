"""
Screenshot capture service using Playwright
"""
import base64
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        logger.info("="*80)
        logger.info("📸 SCREENSHOT CAPTURE SERVICE - START")
        logger.info("="*80)
        logger.info(f"🌐 Target URL: {url}")
        logger.info(f"📐 Viewport: {width}x{height}")

        try:
            logger.info("🚀 Launching Playwright...")
            async with async_playwright() as p:
                logger.info("🌐 Launching Chromium browser (headless mode)...")
                # Launch browser in headless mode
                browser = await p.chromium.launch(headless=True)
                logger.info("✅ Browser launched successfully")

                # Create a new page with specified viewport
                logger.info(f"📄 Creating new page with viewport {width}x{height}...")
                page = await browser.new_page(viewport={"width": width, "height": height})
                logger.info("✅ Page created successfully")

                # Navigate to the URL with a timeout of 30 seconds
                logger.info(f"🔗 Navigating to {url} (timeout: 30s, wait_until: networkidle)...")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                logger.info("✅ Page loaded successfully (network idle)")

                # Wait a bit more to ensure everything is rendered
                logger.info("⏳ Waiting 2 seconds for rendering to complete...")
                await asyncio.sleep(2)
                logger.info("✅ Rendering wait complete")

                # Take screenshot
                logger.info("📸 Capturing screenshot...")
                screenshot_bytes = await page.screenshot(type="png", full_page=False)
                logger.info(f"✅ Screenshot captured ({len(screenshot_bytes)} bytes)")

                # Close browser
                logger.info("🔒 Closing browser...")
                await browser.close()
                logger.info("✅ Browser closed")

                # Convert to base64 with data URI prefix
                logger.info("🔄 Converting to base64...")
                base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                data_uri = f"data:image/png;base64,{base64_image}"
                logger.info(f"✅ Conversion complete (total size: {len(data_uri)} bytes)")
                logger.info("="*80)
                logger.info("✅ SCREENSHOT CAPTURE SERVICE - SUCCESS")
                logger.info("="*80)
                return data_uri

        except PlaywrightTimeoutError as e:
            logger.error("="*80)
            logger.error("❌ SCREENSHOT CAPTURE FAILED - TIMEOUT")
            logger.error("="*80)
            logger.error(f"URL: {url}")
            logger.error(f"Error: Timeout while loading {url}")
            logger.error(f"Details: {str(e)}")
            logger.error("Possible causes:")
            logger.error("  - URL is not accessible")
            logger.error("  - WebContainer hasn't started yet")
            logger.error("  - Network issues preventing page load")
            logger.error("="*80)
            return None
        except Exception as e:
            logger.error("="*80)
            logger.error("❌ SCREENSHOT CAPTURE FAILED - EXCEPTION")
            logger.error("="*80)
            logger.error(f"URL: {url}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error("="*80)

            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            logger.error("="*80)

            logger.error("Possible causes:")
            logger.error("  - Playwright not installed: pip install playwright")
            logger.error("  - Chromium not installed: playwright install chromium")
            logger.error("  - System missing dependencies")
            logger.error("="*80)
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
