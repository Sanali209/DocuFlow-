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

        url = page.url
        content = page.content()
        # Accept either redirect to /login or page content containing 'DocuFlow'
        assert "/login" in url or "DocuFlow" in content
        browser.close()

