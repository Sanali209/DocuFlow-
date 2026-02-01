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

        self.assertEqual(len(sheet.parts), 3)

        part1 = sheet.parts[1]
        self.assertEqual(part1.name, "3515-76-005-A-26")

        contour_ids1 = [c.id for c in part1.contours]
        self.assertTrue(len(part1.contours) >= 2)
        self.assertIn(1, contour_ids1)
        self.assertIn(2, contour_ids1)

        part2 = sheet.parts[2]
        self.assertEqual(part2.name, "3515-76-009-A-10")

        contour_ids2 = [c.id for c in part2.contours]
        self.assertTrue(len(part2.contours) >= 1)
        self.assertIn(10, contour_ids2)

    def test_no_part_name_fallback(self):
        content = """
(==== CONTOUR  1 ====)
G01 X10 Y10
(==== CONTOUR  2 ====)
G01 X20 Y20
"""
        sheet = self.parser.parse(content)
        self.assertEqual(len(sheet.parts), 1)
        part = sheet.parts[0]
        self.assertEqual(len(part.contours), 2)
        self.assertEqual(part.contours[0].id, 1)
        self.assertEqual(part.contours[1].id, 2)

if __name__ == '__main__':
    unittest.main()
