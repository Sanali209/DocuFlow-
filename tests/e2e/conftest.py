"""
Playwright E2E conftest для DocuFlow.

Запускает приложение перед тестами.
"""

import subprocess
import time
from collections.abc import Generator

import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def e2e_server() -> Generator[str, None, None]:
    """Запускает DocuFlow приложение для E2E тестов.

    Returns:
        URL запущенного приложения.
    """
    import socket

    # Check if something is already running on 8082 (default DocuFlow port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", 8082))
    sock.close()

    if result == 0:
        # Port is already in use, assume app is running
        yield "http://localhost:8082"
        return

    # Start the application
    process = subprocess.Popen(
        ["python", "-m", "docuflow.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(8)

    yield "http://localhost:8082"

    # Cleanup
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def app_url(e2e_server: str) -> str:
    """Provides the application URL."""
    return e2e_server


@pytest.fixture(autouse=True)
def set_viewport(page: Page):
    """Set viewport for desktop testing."""
    page.set_viewport_size({"width": 1920, "height": 1080})


@pytest.fixture
def logged_in_page(page: Page, app_url: str) -> Page:
    """Provides a logged-in page fixture."""
    import time

    page.goto(f"{app_url}/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Fill login form
    page.fill('input[aria-label="Username"]', "admin")
    page.fill('input[aria-label="Password"]', "admin")
    page.click('button:has-text("AUTHORIZE NODE")')

    # Wait for redirect
    page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
    time.sleep(3)

    yield page
