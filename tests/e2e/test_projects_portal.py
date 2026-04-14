import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright


def test_root_redirects_or_shows_login():
    """Basic smoke E2E: ensure the app serves the portal/login page.

    Note: the application must be running locally (default port 8082) for this test.
    """
    base = "http://localhost:8082"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(base + "/", timeout=10000)
        except Exception:
            # If the server is not up, the test will raise; let pytest report it.
            raise

        # If the app redirected to login, perform login using bootstrap admin
        url = page.url
        content = page.content()

        # Basic check that page loaded / login is served or portal is visible
        assert "/login" in url or "DocuFlow" in content

        # If on login page, attempt to login with default bootstrap admin
        if "/login" in page.url or "AUTHORIZE NODE" in page.content():
            # Fill username and password and submit
            page.fill('input[placeholder="Username"]', "admin")
            page.fill('input[placeholder="Password"]', "docuflow_admin")
            # Click the authorize button
            page.click("text=AUTHORIZE NODE")

        # Navigate to Projects via the sidebar button (may require the user to be logged in)
        # The layout shows a button labeled 'Projects' when the user has access
        try:
            page.click("text=Projects", timeout=5000)
        except Exception:
            # If Projects not visible, fail the test with helpful info
            content = page.content()
            browser.close()
            raise AssertionError(
                f"Projects nav not found. Current URL: {page.url}\nContent snapshot: {content[:2000]}"
            )

        # Wait for Projects header to appear
        page.wait_for_selector("text=Управление проектами", timeout=5000)

        # Create a new project with a unique name
        import time

        proj_name = f"e2e-project-{int(time.time())}"

        # Fill the "Имя нового проекта" input and trigger the adjacent add button
        # Use JS to set the input value and click the sibling button (works reliably across renderers)
        page.eval_on_selector(
            'input[placeholder="Имя нового проекта"]',
            f"(el) => {{ el.value = '{proj_name}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); const btn = el.parentElement.querySelector('button'); if (btn) btn.click(); }}",
        )

        # Verify the new project appears in the projects list
        page.wait_for_function(
            "(name) => document.body.innerText.includes(name)", arg=proj_name, timeout=5000
        )

        # Final sanity: assert project name present in page content
        assert proj_name in page.content()
        browser.close()
