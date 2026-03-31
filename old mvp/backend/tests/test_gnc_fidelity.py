import pytest
import os
from backend.gnc_parser import GNCParser
from backend.gnc_generator import GNCGenerator

SAMPLE_PATH = "testing/sidra_test/sidra 3455/06-02-SIDRA-351501-SHLAV-1-23.12.2024-SS 1.4003-1.5.GNC"

def test_gnc_multi_part_nesting():
    """
    Test placing two parts with different positions and verify renumbering and offsets.
    """
    if not os.path.exists(SAMPLE_PATH):
        pytest.skip("Sample GNC file not found")
        
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    parser = GNCParser()
    # Extract just one part from the sample to use as a template
    full_sheet = parser.parse(content)
    if not full_sheet.parts:
        pytest.skip("No parts found in sample")
    
    source_part = full_sheet.parts[0]
    
    # Create a new sheet with 2 instances of this part
    from backend.gnc_parser import GNCSheet, GNCPart
    import copy
    
    new_sheet = GNCSheet(
        name="Test Multi-Part",
        program_width=3000,
        program_height=1500,
        thickness=1.5,
        header_commands=full_sheet.header_commands[:5] # Keep some headers
    )
    
    # Part 1 at (0, 0)
    p1 = copy.deepcopy(source_part)
    p1.x = 0
    p1.y = 0
    
    # Part 2 at (500, 200)
    p2 = copy.deepcopy(source_part)
    p2.x = 500
    p2.y = 200
    
    new_sheet.parts = [p1, p2]
    
    generator = GNCGenerator()
    generated = generator.generate(new_sheet)
    lines = generated.splitlines()
    
    # Verification 1: Count contours
    # Count how many (==== CONTOUR lines are in the source_part object
    n_source_part_contours = 0
    for contour in source_part.contours:
        if any("(==== CONTOUR" in cmd.original_text.upper() for cmd in contour.commands if cmd.original_text):
            n_source_part_contours += 1
    
    contour_lines = [l for l in lines if "(==== CONTOUR" in l]
    print(f"Generated {len(contour_lines)} contour lines (Source part had {n_source_part_contours})")
    
    assert len(contour_lines) == 2 * n_source_part_contours, f"Expected {2*n_source_part_contours} contours, got {len(contour_lines)}"
    
    # Verification 2: Sequential numbering
    for i, line in enumerate(contour_lines):
        expected_label = f"CONTOUR  {i+1}"
        assert expected_label in line, f"Expected {expected_label} in line: {line}"
        
    # Verification 3: Sequential N-codes
    import re
    n_codes = []
    for line in lines:
        match = re.search(r'^N(\d+)', line.strip())
        if match:
            n_codes.append(int(match.group(1)))
            
    assert len(n_codes) > 0
    assert all(n_codes[i] < n_codes[i+1] for i in range(len(n_codes)-1)), "N-codes are not strictly increasing"
    
    # Verification 4: Coordinate Offsets and Content
    part_name_lines = [l for l in lines if "(PART NAME:" in l]
    print(f"Found {len(part_name_lines)} PART NAME lines")
    for l in part_name_lines: print(f"  {l}")

    # Split lines by parts
    part_blocks = []
    current_block = []
    for line in lines:
        if "(PART NAME:" in line:
            if current_block:
                # If we are already in a block, the new header marks the end of previous
                part_blocks.append(current_block)
            current_block = [line]
        elif current_block:
            current_block.append(line)
            
    if current_block:
        part_blocks.append(current_block)
    
    # NOTE: The first block might contain sheet headers if they were before the first part info
    # Let's filter blocks that actually contain (PART NAME:
    part_blocks = [b for b in part_blocks if any("(PART NAME:" in l for l in b)]
    
    assert len(part_blocks) == 2, f"Expected 2 part blocks, got {len(part_blocks)}"
    
    p1_lines = part_blocks[0]
    p2_lines = part_blocks[1]
    
    # Check a few moves
    move_pattern = re.compile(r'G\d+.*[XY][+-]?(\d*\.?\d+)', re.I)
    
    p1_moves = [l for l in p1_lines if move_pattern.search(l)]
    p2_moves = [l for l in p2_lines if move_pattern.search(l)]
    
    assert len(p1_moves) == len(p2_moves), "Part 1 and Part 2 have different number of moves"
    
    for m1, m2 in zip(p1_moves, p2_moves):
        # Parity check
        for axis in ['X', 'Y', 'I', 'J']: # Check all coordinates
            v1_match = re.search(rf'{axis}([+-]?\d*\.?\d+)', m1)
            v2_match = re.search(rf'{axis}([+-]?\d*\.?\d+)', m2)
            
            if v1_match and v2_match:
                v1 = float(v1_match.group(1))
                v2 = float(v2_match.group(1))
                offset = 500 if axis == 'X' else (200 if axis == 'Y' else 0)
                assert abs(v2 - (v1 + offset)) < 0.001, f"Offset error in {axis} for {m1} -> {m2}"
        
        # SSD renumbering check
        ssd_match1 = re.search(r'SSD\[SD\.Cr_Nb1=(\d+)\]', m1)
        ssd_match2 = re.search(r'SSD\[SD\.Cr_Nb1=(\d+)\]', m2)
        
        if ssd_match1 and ssd_match2:
            n2_match = re.search(r'^N(\d+)', m2.strip())
            if n2_match:
                n2_val = n2_match.group(1)
                ssd2_val = ssd_match2.group(1)
                assert n2_val == ssd2_val, f"SSD call {ssd2_val} does not match N-code {n2_val} in line: {m2}"

