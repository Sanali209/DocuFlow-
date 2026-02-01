import unittest
from .gnc_parser import GNCParser, Sheet

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
        # Expect 1 Part
        self.assertEqual(len(sheet.parts), 1)
        part = sheet.parts[0]
        self.assertEqual(part.id, 1)

        # Expect 1 Contour in that Part
        self.assertEqual(len(part.contours), 1)
        cmds = part.contours[0].commands
        self.assertEqual(len(cmds), 2)
        self.assertEqual(cmds[1].type, "G01")
        self.assertEqual(cmds[1].x, 10.0)

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
        # Expect 2 Parts (since we treat separate CONTOUR blocks as parts in machine mode currently)
        self.assertEqual(len(sheet.parts), 2)
        self.assertEqual(sheet.parts[0].id, 1)
        self.assertEqual(sheet.parts[1].id, 2)

        # Check coordinates to be sure
        self.assertEqual(sheet.parts[0].contours[0].commands[0].x, 10.0)
        self.assertEqual(sheet.parts[1].contours[0].commands[0].x, 20.0)

if __name__ == '__main__':
    unittest.main()
