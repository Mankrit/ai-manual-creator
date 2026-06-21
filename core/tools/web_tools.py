import os
import time
import logging
from typing import Optional

logger = logging.getLogger("browser_tools")

# Global state for browser persistence
_playwright = None
_browser = None
_page = None

def get_page():
    """
    Lazy-initializes and returns a running Playwright page context.
    """
    global _playwright, _browser, _page
    if _page is None:
        from playwright.sync_api import sync_playwright
        import json
        
        # Load headless preference from config if available
        headless = True
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    cfg = json.load(f)
                    headless = cfg.get("headless", True)
        except Exception:
            pass
            
        logger.info(f"Launching Playwright (headless={headless})...")
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=headless)
        
        # Configure context with standard viewport and user agent
        context = _browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        _page = context.new_page()
        
        # Configure default timeout (15 seconds)
        _page.set_default_timeout(15000)
        
    return _page

def close_browser():
    """
    Closes the persistent Playwright browser instance.
    """
    global _playwright, _browser, _page
    logger.info("Closing Playwright browser...")
    if _page:
        try:
            _page.close()
        except Exception:
            pass
        _page = None
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright:
        try:
            _playwright.stop()
        except Exception:
            pass
        _playwright = None

def browser_navigate(url: str) -> str:
    """
    Navigate the browser to the specified URL.
    url: The target web address to open.
    """
    try:
        page = get_page()
        logger.info(f"Navigating to {url}...")
        page.goto(url)
        page.wait_for_load_state("load")
        title = page.title()
        return f"Successfully navigated to {url}. Page title: '{title}'"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"

def browser_fill(selector: str, value: str) -> str:
    """
    Fill an input field on the page with a value.
    selector: The CSS selector matching the input element.
    value: The text content to enter.
    """
    try:
        page = get_page()
        page.wait_for_selector(selector, state="visible")
        # Scroll element into view
        page.locator(selector).scroll_into_view_if_needed()
        page.fill(selector, value)
        return f"Successfully filled element '{selector}'."
    except Exception as e:
        return f"Error filling element '{selector}': {str(e)}"

def browser_click(selector: str) -> str:
    """
    Click an element on the page.
    selector: The CSS selector matching the element to click.
    """
    try:
        page = get_page()
        page.wait_for_selector(selector, state="visible")
        page.locator(selector).scroll_into_view_if_needed()
        # Perform click
        page.click(selector)
        # Wait a short moment for animations or page state changes
        time.sleep(1.0)
        return f"Successfully clicked element '{selector}'."
    except Exception as e:
        return f"Error clicking element '{selector}': {str(e)}"

def browser_screenshot(filename: str, highlight_selector: Optional[str] = None) -> str:
    """
    Capture a screenshot of the current page and save it.
    filename: The output filename (e.g. 'login_page.png'). Saved in the output/ directory.
    highlight_selector: Optional CSS selector of an element to highlight with a glowing box before screenshot.
    """
    try:
        page = get_page()
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        
        # 1. Apply glowing highlight if specified
        if highlight_selector:
            try:
                page.wait_for_selector(highlight_selector, state="visible", timeout=3000)
                page.evaluate(
                    f"""
                    const el = document.querySelector("{highlight_selector}");
                    if (el) {{
                        el.style.outline = "3px solid #ff0050";
                        el.style.outlineOffset = "3px";
                        el.style.boxShadow = "0 0 15px 5px rgba(255, 0, 80, 0.6)";
                        el.style.borderRadius = "4px";
                    }}
                    """
                )
                # Wait for style injection to register visually
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Could not apply highlight to {highlight_selector}: {str(e)}")
                
        # 2. Capture screenshot
        page.screenshot(path=filepath)
        
        # 3. Clean up highlight styles
        if highlight_selector:
            try:
                page.evaluate(
                    f"""
                    const el = document.querySelector("{highlight_selector}");
                    if (el) {{
                        el.style.outline = "";
                        el.style.outlineOffset = "";
                        el.style.boxShadow = "";
                        el.style.borderRadius = "";
                    }}
                    """
                )
            except Exception:
                pass
                
        return f"Screenshot saved successfully to output/{filename}."
    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"
