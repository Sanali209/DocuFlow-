import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8082"
LOG_PATH = "/tmp/docuflow_app.log"
OUTPUT_DIR = "/tmp/docuflow_screenshots"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Navigation items to click (button text -> report name)
NAV_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Task Board", "task_board"),
    ("Workshop Chat", "chat"),
    ("Analytics KPIs", "analytics"),
    ("Folder Scanner", "scanner"),
    ("Parts Library", "parts"),
    ("Warehouse", "warehouse"),
    ("Finished Pallets", "production"),
    ("Projects", "projects"),
    ("Reports & Exports", "reports"),
    ("System Admin", "admin"),
]

console_errors = []
python_tracebacks = []
successful_views = []
failed_views = []

def check_log_for_errors():
    """Check the app log file for Python tracebacks since last check."""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # Simple traceback detection
    errors = []
    lines = content.splitlines()
    in_traceback = False
    current_tb = []
    for line in lines:
        if "Traceback (most recent call last):" in line:
            in_traceback = True
            current_tb = [line]
        elif in_traceback:
            current_tb.append(line)
            # Traceback ends at an empty line or a line that doesn't start with spaces/File/Error
            if line.strip() == "" or (not line.startswith(" ") and not line.startswith("\t") and not any(x in line for x in ["File", "line", "Error", "Exception", "Traceback", "^"])):
                if len(current_tb) > 1:
                    errors.append("\n".join(current_tb))
                in_traceback = False
                current_tb = []
    if in_traceback and current_tb:
        errors.append("\n".join(current_tb))
    return errors

def main():
    global console_errors, python_tracebacks, successful_views, failed_views

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Collect console errors
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(f"[{msg.type}] {msg.text}")
            elif msg.type == "warning":
                console_errors.append(f"[{msg.type}] {msg.text}")
        page.on("console", handle_console)

        # Collect page errors
        def handle_page_error(err):
            console_errors.append(f"[page error] {err}")
        page.on("pageerror", handle_page_error)

        # 1. Open login page
        print("Navigating to", BASE_URL)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Screenshot login
        login_screenshot = "/tmp/docuflow_login.png"
        page.screenshot(path=login_screenshot, full_page=True)
        print(f"Saved login screenshot: {login_screenshot}")

        # 2. Check for login form and log in
        try:
            # Wait for username input
            page.wait_for_selector("input", timeout=5000)
            print("Login form detected, logging in with admin/admin")
            # Fill username and password - find inputs by placeholder or type
            inputs = page.query_selector_all("input")
            if len(inputs) >= 2:
                inputs[0].fill("admin")
                inputs[1].fill("admin")
            else:
                # Try by aria-label or placeholder
                page.fill('input[placeholder="Username"]', "admin")
                page.fill('input[placeholder="Password"]', "admin")
            # Click the AUTHORIZE NODE button
            page.click("button:has-text('AUTHORIZE NODE')")
            time.sleep(2)
            page.wait_for_load_state("networkidle")
            print("Logged in successfully")
        except Exception as e:
            print(f"Login step issue: {e}")
            # Maybe already logged in or no login needed
            pass

        # 3. Click through each navigation item
        for label, report_name in NAV_ITEMS:
            print(f"\n--- Navigating to: {label} ---")
            try:
                # Find and click the nav button
                button = page.locator(f"button:has-text('{label}')").first
                if button.count() == 0:
                    # Some labels might differ slightly
                    alt_labels = {
                        "Chat": "Workshop Chat",
                        "Analytics": "Analytics KPIs",
                        "Scanner": "Folder Scanner",
                        "Parts": "Parts Library",
                        "Inventory": "Warehouse",
                        "Production": "Finished Pallets",
                        "Admin": "System Admin",
                    }
                    if label in alt_labels:
                        button = page.locator(f"button:has-text('{alt_labels[label]}')").first
                
                if button.count() == 0:
                    print(f"  WARNING: Button '{label}' not found, skipping")
                    failed_views.append((label, "Button not found"))
                    continue

                button.click()
                time.sleep(2)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                # Screenshot
                ss_path = os.path.join(OUTPUT_DIR, f"{report_name}.png")
                page.screenshot(path=ss_path, full_page=True)
                print(f"  Screenshot saved: {ss_path}")

                # Check for errors in log
                tbs = check_log_for_errors()
                if tbs:
                    print(f"  TRACEBACKS FOUND ({len(tbs)})")
                    for tb in tbs:
                        python_tracebacks.append((label, tb))
                else:
                    print(f"  No Python tracebacks")

                successful_views.append(label)

            except Exception as e:
                print(f"  ERROR clicking {label}: {e}")
                failed_views.append((label, str(e)))
                # Try to screenshot anyway
                try:
                    ss_path = os.path.join(OUTPUT_DIR, f"{report_name}_error.png")
                    page.screenshot(path=ss_path, full_page=True)
                except Exception:
                    pass

        # Final screenshot
        final_ss = os.path.join(OUTPUT_DIR, "final.png")
        page.screenshot(path=final_ss, full_page=True)
        print(f"\nFinal screenshot: {final_ss}")

        browser.close()

    # Report
    print("\n" + "="*60)
    print("REPORT")
    print("="*60)
    print(f"\nSuccessful views ({len(successful_views)}):")
    for v in successful_views:
        print(f"  - {v}")

    print(f"\nFailed views ({len(failed_views)}):")
    for v, reason in failed_views:
        print(f"  - {v}: {reason}")

    print(f"\nPython tracebacks ({len(python_tracebacks)}):")
    for view, tb in python_tracebacks:
        print(f"\n--- {view} ---")
        print(tb)

    print(f"\nJavaScript console errors/warnings ({len(console_errors)}):")
    for err in console_errors:
        print(f"  {err}")

    print(f"\nScreenshots saved in: {OUTPUT_DIR}")
    print(f"Login screenshot: {login_screenshot}")

if __name__ == "__main__":
    main()