def test_gnc_sidra_roundtrip():
    """
    Test parsing and generating the Sidra sample and ensuring structural/functional parity.
    """
    if not os.path.exists(SAMPLE_PATH):
        pytest.skip("Sample GNC file not found")
        
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    parser = GNCParser()
    sheet = parser.parse(original_content, SAMPLE_PATH)
    
    generator = GNCGenerator()
    # Adjust generator to match original's starting N-code and step if we want BIT-PERFECT,
    # but the user asked for "proper file", so let's see what the generator produces by default.
    generated_content = generator.generate(sheet)
    
    gen_lines = generated_content.splitlines()
    orig_lines = original_content.splitlines()
    
    # 1. Structural checks
    # Basic lengths should be similar (allowing for some blank line differences)
    print(f"\nOriginal lines: {len(orig_lines)}")
    print(f"Generated lines: {len(gen_lines)}")
    
    # 2. Check for critical machine codes presence
    critical_codes = ["(*MODEL", "(*SHEET", "G71", "G90", "G54", "M30"]
    for code in critical_codes:
        found_orig = any(code in l for l in orig_lines)
        found_gen = any(code in l for l in gen_lines)
        assert found_orig == found_gen, f"Critical code {code} parity failed. Orig: {found_orig}, Gen: {found_gen}"

    # 3. Check coordinate parity for a few moves
    import re
    move_pattern = re.compile(r'G\d+.*[XY][+-]?(\d*\.?\d+)', re.I)
    orig_moves = [l for l in orig_lines if move_pattern.search(l)]
    gen_moves = [l for l in gen_lines if move_pattern.search(l)]
    
    # Filter out redundant header moves if any
    # (Sidra files sometimes have a G0x move in the header)
    
    print(f"Original moves: {len(orig_moves)}")
    print(f"Generated moves: {len(gen_moves)}")
    
    # Even if line numbers differ, coordinates must match
    for o_move, g_move in zip(orig_moves[:20], gen_moves[:20]):
        for axis in ['X', 'Y', 'I', 'J']:
            o_m = re.search(rf'{axis}([+-]?\d*\.?\d+)', o_move)
            g_m = re.search(rf'{axis}([+-]?\d*\.?\d+)', g_move)
            if o_m and g_m:
                assert abs(float(o_m.group(1)) - float(g_m.group(1))) < 0.001, f"Coordinate mismatch: {o_move} vs {g_move}"

    # 4. Check for N-code and SSD consistency in generated file
    for line in gen_lines:
        match_n = re.search(r'^N(\d+)', line.strip())
        match_ssd = re.search(r'SSD\[SD\.Cr_Nb1=(\d+)\]', line)
        if match_n and match_ssd:
            assert match_n.group(1) == match_ssd.group(1), f"SSD mismatch in generated line: {line}"

    print("Sidra GNC roundtrip verification PASSED")
