import unittest
from .gnc_parser import GNCParser, GNCSheet

class TestGNCParser(unittest.TestCase):
    def setUp(self):
        self.parser = GNCParser()

    def test_machine_format_detection(self):
        content = """%
(===== CONTOUR 1 =====)
G00 X0 Y0
G01 X10 Y10
"""
        sheet = self.parser.parse(content)
        self.assertFalse(self.parser.office_mode)
        # Expect 1 Part (Main Part default)
        self.assertEqual(len(sheet.parts), 1)
        part = sheet.parts[0]

        # Expect 2 Contours:
        # 1. Header/Metadata contour (containing '%')
        # 2. Contour 1 (containing geometry)
        self.assertEqual(len(part.contours), 2)

        # Check Geometry Contour
        geo_contour = part.contours[1]
        self.assertEqual(geo_contour.id, 1)

        # Check Geometry Commands
        # (===== CONTOUR 1 =====) line is also stored as METADATA in this contour
        # So commands: [METADATA, G00, G01]
        self.assertEqual(len(geo_contour.commands), 3)
        self.assertEqual(geo_contour.commands[2].type, "G01")
        self.assertEqual(geo_contour.commands[2].x, 10.0)

    def test_office_format_detection(self):
        content = """
G00 X0 Y0
G01 X20 Y20
"""
        sheet = self.parser.parse(content)
        self.assertTrue(self.parser.office_mode)
        # Expect 1 Part (default)
        self.assertEqual(len(sheet.parts), 1)
        part = sheet.parts[0]
        # Expect 1 contour (default id=1) containing blank line cmds?
        # Content starts with empty line.
        # Line 1: empty -> ignored
        # Line 2: G00 -> Implicit Part, Implicit Contour
        # Line 3: G01
        self.assertEqual(len(part.contours), 1)
        self.assertEqual(len(part.contours[0].commands), 2)

    def test_parsing_commands(self):
        content = """
G00 X10.5 Y-5.0
G02 X20 Y0 I5 J0
"""
        sheet = self.parser.parse(content)
        part = sheet.parts[0]
        cmds = part.contours[0].commands

        # Line 1 empty -> ignored
        # Line 2: G00
        self.assertEqual(cmds[0].type, "G00")
        self.assertEqual(cmds[0].x, 10.5)
        self.assertEqual(cmds[0].y, -5.0)

        self.assertEqual(cmds[1].type, "G02")
        self.assertEqual(cmds[1].x, 20.0)
        self.assertEqual(cmds[1].i, 5.0)

    def test_machine_contours(self):
        content = """%
(===== CONTOUR 1 =====)
G01 X10 Y10
(===== CONTOUR 2 =====)
G01 X20 Y20
"""
        sheet = self.parser.parse(content)
        # Expect 1 Part (Main Part)
        self.assertEqual(len(sheet.parts), 1)
        part = sheet.parts[0]

        # Expect 3 Contours:
        # 1. Header (contains '%')
        # 2. Contour 1
        # 3. Contour 2
        self.assertEqual(len(part.contours), 3)

        # Contour 1 (Index 1)
        c1 = part.contours[1]
        self.assertEqual(c1.id, 1)
        # Commands: [Marker, G01]
        self.assertEqual(len(c1.commands), 2)
        self.assertEqual(c1.commands[1].x, 10.0)

        # Contour 2 (Index 2)
        c2 = part.contours[2]
        self.assertEqual(c2.id, 2)
        # Commands: [Marker, G01]
        self.assertEqual(len(c2.commands), 2)
        self.assertEqual(c2.commands[1].x, 20.0)

if __name__ == '__main__':
    unittest.main()
