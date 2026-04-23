import re

files_to_fix = [
    'src/docuflow/features/admin/view.py',
    'src/docuflow/features/core/layout.py',
    'src/docuflow/features/inventory/view.py',
    'src/docuflow/features/production/view.py',
]

for filepath in files_to_fix:
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # regex for multiline NotifyHelper with color/type
    content = re.sub(r'NotifyHelper\.[a-z]+\(\s*(f?".*?"),\s*(?:color|type|icon)=".*?",?\s*\)', r'NotifyHelper.warning(\1)', content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
