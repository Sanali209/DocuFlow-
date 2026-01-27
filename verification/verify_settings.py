from playwright.sync_api import sync_playwright, expect

def verify_settings(page):
    page.goto("http://localhost:5173")

    # Check Settings Button is visible
    settings_btn = page.get_by_title("Settings")
    expect(settings_btn).to_be_visible()

    # Click Settings
    settings_btn.click()

    # Check Modal Title
    expect(page.get_by_role("heading", name="Settings")).to_be_visible()

    # Check Input
    input_field = page.get_by_label("OCR Service URL")
    expect(input_field).to_be_visible()

    # Wait for value to load (it might take a moment if async)
    # The default is http://localhost:7860 if backend is reachable
    # However, pytest execution might have changed it to http://custom-ocr.com in the DB
    # Let's verify it has SOME value, or just proceed to set it.

    # Change value
    input_field.fill("http://new-ocr-url.com")

    # Save
    page.get_by_role("button", name="Save Settings").click()

    # Expect success message
    expect(page.get_by_text("Settings saved successfully")).to_be_visible()

    # Take screenshot
    page.screenshot(path="verification/settings_modal.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_settings(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/settings_error.png")
            raise e
        finally:
            browser.close()
