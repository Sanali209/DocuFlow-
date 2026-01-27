import re

DOC_NAME_REGEX = r"(?si)Order:\s*(.*?)\s*Date:"

test_cases = [
    {
        "input": """
Header Information
Order: SIDRA-351606-352501-SHLAV-2-15.01.2026.Dsp
Date: Thursday, Jan 15 2026
Other Info
""",
        "expected": "SIDRA-351606-352501-SHLAV-2-15.01.2026.Dsp"
    },
    {
        "input": "Response Order: SIDRA-351606-352501-SHLAV-2-15.01.2026.DsP Date: Thursday, Jan 15",
        "expected": "SIDRA-351606-352501-SHLAV-2-15.01.2026.DsP"
    },
    {
        "input": """
Order:
SIDRA-TEST-ORDER
Date: Friday
""",
        "expected": "SIDRA-TEST-ORDER"
    }
]

def run_tests():
    passed = 0
    failed = 0
    for i, case in enumerate(test_cases):
        print(f"Test Case {i+1}:")
        match = re.search(DOC_NAME_REGEX, case["input"])
        result = match.group(1).strip() if match else None

        if result == case["expected"]:
            print("  PASSED")
            passed += 1
        else:
            print("  FAILED")
            print(f"    Expected: '{case['expected']}'")
            print(f"    Got:      '{result}'")
            failed += 1

    print(f"\nSummary: {passed} Passed, {failed} Failed")
    if failed > 0:
        exit(1)

if __name__ == "__main__":
    run_tests()
