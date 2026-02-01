from backend.gnc_parser import GNCParser

def debug():
    parser = GNCParser()
    content = """(Header)
(PART NAME:Part 1 )
(==== CONTOUR 1 ====)
*N1005 P660=1005 P100=20
G01 X10 Y10
"""
    print(f"--- Parsing P-Code Content ---")
    sheet = parser.parse(content)
    for i, part in enumerate(sheet.parts):
        print(f"Part {i}: Name='{part.name}'")
        for j, contour in enumerate(part.contours):
            print(f"  Contour {j} (ID {contour.id}): Metadata={contour.metadata}")
            for k, cmd in enumerate(contour.commands):
                print(f"    Cmd {k}: Type={cmd.type} Text='{cmd.original_text}'")

    content2 = """(CK-AN Post V22.1 SP360)
(*MODEL HANS_G3015-REXROTH)
(PART NAME:Part A )
(==== CONTOUR 1 ====)
G00 X0 Y0
G01 X10 Y10
(PART NAME:Part B )
(==== CONTOUR 2 ====)
G01 X20 Y20
"""
    print(f"\n--- Parsing Identity Content ---")
    sheet2 = parser.parse(content2)
    for i, part in enumerate(sheet2.parts):
        print(f"Part {i}: Name='{part.name}'")
        for j, contour in enumerate(part.contours):
            print(f"  Contour {j} (ID {contour.id})")
            for k, cmd in enumerate(contour.commands):
                print(f"    Cmd {k}: Type={cmd.type} Text='{cmd.original_text}'")

if __name__ == "__main__":
    debug()
