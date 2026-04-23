"""
Полное E2E тестирование DocuFlow.

Запуск:
    uv run python tests/e2e/full_e2e_test.py
"""

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8082"
SCREENSHOTS_DIR = Path("tests/e2e/screenshots/full")


def ensure_dir():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def login(page):
    """Логин как admin."""
    print("🔐 Логин...")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Заполняем форму (используем aria-label)
    page.fill('input[aria-label="Username"]', "admin")
    page.fill('input[aria-label="Password"]', "admin")

    # Кликаем кнопку
    page.click('button:has-text("AUTHORIZE NODE")')

    # Ждём redirect
    page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
    time.sleep(4)  # Ждём загрузки SPA

    print("✅ Успешный логин")
    return True


def take_screenshot(page, name):
    """Делает скриншот."""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=path, full_page=True)
    print(f"📸 Скриншот: {path}")
    return path


def test_view(page, view_name, button_text, wait_for_text=None):
    """Тестирует view через sidebar."""
    print(f"\n📋 Тестируем: {view_name}")

    try:
        # Находим и кликаем кнопку в sidebar
        button = page.locator(f"button:has-text('{button_text}')").first

        if not button.is_visible():
            print(f"⚠️  Кнопка '{button_text}' не видна")
            return False

        button.click()
        time.sleep(4)  # Ждём рендеринг view

        # Делаем скриншот
        take_screenshot(page, view_name)

        # Проверяем наличие ожидаемого текста
        if wait_for_text:
            content = page.content()
            if wait_for_text.lower() in content.lower():
                print(f"✅ Найден текст: '{wait_for_text}'")
            else:
                print(f"⚠️  Текст '{wait_for_text}' не найден")

        # Проверяем что нет ошибок 404
        content = page.content()
        if "404" in content and "not found" in content.lower():
            print(f"❌ View {view_name} вернул 404")
            return False

        print(f"✅ {view_name} работает")
        return True

    except Exception as e:
        print(f"❌ Ошибка в {view_name}: {e}")
        take_screenshot(page, f"{view_name}_error")
        return False


def run_full_test():
    """Запускает полное E2E тестирование."""
    ensure_dir()

    print("=" * 70)
    print("🚀 ПОЛНОЕ E2E ТЕСТИРОВАНИЕ DOCUFLOW")
    print("=" * 70)

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # 1. Логин
        if not login(page):
            print("❌ Не удалось залогиниться")
            browser.close()
            return

        take_screenshot(page, "after_login")

        # 2. Тестируем все views через sidebar
        views_to_test = [
            ("dashboard", "Dashboard", "Cluster"),
            ("work_items", "Work Items", "Work"),
            ("task_board", "Task Board", "Role"),
            ("scanner", "Folder Scanner", "Scanner"),
            ("warehouse", "Warehouse", "Warehouse"),
            ("production", "Finished Pallets", "Pallet"),
            ("parts", "Parts Library", "Parts"),
            ("projects", "Projects", "Project"),
            ("consumables", "Supplies", "Supply"),
            ("chat", "Workshop Chat", "Chat"),
            ("incidents", "Incidents", "Incident"),
            ("analytics", "Analytics KPIs", "Analytics"),
            ("reports", "Reports", "Report"),
            ("docs", "Documentation", "Doc"),
            ("admin", "System Admin", "Admin"),
        ]

        for view_name, button_text, expected_text in views_to_test:
            results[view_name] = test_view(page, view_name, button_text, expected_text)

        # 3. Тест User Info
        print("\n👤 Тест User Info...")
        try:
            avatar = page.locator(".q-avatar").first
            if avatar.is_visible():
                print("✅ Avatar пользователя виден")
                results["user_info"] = True
            else:
                print("⚠️  Avatar не найден")
                results["user_info"] = False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            results["user_info"] = False

        # 4. Тест Logout
        print("\n🚪 Тест Logout...")
        try:
            # Кнопка logout в header
            logout_btn = page.locator('button[icon="logout"]').first
            if logout_btn.is_visible():
                logout_btn.click()
                time.sleep(3)

                if "/login" in page.url:
                    print("✅ Logout работает")
                    results["logout"] = True
                    take_screenshot(page, "after_logout")
                else:
                    print(f"⚠️  URL после logout: {page.url}")
                    results["logout"] = False
            else:
                print("⚠️  Кнопка logout не найдена")
                results["logout"] = False
        except Exception as e:
            print(f"❌ Ошибка Logout: {e}")
            results["logout"] = False

        browser.close()

    # Отчёт
    print("\n" + "=" * 70)
    print("📊 ОТЧЁТ E2E ТЕСТИРОВАНИЯ")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nПройдено: {passed}/{total}")
    print()

    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {name}")

    print()
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print(f"⚠️  {total - passed} тестов не пройдены")

    print(f"\n📸 Все скриншоты: {SCREENSHOTS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    run_full_test()
