import unittest
from .gnc_parser import GNCParser, GNCSheet

class TestGNCParserComplex(unittest.TestCase):
    def setUp(self):
        self.parser = GNCParser()

    def test_complex_office_file(self):
        content = """(CK-AN Post V22.1 SP360  run on DEC 30 2024)
(*MODEL HANS_G3015-REXROTH)
(31  PARTS)
(DATE DEC 30 2024)
(*SHEET 3000.0 1500.0 1.5 6 1 0.0 0.0 )
(*****Part info*****)
(PART NAME:3515-76-005-A-26 )
(==== CONTOUR  1 ====)
N1005 G00X567Y189.955 SSD[SD.Cr_Nb1=1005]
N1030 G41 D1 G01X567.248Y191.924
(==== CONTOUR  2 ====)
N1075 G00X687Y189.955 SSD[SD.Cr_Nb1=1075]
N1095 G41 D1 G01X687.248Y191.924
(*****Part info*****)
(PART NAME:3515-76-009-A-10 )
(==== CONTOUR  10 ====)
N1535 G00X29Y15 SSD[SD.Cr_Nb1=1535]
N1560 G41 D3 G01X30.816Y14.752
"""
        sheet = self.parser.parse(content)

        # We expect 2 Parts (based on Part Info)
        # Part 1: 3515-76-005-A-26 with 2 contours
        # Part 2: 3515-76-009-A-10 with 1 contour

        self.assertEqual(len(sheet.parts), 2)

        part1 = sheet.parts[0]
        self.assertEqual(part1.name, "3515-76-005-A-26")
        self.assertEqual(len(part1.contours), 2)
        self.assertEqual(part1.contours[0].id, 1)
        self.assertEqual(part1.contours[1].id, 2)

        part2 = sheet.parts[1]
        self.assertEqual(part2.name, "3515-76-009-A-10")
        self.assertEqual(len(part2.contours), 1)
        self.assertEqual(part2.contours[0].id, 10)

    def test_no_part_name_fallback(self):
        # Case where there are contours but no PART NAME tags (legacy or simple nesting)
        content = """
(==== CONTOUR  1 ====)
G01 X10 Y10
(==== CONTOUR  2 ====)
G01 X20 Y20
"""
        sheet = self.parser.parse(content)

        # If no explicit part name, current behavior creates Parts for contours?
        # Or should we group them?
        # For robustness, if NO part info is seen, maybe we should put them in one "Sheet Part" or keep separate?
        # Given "Sheet contains Parts", if these are parts on a sheet, they should be parts.
        # But if they are just contours of one part, they should be contours.
        # Without metadata it's ambiguous.
        # For now, let's verify checking what the *new* logic does.
        # If I implement "CONTOUR adds to Current Part", and "Current Part defaults to Main",
        # then this will produce 1 Part with 2 Contours.

        self.assertEqual(len(sheet.parts), 1)
        self.assertEqual(len(sheet.parts[0].contours), 2)

if __name__ == '__main__':
    unittest.main()
