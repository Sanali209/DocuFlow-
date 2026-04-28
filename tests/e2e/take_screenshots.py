"""
Скрипт для создания скриншотов всех страниц DocuFlow.
Запускать когда приложение работает.
"""

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8082"


def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        pages_to_test = [
            ("login", "/login"),
            ("home", "/"),
            ("health", "/health"),
        ]

        for name, path in pages_to_test:
            try:
                page.goto(f"{BASE_URL}{path}", timeout=10000)
                page.wait_for_load_state("networkidle")

                # Даём время на рендеринг
                page.wait_for_timeout(2000)

                screenshot_path = f"tests/e2e/screenshots/{name}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"✅ {name}: {screenshot_path}")

                # Выводим информацию о странице
                title = page.title()
                url = page.url
                content_length = len(page.content())
                print(f"   Title: {title}")
                print(f"   URL: {url}")
                print(f"   Content size: {content_length} bytes")
                print()

            except Exception as e:
                print(f"❌ {name}: {e}")

        browser.close()


if __name__ == "__main__":
    import os

    os.makedirs("tests/e2e/screenshots", exist_ok=True)
    take_screenshots()
