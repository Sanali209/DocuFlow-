from playwright.sync_api import sync_playwright, expect
import time

def verify_new_features():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Go to Dashboard
        print("Navigating to Dashboard...")
        page.goto("http://localhost:5173")
        page.wait_for_load_state("networkidle")

        # 2. Verify Parts Library
        print("Checking Parts Library...")
        page.get_by_role("button", name="Parts Library").click()
        # Expect H2 specific to the view
        expect(page.locator("h2").filter(has_text="Parts Library")).to_be_visible()
        time.sleep(0.5)
        page.screenshot(path="verification/parts_view.png")

        # 3. Verify Stock
        print("Checking Stock Management...")
        page.get_by_role("button", name="Stock").click()
        expect(page.locator("h2").filter(has_text="Stock Management")).to_be_visible()
        time.sleep(0.5)
        page.screenshot(path="verification/stock_view.png")

        # 4. Verify Shift Logs
        print("Checking Shift Logs...")
        page.get_by_role("button", name="Shift Logs").click()
        expect(page.locator("h2").filter(has_text="Shift Logs")).to_be_visible()
        time.sleep(0.5)
        page.screenshot(path="verification/shift_logs_view.png")

        # 5. Verify GNC Editor
        print("Checking GNC Editor...")
        page.get_by_role("button", name="GNC Editor").click()
        expect(page.locator("h2").filter(has_text="GNC Editor")).to_be_visible()
        time.sleep(0.5)
        page.screenshot(path="verification/gnc_editor_view.png")

        browser.close()
        print("Verification complete.")

if __name__ == "__main__":
    verify_new_features()
