"""
Дебаг страницы логина - посмотреть HTML структуру.
"""

import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8082"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})

    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Получаем HTML
    html = page.content()

    # Ищем input поля
    import re

    inputs = re.findall(r"<input[^>]*>", html)
    print("Input поля на странице:")
    for inp in inputs:
        print(f"  {inp}")

    # Ищем кнопки
    buttons = re.findall(r"<button[^>]*>.*?</button>", html, re.DOTALL)
    print("\nКнопки на странице:")
    for btn in buttons[:5]:
        print(f"  {btn[:100]}")

    # Делаем скриншот
    page.screenshot(path="tests/e2e/screenshots/login_debug.png", full_page=True)
    print("\nСкриншот сохранён: tests/e2e/screenshots/login_debug.png")

    browser.close()
