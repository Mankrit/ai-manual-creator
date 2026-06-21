import os
from core.tools.web_tools import (
    browser_navigate,
    browser_fill,
    browser_click,
    browser_screenshot,
    close_browser
)

def main():
    print("Starting browser verification test...")
    
    # 1. Navigation Test
    # Let's open a fast, lightweight page (e.g., wikipedia.org)
    url = "https://www.wikipedia.org/"
    print(f"Testing navigation to: {url}")
    nav_result = browser_navigate(url)
    print(nav_result)
    
    # 2. Input Fill Test
    # Wikipedia's search input CSS selector is normally "#searchInput"
    search_selector = "#searchInput"
    search_query = "Artificial Intelligence"
    print(f"Testing form input on '{search_selector}' with query '{search_query}'...")
    fill_result = browser_fill(search_selector, search_query)
    print(fill_result)
    
    # 3. Screenshot Capture with Glowing Highlight Test
    # Let's take a screenshot and highlight the search input box
    screenshot_file = "wiki_search.png"
    print(f"Capturing screenshot '{screenshot_file}' with highlight on search box...")
    screenshot_result = browser_screenshot(screenshot_file, highlight_selector=search_selector)
    print(screenshot_result)
    
    # 4. Form Submit / Click Test
    # Wikipedia's search button is normally ".pure-button-primary-progressive" or "button[type='submit']"
    btn_selector = "button[type='submit']"
    print(f"Testing click on '{btn_selector}' to perform search...")
    click_result = browser_click(btn_selector)
    print(click_result)
    
    # 5. Final Screenshot Test
    final_screenshot = "wiki_results.png"
    print(f"Capturing final screenshot '{final_screenshot}'...")
    final_result = browser_screenshot(final_screenshot)
    print(final_result)
    
    # 6. Close Browser
    close_browser()
    
    print("\n----------------------------------------")
    print("Verification Check:")
    if os.path.exists(os.path.join("output", screenshot_file)):
        print(f"SUCCESS: Screenshot output/{screenshot_file} exists.")
    else:
        print(f"FAILURE: Screenshot output/{screenshot_file} does not exist.")
        
    if os.path.exists(os.path.join("output", final_screenshot)):
        print(f"SUCCESS: Screenshot output/{final_screenshot} exists.")
    else:
        print(f"FAILURE: Screenshot output/{final_screenshot} does not exist.")
    print("----------------------------------------")

if __name__ == "__main__":
    main()
