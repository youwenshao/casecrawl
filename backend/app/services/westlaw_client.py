"""
WestlawClient - Playwright-based scraper with stealth configuration.

Implements comprehensive anti-detection measures and human-like behavior.
"""
import asyncio
import random
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import stealth

from app.core.config import get_settings
from app.core.constants import WESTLAW_SELECTORS
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for Westlaw requests."""
    
    def __init__(self):
        self.last_search_time: Optional[float] = None
        self.last_download_time: Optional[float] = None
        self.searches_this_minute = 0
        self.downloads_this_minute = 0
        self.minute_start = asyncio.get_event_loop().time()
    
    async def wait_for_search(self) -> None:
        """Wait before performing a search."""
        now = asyncio.get_event_loop().time()
        
        # Reset counters if minute has passed
        if now - self.minute_start >= 60:
            self.searches_this_minute = 0
            self.downloads_this_minute = 0
            self.minute_start = now
        
        # Check rate limit
        if self.searches_this_minute >= settings.searches_per_minute:
            wait_time = 60 - (now - self.minute_start)
            if wait_time > 0:
                logger.info("rate_limit_waiting", seconds=wait_time, action="search")
                await asyncio.sleep(wait_time)
                self.searches_this_minute = 0
                self.minute_start = asyncio.get_event_loop().time()
        
        # Add base delay between actions
        if self.last_search_time:
            elapsed = now - self.last_search_time
            min_delay = settings.delay_between_actions_min
            max_delay = settings.delay_between_actions_max
            # Add jitter (±20%)
            jitter = random.uniform(0.8, 1.2)
            required_delay = random.uniform(min_delay, max_delay) * jitter
            
            if elapsed < required_delay:
                await asyncio.sleep(required_delay - elapsed)
        
        self.last_search_time = asyncio.get_event_loop().time()
        self.searches_this_minute += 1
    
    async def wait_for_download(self) -> None:
        """Wait before performing a download."""
        now = asyncio.get_event_loop().time()
        
        # Reset counters if minute has passed
        if now - self.minute_start >= 60:
            self.searches_this_minute = 0
            self.downloads_this_minute = 0
            self.minute_start = now
        
        # Check rate limit
        if self.downloads_this_minute >= settings.downloads_per_minute:
            wait_time = 60 - (now - self.minute_start)
            if wait_time > 0:
                logger.info("rate_limit_waiting", seconds=wait_time, action="download")
                await asyncio.sleep(wait_time)
                self.downloads_this_minute = 0
                self.minute_start = asyncio.get_event_loop().time()
        
        # Add base delay
        if self.last_download_time:
            elapsed = now - self.last_download_time
            min_delay = settings.delay_between_actions_min
            max_delay = settings.delay_between_actions_max
            jitter = random.uniform(0.8, 1.2)
            required_delay = random.uniform(min_delay, max_delay) * jitter
            
            if elapsed < required_delay:
                await asyncio.sleep(required_delay - elapsed)
        
        self.last_download_time = asyncio.get_event_loop().time()
        self.downloads_this_minute += 1


class WestlawClient:
    """
    Client for interacting with Westlaw Asia.
    
    Features:
    - Stealth browser configuration
    - Human-like behavior (typing, mouse movements, delays)
    - Rate limiting
    - Session management
    - CAPTCHA detection
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.rate_limiter = RateLimiter()
        self._playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Start the browser with stealth configuration."""
        logger.info("westlaw_client_starting")
        
        self._playwright = await async_playwright().start()
        
        # Launch browser with anti-detection settings
        self.browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                f"--timezone={settings.browser_timezone}",
            ],
        )
        
        # Create context with human-like settings
        self.context = await self.browser.new_context(
            viewport={
                "width": settings.browser_viewport_width,
                "height": settings.browser_viewport_height,
            },
            locale=settings.browser_locale,
            timezone_id=settings.browser_timezone,
            user_agent=settings.user_agent if hasattr(settings, 'user_agent') else None,
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True,
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)
        
        # Create page
        self.page = await self.context.new_page()
        
        # Apply playwright-stealth
        await stealth(self.page)
        
        logger.info("westlaw_client_started")
    
    async def close(self) -> None:
        """Close the browser."""
        logger.info("westlaw_client_closing")
        
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("westlaw_client_closed")
    
    async def human_type(self, selector: str, text: str) -> None:
        """
        Type text with human-like delays.
        
        - Random delay between keystrokes
        - Occasional pauses
        """
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.click(selector)
        
        for char in text:
            # Random delay between keystrokes
            delay = random.randint(
                settings.typing_delay_min,
                settings.typing_delay_max
            )
            
            # Occasional pause (10% probability)
            if random.random() < 0.1:
                delay += random.randint(200, 500)
            
            await self.page.type(selector, char, delay=delay)
    
    async def human_click(self, selector: str) -> None:
        """
        Click element with human-like movement.
        
        Uses random offset from center of element.
        """
        if not self.page:
            raise RuntimeError("Browser not started")
        
        # Get element bounding box
        element = await self.page.query_selector(selector)
        if not element:
            raise ValueError(f"Element not found: {selector}")
        
        box = await element.bounding_box()
        if not box:
            raise ValueError(f"Cannot get bounding box for: {selector}")
        
        # Random offset from center (±20% of dimensions)
        offset_x = random.uniform(-box["width"] * 0.2, box["width"] * 0.2)
        offset_y = random.uniform(-box["height"] * 0.2, box["height"] * 0.2)
        
        x = box["x"] + box["width"] / 2 + offset_x
        y = box["y"] + box["height"] / 2 + offset_y
        
        # Move mouse with bezier curve simulation
        await self._human_mouse_move(x, y)
        
        # Random delay before click
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        await self.page.mouse.click(x, y)
    
    async def _human_mouse_move(self, target_x: float, target_y: float) -> None:
        """Simulate human-like mouse movement."""
        if not self.page:
            return
        
        # Get current position (or use center of viewport)
        current_x, current_y = settings.browser_viewport_width / 2, settings.browser_viewport_height / 2
        
        # Generate control points for bezier curve
        control_x = (current_x + target_x) / 2 + random.uniform(-100, 100)
        control_y = (current_y + target_y) / 2 + random.uniform(-100, 100)
        
        # Number of steps
        steps = random.randint(10, 20)
        
        for i in range(steps + 1):
            t = i / steps
            # Quadratic bezier curve
            x = (1 - t) ** 2 * current_x + 2 * (1 - t) * t * control_x + t ** 2 * target_x
            y = (1 - t) ** 2 * current_y + 2 * (1 - t) * t * control_y + t ** 2 * target_y
            
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))
    
    async def random_delay(self, min_sec: float, max_sec: float) -> None:
        """Add random delay with jitter."""
        jitter = random.uniform(0.8, 1.2)
        delay = random.uniform(min_sec, max_sec) * jitter
        await asyncio.sleep(delay)
    
    async def check_captcha(self) -> bool:
        """Check if CAPTCHA is present."""
        if not self.page:
            return False
        
        captcha_selectors = WESTLAW_SELECTORS["captcha"]
        
        for selector in captcha_selectors.values():
            element = await self.page.query_selector(selector)
            if element:
                logger.warning("captcha_detected")
                return True
        
        return False
    
    async def navigate(self, url: str) -> None:
        """Navigate to URL with human-like delay."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.goto(url, wait_until="domcontentloaded")
        
        # Wait for page load
        await self.random_delay(
            settings.page_load_wait_min,
            settings.page_load_wait_max
        )
        
        # Check for CAPTCHA
        if await self.check_captcha():
            raise Exception("CAPTCHA detected - manual intervention required")
    
    async def login(self, username: str, password: str, totp_code: Optional[str] = None) -> bool:
        """
        Login to Westlaw.
        
        Returns True if successful, False otherwise.
        """
        logger.info("westlaw_login_attempt")
        
        if not self.page:
            raise RuntimeError("Browser not started")
        
        # Navigate to login page
        await self.navigate(settings.westlaw_base_url)
        
        # Wait for login form
        selectors = WESTLAW_SELECTORS["login"]
        
        try:
            await self.page.wait_for_selector(
                selectors["username_input"],
                timeout=10000
            )
        except Exception:
            # Might already be logged in
            if "login" not in self.page.url.lower():
                logger.info("already_logged_in")
                return True
            raise
        
        # Enter credentials with human-like typing
        await self.human_type(selectors["username_input"], username)
        await self.random_delay(0.5, 1.5)
        
        await self.human_type(selectors["password_input"], password)
        await self.random_delay(0.5, 1.5)
        
        # Submit
        await self.human_click(selectors["submit_button"])
        
        # Check for TOTP
        if totp_code:
            try:
                await self.page.wait_for_selector(
                    selectors["totp_input"],
                    timeout=5000
                )
                await self.human_type(selectors["totp_input"], totp_code)
                await self.human_click(selectors["submit_button"])
            except Exception:
                pass  # TOTP not required
        
        # Wait for navigation
        await self.random_delay(3, 5)
        
        # Check if login successful
        if "login" in self.page.url.lower():
            logger.error("westlaw_login_failed")
            return False
        
        logger.info("westlaw_login_success")
        return True
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a search on Westlaw.
        
        Returns list of search results.
        """
        await self.rate_limiter.wait_for_search()
        
        if not self.page:
            raise RuntimeError("Browser not started")
        
        logger.info("westlaw_search", query=query)
        
        selectors = WESTLAW_SELECTORS["search"]
        
        # Enter search query
        await self.human_type(selectors["search_box"], query)
        await self.random_delay(0.5, 1.0)
        
        # Submit search
        await self.human_click(selectors["search_button"])
        
        # Wait for results
        await self.page.wait_for_load_state("networkidle")
        await self.random_delay(
            settings.post_search_wait_min,
            settings.post_search_wait_max
        )
        
        # Check for CAPTCHA
        if await self.check_captcha():
            raise Exception("CAPTCHA detected during search")
        
        # Extract results
        results = await self._extract_search_results()
        
        logger.info("westlaw_search_complete", results_count=len(results))
        return results
    
    async def _extract_search_results(self) -> List[Dict[str, Any]]:
        """Extract search results from the page."""
        if not self.page:
            return []
        
        selectors = WESTLAW_SELECTORS["document"]
        
        results = await self.page.evaluate("""
            () => {
                const results = [];
                const items = document.querySelectorAll('.result-item, .search-result');
                items.forEach(item => {
                    const citation = item.querySelector('.citation, .case-citation');
                    const parties = item.querySelector('.parties, .case-parties');
                    const date = item.querySelector('.decision-date');
                    
                    results.push({
                        citation: citation ? citation.textContent.trim() : '',
                        parties: parties ? parties.textContent.trim() : '',
                        date: date ? date.textContent.trim() : '',
                    });
                });
                return results;
            }
        """)
        
        return results
    
    async def download_document(self, download_url: str, output_path: Path) -> bool:
        """
        Download a document.
        
        Returns True if successful.
        """
        await self.rate_limiter.wait_for_download()
        
        if not self.page:
            raise RuntimeError("Browser not started")
        
        logger.info("westlaw_download", url=download_url, path=str(output_path))
        
        try:
            # Setup download handler
            async with self.page.expect_download() as download_info:
                await self.page.goto(download_url)
            
            download = await download_info.value
            await download.save_as(output_path)
            
            logger.info("westlaw_download_complete", path=str(output_path))
            return True
            
        except Exception as e:
            logger.error("westlaw_download_failed", error=str(e))
            return False
    
    async def get_page_content(self) -> str:
        """Get current page HTML content."""
        if not self.page:
            return ""
        return await self.page.content()
    
    async def get_page_text(self) -> str:
        """Get current page text content."""
        if not self.page:
            return ""
        return await self.page.evaluate("() => document.body.innerText")
