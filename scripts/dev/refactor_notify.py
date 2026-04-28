import re
from pathlib import Path


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Needs NotifyHelper?
    if "ui.notify" in content:
        # Check if NotifyHelper is imported
        if "NotifyHelper" not in content:
            # Add import after `from nicegui import ui` or at the end of imports
            if "from nicegui import ui" in content:
                content = content.replace(
                    "from nicegui import ui",
                    "from nicegui import ui\nfrom docuflow.lib.widgets.ui_utils import NotifyHelper",
                )
            else:
                content = "from docuflow.lib.widgets.ui_utils import NotifyHelper\n" + content

        # Replace multi-line and single-line ui.notify calls
        # 1. color="warning" or type="warning"
        content = re.sub(
            r'ui\.notify\((.*?),\s*(?:color|type)="warning"(?:,\s*icon=".*?")?\)',
            r"NotifyHelper.warning(\1)",
            content,
            flags=re.DOTALL,
        )

        # 2. color="negative" or type="negative" or color="red"
        content = re.sub(
            r'ui\.notify\((.*?),\s*(?:color|type)="(?:negative|red)"(?:,\s*icon=".*?")?\)',
            r"NotifyHelper.error(\1)",
            content,
            flags=re.DOTALL,
        )

        # 3. color="positive" or type="positive" or color="emerald" or color="green"
        content = re.sub(
            r'ui\.notify\((.*?),\s*(?:color|type)="(?:positive|emerald|green)"(?:,\s*position=".*?")?\)',
            r"NotifyHelper.success(\1)",
            content,
            flags=re.DOTALL,
        )

        # 4. type="info"
        content = re.sub(
            r'ui\.notify\((.*?),\s*type="info"\)',
            r"NotifyHelper.info(\1)",
            content,
            flags=re.DOTALL,
        )

        # 5. color="yellow" or color="orange" -> warning
        content = re.sub(
            r'ui\.notify\((.*?),\s*color="(?:yellow|orange)"\)',
            r"NotifyHelper.warning(\1)",
            content,
            flags=re.DOTALL,
        )

        # 6. Default (no color/type)
        content = re.sub(r"ui\.notify\((.*?)\)", r"NotifyHelper.info(\1)", content)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")


def main():
    root_dir = Path("src/docuflow/lib")
    for py_file in root_dir.glob("**/*.py"):
        process_file(py_file)


if __name__ == "__main__":
    main()
