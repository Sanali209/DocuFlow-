from fastapi.testclient import TestClient
from .main import app
import os
import unittest

client = TestClient(app)

class TestGNCAPI(unittest.TestCase):
    def test_parse_gnc_office_simple(self):
        content = """
(PART NAME: Test Part)
(===== CONTOUR 1 =====)
G00 X0 Y0
G01 X10 Y10
"""
        files = {'file': ('test.gnc', content, 'text/plain')}
        response = client.post("/api/parse-gnc", files=files)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check structure
        self.assertTrue('parts' in data)
        self.assertEqual(len(data['parts']), 1)
        self.assertEqual(data['parts'][0]['name'], 'Test Part')
        self.assertEqual(len(data['parts'][0]['contours']), 1)
        self.assertEqual(len(data['parts'][0]['contours'][0]['commands']), 2)

    def test_parse_gnc_machine_complex(self):
        content = """%
(===== CONTOUR 1 =====)
G01 X10 Y10
(===== CONTOUR 2 =====)
G01 X20 Y20
"""
        files = {'file': ('machine.gnc', content, 'text/plain')}
        response = client.post("/api/parse-gnc", files=files)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Expect 1 default part with 2 contours
        self.assertEqual(len(data['parts']), 1)
        self.assertEqual(data['parts'][0]['name'], 'Main Part')
        self.assertEqual(len(data['parts'][0]['contours']), 2)

    def test_parse_gnc_invalid_file(self):
        # Test uploading a non-text file or empty
        files = {'file': ('test.bin', b'\x00\xFF', 'application/octet-stream')}

        response = client.post("/api/parse-gnc", files=files)

        # Depending on implementation details, it might return 200 with garbage or 400.
        # But latin-1 usually decodes everything. So let's check if it returns a valid structure at least.

        if response.status_code == 200:
            data = response.json()
            self.assertTrue('parts' in data)
        else:
            self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
