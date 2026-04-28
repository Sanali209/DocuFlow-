"""
Playwright E2E тесты для DocuFlow.

Требуют:
    uv sync
    uv run playwright install chromium

Запуск:
    # С запущенным приложением (в отдельном терминале)
    uv run python -m docuflow.main

    # E2E тесты
    uv run pytest tests/e2e/ -v --headed

    # Headless (CI)
    uv run pytest tests/e2e/ -v
"""

from playwright.sync_api import Page, expect


class TestSmokeViews:
    """Smoke тесты для проверки доступности страниц."""

    def test_home_page_loads(self, page: Page, app_url: str):
        """Проверка загрузки главной страницы."""
        page.goto(app_url)
        expect(page).to_have_title("DocuFlow Portal")
        body = page.locator("body")
        expect(body).to_be_visible()

    def test_login_page_loads(self, page: Page, app_url: str):
        """Проверка загрузки страницы логина."""
        page.goto(f"{app_url}/login")
        body = page.locator("body")
        expect(body).to_be_visible()

    def test_main_page_has_content(self, page: Page, app_url: str):
        """Проверка наличия контента на главной странице."""
        page.goto(app_url)
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        # Check body is visible
        body = page.locator("body")
        expect(body).to_be_visible()


class TestResponsiveDesign:
    """Тесты адаптивного дизайна."""

    def test_mobile_viewport(self, page: Page, app_url: str):
        """Проверка отображения на мобильном устройстве."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(app_url)
        body = page.locator("body")
        expect(body).to_be_visible()

    def test_tablet_viewport(self, page: Page, app_url: str):
        """Проверка отображения на планшете."""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(app_url)
        body = page.locator("body")
        expect(body).to_be_visible()

    def test_desktop_viewport(self, page: Page, app_url: str):
        """Проверка отображения на десктопе."""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(app_url)
        body = page.locator("body")
        expect(body).to_be_visible()


class TestPagePerformance:
    """Тесты производительности страниц."""

    def test_home_page_load_time(self, page: Page, app_url: str):
        """Проверка времени загрузки главной страницы."""
        import time

        start = time.time()
        page.goto(app_url)
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start
        # Page should load in under 5 seconds
        assert load_time < 5.0, f"Page load time {load_time}s exceeds 5s threshold"

    def test_no_console_errors(self, page: Page, app_url: str):
        """Проверка отсутствия ошибок в консоли."""
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.goto(app_url)
        page.wait_for_timeout(2000)
        # Filter out expected errors
        critical_errors = [e for e in errors if "404" not in e and "favicon" not in e.lower()]
        assert len(critical_errors) == 0, f"Console errors found: {critical_errors}"
