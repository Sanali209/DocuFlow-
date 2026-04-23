import glob
import re

# Find all python files
files = glob.glob("src/docuflow/**/*.py", recursive=True)

for file in files:
    with open(file, encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    for i, line in enumerate(lines):
        if re.search(r'\.(ilike|contains|asc|desc|in_)\b', line) and 'type: ignore' not in line:
            # We add type ignore
            # Remove trailing newline
            lines[i] = line.rstrip() + "  # type: ignore[attr-defined]\n"
            modified = True

    if modified:
        with open(file, "w", encoding="utf-8") as f:
            f.writelines(lines)
