from playwright.sync_api import sync_playwright, expect
import time

def verify_frontend(page):
    page.goto("http://localhost:5173")

    # Wait for title or header
    expect(page.get_by_role("heading", name="DocuFlow")).to_be_visible()

    # Click New Document
    page.get_by_role("button", name="New Document").click()

    # Check for Modal
    expect(page.get_by_role("heading", name="New Document", exact=True)).to_be_visible()

    # Check for Scan Input
    expect(page.get_by_label("Scan Document (Image)")).to_be_visible()

    # Check for Name Input
    expect(page.get_by_label("Name")).to_be_visible()

    # Take screenshot of the Form
    page.screenshot(path="verification/verification_form.png")

    # Close modal
    page.get_by_role("button", name="Cancel").click()

    # Add a document manually to test list and buttons
    page.get_by_role("button", name="New Document").click()
    page.get_by_label("Name").fill("Test Doc Playwright")
    page.get_by_role("button", name="Register Document").click()

    # Wait for list update
    expect(page.get_by_text("Test Doc Playwright")).to_be_visible()

    # Check for View and Edit buttons
    expect(page.get_by_title("View Content").first).to_be_visible()
    expect(page.get_by_title("Edit").first).to_be_visible()

    # Take screenshot of List
    page.screenshot(path="verification/verification_list.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_frontend(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
            raise e
        finally:
            browser.close()
