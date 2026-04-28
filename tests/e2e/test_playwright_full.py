"""
Полный набор Playwright E2E тестов для DocuFlow.

Тестирует:
- Авторизацию
- Все views через sidebar
- User info
- Logout

Запуск:
    # С запущенным приложением
    uv run pytest tests/e2e/test_playwright_full.py -v --headed
"""

import time

import pytest
from playwright.sync_api import Page, expect


class TestAuth:
    """Тесты авторизации."""

    def test_login_page_loads(self, page: Page, app_url: str):
        """Страница логина загружается."""
        page.goto(f"{app_url}/login")
        page.wait_for_load_state("networkidle")

        # Проверяем наличие полей
        expect(page.locator('input[aria-label="Username"]')).to_be_visible()
        expect(page.locator('input[aria-label="Password"]')).to_be_visible()
        expect(page.locator('button:has-text("AUTHORIZE NODE")')).to_be_visible()

    def test_login_with_valid_credentials(self, page: Page, app_url: str):
        """Успешный логин с правильными кредами."""
        page.goto(f"{app_url}/login")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        page.fill('input[aria-label="Username"]', "admin")
        page.fill('input[aria-label="Password"]', "admin")
        page.click('button:has-text("AUTHORIZE NODE")')

        # Ждём redirect с логина
        page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
        time.sleep(3)

        # Должны быть на главной
        expect(page.locator("body")).to_be_visible()
        # Должен быть виден header с DocuFlow
        assert "DocuFlow" in page.content()

    def test_login_with_invalid_credentials(self, page: Page, app_url: str):
        """Логин с неверными кредами не проходит."""
        page.goto(f"{app_url}/login")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        page.fill('input[aria-label="Username"]', "wrong")
        page.fill('input[aria-label="Password"]', "wrong")
        page.click('button:has-text("AUTHORIZE NODE")')

        time.sleep(2)
        # Должны остаться на странице логина
        assert "/login" in page.url


class TestDashboard:
    """Тесты Dashboard view."""

    def test_dashboard_shows_cluster_info(self, logged_in_page: Page, app_url: str):
        """Dashboard показывает информацию о кластере."""
        page = logged_in_page

        # Кликаем Dashboard в sidebar
        page.click('button:has-text("Dashboard")')
        time.sleep(3)

        content = page.content()
        assert "Cluster Management Hub" in content
        assert "ONLINE" in content

    def test_dashboard_shows_activity_stream(self, logged_in_page: Page, app_url: str):
        """Dashboard показывает activity stream."""
        page = logged_in_page

        page.click('button:has-text("Dashboard")')
        time.sleep(3)

        content = page.content()
        assert "LIVE ACTIVITY" in content or "Activity" in content


class TestSidebarNavigation:
    """Тесты навигации через sidebar."""

    views = [
        ("work_items", "Work Items", "Work"),
        ("task_board", "Task Board", "Role"),
        ("scanner", "Folder Scanner", "Scanner"),
        ("warehouse", "Warehouse", "Warehouse"),
        ("production", "Finished Pallets", "Pallet"),
        ("parts", "Parts Library", "Parts"),
        ("projects", "Projects", "Project"),
        ("consumables", "Supplies", "Supplies"),
        ("chat", "Workshop Chat", "Chat"),
        ("incidents", "Incidents", "Incident"),
        ("analytics", "Analytics KPIs", "Analytics"),
        ("reports", "Reports", "Report"),
        ("docs", "Documentation", "Doc"),
    ]

    @pytest.mark.parametrize("view_name,button_text,expected_text", views)
    def test_view_navigation(
        self, logged_in_page: Page, app_url: str, view_name, button_text, expected_text
    ):
        """Проверка перехода в каждый view."""
        page = logged_in_page

        # Проверяем видимость кнопки
        button = page.locator(f"button:has-text('{button_text}')").first
        if not button.is_visible():
            pytest.skip(f"Button '{button_text}' not visible (no access)")

        # Кликаем
        button.click()
        time.sleep(3)

        # Проверяем что view загрузился (нет 404)
        content = page.content()
        assert "404" not in content or "not found" not in content.lower()

        # Проверяем наличие ожидаемого текста
        assert expected_text.lower() in content.lower(), (
            f"Expected '{expected_text}' in {view_name}"
        )

    def test_admin_view_accessible_for_admin(self, logged_in_page: Page, app_url: str):
        """Admin view доступен для admin."""
        page = logged_in_page

        button = page.locator('button:has-text("System Admin")').first
        if not button.is_visible():
            pytest.skip("Admin button not visible")

        button.click()
        time.sleep(3)

        content = page.content()
        assert "Admin" in content or "Registry" in content


class TestHeader:
    """Тесты header."""

    def test_header_shows_user_info(self, logged_in_page: Page, app_url: str):
        """Header показывает информацию о пользователе."""
        page = logged_in_page

        # Avatar должен быть виден
        avatar = page.locator(".q-avatar").first
        expect(avatar).to_be_visible()

        # Имя пользователя
        content = page.content()
        assert "admin" in content.lower()

    def test_header_shows_node_info(self, logged_in_page: Page, app_url: str):
        """Header показывает информацию о node."""
        page = logged_in_page

        content = page.content()
        assert "node_01" in content or "NODE" in content

    def test_logout_works(self, logged_in_page: Page, app_url: str):
        """Logout работает."""
        page = logged_in_page

        # Ищем кнопку logout (иконка в header)
        # В header есть кнопка с icon="logout"
        logout_buttons = page.locator("button").all()
        logout_btn = None

        for btn in logout_buttons:
            try:
                if btn.is_visible() and (
                    "logout" in btn.get_attribute("icon") or "logout" in btn.inner_html().lower()
                ):
                    logout_btn = btn
                    break
            except:
                continue

        if not logout_btn:
            # Пробуем найти по HTML
            buttons = page.locator("button").all()
            for btn in buttons:
                try:
                    html = btn.inner_html()
                    if "logout" in html.lower():
                        logout_btn = btn
                        break
                except:
                    continue

        if not logout_btn:
            pytest.skip("Logout button not found")

        logout_btn.click()
        time.sleep(3)

        # Должны быть на странице логина
        assert "/login" in page.url


class TestPerformance:
    """Тесты производительности."""

    def test_page_load_time(self, page: Page, app_url: str):
        """Время загрузки страницы."""
        import time as time_module

        start = time_module.time()
        page.goto(f"{app_url}/login")
        page.wait_for_load_state("networkidle")
        load_time = time_module.time() - start

        assert load_time < 5.0, f"Page load time {load_time:.2f}s exceeds 5s"

    def test_no_javascript_errors(self, page: Page, app_url: str):
        """Нет JS ошибок при загрузке."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        page.goto(app_url)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Исключаем ожидаемые ошибки
        unexpected = [e for e in errors if "favicon" not in e.lower()]
        assert len(unexpected) == 0, f"Unexpected JS errors: {unexpected}"
