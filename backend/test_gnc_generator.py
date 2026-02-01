import unittest
from .gnc_parser import GNCParser
from .gnc_generator import GNCGenerator

class TestGNCGenerator(unittest.TestCase):
    def setUp(self):
        self.parser = GNCParser()
        self.generator = GNCGenerator()

    def test_regeneration_identity(self):
        content = """(CK-AN Post V22.1 SP360)
(*MODEL HANS_G3015-REXROTH)
(PART NAME:Part A )
(==== CONTOUR 1 ====)
G00 X0 Y0
G01 X10 Y10
(PART NAME:Part B )
(==== CONTOUR 2 ====)
G01 X20 Y20
"""
        sheet = self.parser.parse(content)
        generated = self.generator.generate(sheet)

        self.assertIn("(PART NAME:Part A )", generated)
        self.assertIn("(==== CONTOUR 1 ====)", generated)
        self.assertIn("G00 X0 Y0", generated)

        # Verify no data lost or duplicated
        # Check stripping because newlines at end might vary
        self.assertEqual(content.strip(), generated.strip())

    def test_pcode_update(self):
        content = """(Header)
(PART NAME:Part 1 )
(==== CONTOUR 1 ====)
*N1005 P660=1005 P100=20
G01 X10 Y10
"""
        sheet = self.parser.parse(content)

        # Locate contour and update metadata
        # Part 0 is Main. Part 1 is Part 1.
        part = sheet.parts[1]

        # Part 1 has Contour 0 (Header/Name) and Contour 1 (Geometry)
        # Based on debug_gnc.py output
        self.assertTrue(len(part.contours) > 1)
        contour = part.contours[1]

        # Check parsed metadata
        self.assertEqual(contour.metadata.get('P660'), '1005')
        self.assertEqual(contour.metadata.get('P100'), '20')

        # Modify
        contour.metadata['P660'] = '9999'

        # Generate
        generated = self.generator.generate(sheet)

        self.assertIn("*N1005 P660=9999 P100=20", generated)
        self.assertNotIn("P660=1005", generated)

if __name__ == '__main__':
    unittest.main()
