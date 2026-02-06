import sys
import os
import pytest
from backend.gnc_parser import GNCParser
from backend.gnc_generator import GNCGenerator

# Sample content from the user-provided file
SAMPLE_GNC_PATH = "testing/sidra_test/sidra 3455/06-02-SIDRA-351501-SHLAV-1-23.12.2024-SS 1.4003-1.5.GNC"

def test_gnc_roundtrip():
    if not os.path.exists(SAMPLE_GNC_PATH):
        pytest.skip("Sample GNC file not found")
        
    with open(SAMPLE_GNC_PATH, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    parser = GNCParser()
    sheet = parser.parse(original_content, SAMPLE_GNC_PATH)
    
    generator = GNCGenerator()
    generated_content = generator.generate(sheet)
    
    # We expect high-fidelity reconstruction
    # Some whitespace might differ but commands should be identical
    orig_lines = [l.strip() for l in original_content.splitlines() if l.strip()]
    gen_lines = [l.strip() for l in generated_content.splitlines() if l.strip()]
    
    # For now, let's compare some key lines
    assert orig_lines[0] == gen_lines[0] # Header comment
    assert any("(*SHEET" in l for l in gen_lines)
    assert any("(PART NAME:" in l for l in gen_lines)
    
    # Check if a specific data line (G-code) exists
    assert any("N1005 G00X567Y189.955" in l for l in gen_lines)

def test_gnc_offsets():
    # Synthetic test for offsets
    content = "(PART NAME:TEST)\n(==== CONTOUR 1 ====)\nN10 G00X10Y10\nN20 G01X20Y20"
    parser = GNCParser()
    sheet = parser.parse(content)
    
    # Manually add offset
    sheet.parts[0].x = 100
    sheet.parts[0].y = 50
    
    generator = GNCGenerator()
    generated = generator.generate(sheet)
    
    assert "G00X110.000Y60.000" in generated
    assert "G01X120.000Y70.000" in generated

if __name__ == "__main__":
    pytest.main([__file__])
