from playwright.sync_api import sync_playwright, expect
import time

def verify_new_features():
    with sync_playwright() as p:
        # Launch with a specific viewport to ensure Desktop layout (Sidebar expanded)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # 1. Go to Dashboard
        print("Navigating to Dashboard...")
        page.goto("http://localhost:5173")
        page.wait_for_load_state("networkidle")

        # 2. Verify Parts Library
        print("Checking Parts Library...")
        # Use more robust locator if text is hidden, or rely on viewport fix
        page.get_by_role("button", name="Parts Library").click()
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
