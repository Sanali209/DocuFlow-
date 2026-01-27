from playwright.sync_api import Page, expect, sync_playwright
import os
import time

def test_content_edit(page: Page):
    # 1. Goto App
    page.goto("http://localhost:5173")

    # 2. Click "New Document"
    page.locator(".add-btn").click()

    # 3. Assert Content Textarea Exists and is visible
    content_area = page.locator("textarea#content")
    expect(content_area).to_be_visible()

    # 4. Assert Image Preview is GONE
    preview_img = page.locator(".preview-container img")
    expect(preview_img).not_to_be_visible()

    # 5. Type into textarea (simulating scan or manual edit)
    content_area.fill("# Recognized Content\n\nThis is a test.")

    # 6. Screenshot
    page.screenshot(path="verification/verification_content.png")
    print("Screenshot saved to verification/verification_content.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_content_edit(page)
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="verification/error_content.png")
            exit(1)
        finally:
            browser.close()
