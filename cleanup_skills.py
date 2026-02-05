import os
import shutil

SKILLS_DIR = r"d:\github\DocuFlow-\.agent\skills"
ARCHIVE_DIR = os.path.join(SKILLS_DIR, "_archive")

KEEP_LIST = {
    "fastapi-pro",
    "python-pro",
    "frontend-developer",
    "ui-ux-pro-max",
    "sql-pro",
    "docker-expert",
    "software-architecture",
    "senior-architect",
    "backend-architect",
    "database-architect",
    "database-design",
    "architecture-patterns",
    "planning-with-files",
    "plan-writing",
    "writing-plans",
    "concise-planning",
    "git-pushing",
    "git-advanced-workflows",
    "clean-code",
    "code-review-excellence",
    "debugging-strategies",
    "python-patterns",
    "frontend-dev-guidelines",
    "writing-skills",
    "documentation-templates"
}

def cleanup_skills():
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
        print(f"Created archive directory: {ARCHIVE_DIR}")

    for item in os.listdir(SKILLS_DIR):
        item_path = os.path.join(SKILLS_DIR, item)
        
        # Skip archive dir itself and non-directories (like SKILL.md if any in root)
        if item == "_archive" or not os.path.isdir(item_path):
            continue

        if item not in KEEP_LIST:
            target_path = os.path.join(ARCHIVE_DIR, item)
            try:
                shutil.move(item_path, target_path)
                print(f"Archived: {item}")
            except Exception as e:
                print(f"Error archiving {item}: {e}")
        else:
            print(f"Kept: {item}")

if __name__ == "__main__":
    cleanup_skills()
