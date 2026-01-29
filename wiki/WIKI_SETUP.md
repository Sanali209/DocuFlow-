# GitHub Wiki Setup Guide

This guide explains how to publish the wiki content from this repository to GitHub Wiki.

## Prerequisites

- GitHub repository with wiki enabled
- Git installed locally
- Write access to the repository

## Method 1: Manual Copy (Simple)

### Step 1: Enable Wiki

1. Go to https://github.com/Sanali209/DocuFlow-/settings
2. Scroll to "Features" section
3. Check ✓ "Wikis"
4. Click "Save changes"

### Step 2: Create Wiki Pages

1. Navigate to the Wiki tab: https://github.com/Sanali209/DocuFlow-/wiki
2. Click "Create the first page" (if wiki is empty)
3. For each file in the `wiki/` directory:
   - Click "New Page"
   - Set page title (e.g., "Home", "Getting Started", etc.)
   - Copy content from the corresponding `.md` file
   - Click "Save Page"

### Page Names to Create

Create these pages in order:

1. **Home** (from `Home.md`)
2. **Getting Started** (from `Getting-Started.md`)
3. **User Guide** (from `User-Guide.md`)
4. **API Documentation** (from `API-Documentation.md`)
5. **Deployment Guide** (from `Deployment-Guide.md`)
6. **Developer Guide** (from `Developer-Guide.md`)
7. **FAQ and Troubleshooting** (from `FAQ-and-Troubleshooting.md`)
8. **Contributing** (from `Contributing.md`)

## Method 2: Git Clone (Automated)

GitHub wikis are actually git repositories themselves!

### Step 1: Clone Wiki Repository

```bash
# Clone your wiki (replace username/repo with your details)
git clone https://github.com/Sanali209/DocuFlow-.wiki.git

# Navigate to wiki directory
cd DocuFlow-.wiki
```

### Step 2: Copy Wiki Files

```bash
# From your main repository, copy all wiki markdown files
# Assuming you're in the wiki repository directory

# Copy all .md files from your main repo's wiki directory
cp ../DocuFlow-/wiki/*.md .

# Or if not in adjacent directories:
cp /path/to/DocuFlow-/wiki/*.md .
```

### Step 3: Commit and Push

```bash
# Add all files
git add *.md

# Commit changes
git commit -m "Add comprehensive DocuFlow documentation"

# Push to GitHub Wiki
git push origin master
```

### Step 4: Verify

Visit https://github.com/Sanali209/DocuFlow-/wiki to see your updated wiki!

## Method 3: Script Automation

Create a script to automate wiki updates:

### update-wiki.sh

```bash
#!/bin/bash

# Configuration
REPO_DIR="/path/to/DocuFlow-"
WIKI_DIR="${REPO_DIR}/wiki"
WIKI_REPO="https://github.com/Sanali209/DocuFlow-.wiki.git"
TEMP_DIR=$(mktemp -d)

echo "🚀 Starting wiki update..."

# Clone wiki repository
echo "📥 Cloning wiki repository..."
git clone "$WIKI_REPO" "$TEMP_DIR"

# Copy markdown files
echo "📝 Copying wiki files..."
cp "$WIKI_DIR"/*.md "$TEMP_DIR/"

# Commit and push
cd "$TEMP_DIR"
echo "💾 Committing changes..."
git add *.md
git commit -m "Update wiki documentation - $(date '+%Y-%m-%d %H:%M:%S')"

echo "📤 Pushing to GitHub..."
git push origin master

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Wiki update complete!"
echo "🌐 View at: https://github.com/Sanali209/DocuFlow-/wiki"
```

### Usage

```bash
chmod +x update-wiki.sh
./update-wiki.sh
```

## GitHub Actions (CI/CD)

Automatically sync wiki when docs are updated:

### .github/workflows/sync-wiki.yml

```yaml
name: Sync Wiki

on:
  push:
    branches:
      - main
    paths:
      - 'wiki/**'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout main repository
        uses: actions/checkout@v3

      - name: Sync to Wiki
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Clone wiki
          git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/${{ github.repository }}.wiki.git" wiki-repo
          
          # Copy files
          cp wiki/*.md wiki-repo/
          
          # Commit and push
          cd wiki-repo
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add *.md
          git commit -m "Auto-sync wiki from main repo" || exit 0
          git push origin master
```

## Customizing Wiki Sidebar

Create a `_Sidebar.md` file in the wiki repository:

```markdown
### 📚 DocuFlow Documentation

**Getting Started**
- [Home](Home)
- [Installation](Getting-Started)

**User Documentation**
- [User Guide](User-Guide)
- [API Docs](API-Documentation)

**Developer Resources**
- [Developer Guide](Developer-Guide)
- [Contributing](Contributing)

**Operations**
- [Deployment](Deployment-Guide)
- [Troubleshooting](FAQ-and-Troubleshooting)

---

[GitHub Repo](https://github.com/Sanali209/DocuFlow-)
```

## Customizing Wiki Footer

Create a `_Footer.md` file:

```markdown
---
DocuFlow © 2024 | [Main Repository](https://github.com/Sanali209/DocuFlow-) | [Report Issue](https://github.com/Sanali209/DocuFlow-/issues)
```

## Wiki URL Structure

After setup, your wiki will be accessible at:

```
https://github.com/Sanali209/DocuFlow-/wiki
https://github.com/Sanali209/DocuFlow-/wiki/Home
https://github.com/Sanali209/DocuFlow-/wiki/Getting-Started
https://github.com/Sanali209/DocuFlow-/wiki/User-Guide
etc.
```

## Maintaining the Wiki

### Regular Updates

1. **Edit source files** in `wiki/` directory of main repo
2. **Commit changes** to main repository
3. **Sync to wiki** using one of the methods above

### Link Checking

After syncing, verify all links work:
- Internal wiki links
- Links to main repository
- External links

### Version Control

- Keep wiki content in main repository for version control
- Use wiki as the published version
- Track changes through main repo's git history

## Troubleshooting

### Wiki Not Enabled

**Error**: Can't access wiki
**Solution**: Enable in repository settings → Features → Wikis

### Push Rejected

**Error**: `! [rejected] master -> master (fetch first)`
**Solution**: 
```bash
git pull origin master --rebase
git push origin master
```

### Permission Denied

**Error**: `Permission denied (publickey)`
**Solution**: Ensure you have write access to the repository or use HTTPS with token

### Large Files

GitHub Wiki has limits:
- **Max file size**: 1 MB per file
- **Max total size**: 1 GB per wiki

If files are too large, consider:
- Splitting into smaller pages
- Hosting images externally
- Using GitHub Releases for large assets

## Best Practices

1. **Keep it Simple**: Wiki pages should be easy to navigate
2. **Consistent Naming**: Use clear, descriptive page names
3. **Regular Updates**: Keep documentation in sync with code
4. **Version Info**: Add version numbers or "last updated" dates
5. **Screenshots**: Include visual aids where helpful
6. **Examples**: Provide practical code examples
7. **Testing**: Verify links and code snippets work

## Additional Resources

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Markdown Guide](https://guides.github.com/features/mastering-markdown/)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**Need Help?**
- Check [GitHub's Wiki Docs](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- Open an [issue](https://github.com/Sanali209/DocuFlow-/issues)
- Contact the maintainers

**Last Updated**: 2026-01-29
