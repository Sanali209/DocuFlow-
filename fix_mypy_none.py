import os
import re

for root, dirs, files in os.walk('src/docuflow'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, encoding='utf-8') as file:
                content = file.read()

            # Replace self.something = None with self.something: Any = None inside __init__
            # A simple regex might be tricky, let's look for `self.\w+ = None` and add `: Any`
            # Only do this if it's not already annotated
            new_content = re.sub(r'(self\.[a-zA-Z0-9_]+) = None', r'\1: Any = None', content)

            # Also need to import Any if not present
            if new_content != content and 'from typing import Any' not in new_content:
                new_content = 'from typing import Any\n' + new_content

            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)

print("Applied type hints for None assignments.")
