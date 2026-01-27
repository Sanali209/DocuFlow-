from playwright.sync_api import Page, expect, sync_playwright
import os
import shutil

def test_multipage_upload(page: Page):
    # 1. Setup Test Images
    if not os.path.exists("verification/test_image.png"):
        # Create it if not exists (re-using logic from generate_image.py implicitly via python call if needed, but easier to just mock here or assume it exists from previous steps.
        # Actually I cleaned it up. I should regenerate.)
        import struct
        import zlib

        def create_png(filename):
            width = 100
            height = 100
            png = b'\x89PNG\r\n\x1a\n'
            ihdr = b'IHDR' + struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(ihdr)
            png += struct.pack('!I', len(ihdr) - 4) + ihdr + struct.pack('!I', ihdr_crc)
            raw_data = b'\x00' + b'\xff\x00\x00' * width
            raw_data = raw_data * height
            compressed = zlib.compress(raw_data)
            idat = b'IDAT' + compressed
            idat_crc = zlib.crc32(idat)
            png += struct.pack('!I', len(idat) - 4) + idat + struct.pack('!I', idat_crc)
            iend = b'IEND'
            iend_crc = zlib.crc32(iend)
            png += struct.pack('!I', len(iend) - 4) + iend + struct.pack('!I', iend_crc)
            with open(filename, 'wb') as f:
                f.write(png)

        create_png("verification/page1.png")
        create_png("verification/page2.png")

    # 2. Goto App
    page.goto("http://localhost:5173")

    # 3. Open New Document
    page.locator(".add-btn").click()

    # 4. Upload Multiple Files
    page.locator("input#scan").set_input_files([
        "verification/page1.png",
        "verification/page2.png"
    ])

    # 5. Wait for scanning (simulated by visibility of result or status)
    # The scanStatus text appears then disappears.
    # We want to check the final textarea content.
    # Since the backend mocks OCR if service is down (returning "OCR Service Unavailable" or similar error in verify environment if real service isn't running),
    # OR if we are running the real stack, it might return empty or error.

    # Wait for the scanning text to disappear
    expect(page.locator(".info-text")).not_to_be_visible(timeout=30000)

    # 6. Check textarea content
    # If the real backend/ocr is running and returns empty text for the red square,
    # we might just get separator.
    # If we get errors, they show in .error-text.

    content_val = page.locator("textarea#content").input_value()
    print(f"Content Value: {content_val}")

    # We expect some content or at least handling.
    # If the backend is mocked to fail or return dummy data, we check that.
    # Note: In the previous turn, the 'backend.log' showed successful startup.
    # But the OCR service might be slow or return nothing for a red square.

    # 7. Screenshot
    page.screenshot(path="verification/multipage_result.png")
    print("Screenshot saved to verification/multipage_result.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_multipage_upload(page)
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="verification/multipage_error.png")
            exit(1)
        finally:
            browser.close()
