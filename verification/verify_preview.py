from playwright.sync_api import Page, expect, sync_playwright
import os
import time

def test_image_preview(page: Page):
    # 1. Goto App
    page.goto("http://localhost:5173")

    # 2. Click "New Document"
    page.locator(".add-btn").click()

    # 3. Upload File
    # Ensure file exists
    if not os.path.exists("verification/test_image.png"):
        raise FileNotFoundError("verification/test_image.png not found")

    page.locator("input#scan").set_input_files("verification/test_image.png")

    # 4. Assert Preview Visible
    preview_img = page.locator(".preview-container img")
    expect(preview_img).to_be_visible()

    # Wait a bit for image to render fully if needed (though expect handles visibility)
    time.sleep(1)

    # 5. Screenshot
    page.screenshot(path="verification/verification.png")
    print("Screenshot saved to verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_image_preview(page)
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="verification/error.png")
            exit(1)
        finally:
            browser.close()
