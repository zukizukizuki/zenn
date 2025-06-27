# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Zenn technical blog repository with automated Qiita synchronization. Articles are written in Markdown with YAML frontmatter and automatically cross-posted to Qiita via GitHub Actions.

## Architecture

### Core Structure
- **articles/**: Main Zenn articles in Markdown format with YAML frontmatter
- **qiita/public/**: Auto-generated Qiita-formatted versions of articles
- **images/**: Article images and diagrams
- **scripts/**: Cross-platform publishing utilities
- **.github/workflows/publish.yml**: GitHub Actions workflow for automatic Qiita sync

### Automated Sync System
The repository uses `C-Naoki/zenn-qiita-sync@main` action to automatically sync articles from Zenn to Qiita when pushed to main/master branches. The workflow:
1. Detects changed markdown files in `articles/` directory
2. Processes articles with `published: true` in frontmatter
3. Converts to Qiita format and posts via Qiita API
4. Saves converted versions to `qiita/public/` directory

## Common Commands

### Article Management
```bash
# Install dependencies
npm install

# Create new article
npx zenn new:article

# Preview articles locally
npx zenn preview

# Manual cross-platform posting
python scripts/cross_post.py articles/filename.md

# Export articles to different formats
python scripts/export_articles.py --format qiita --output ./exported
python scripts/export_articles.py --format wordpress --output ./exported_wp
python scripts/export_articles.py --format hatena --output ./exported_hatena
```

### Git Workflow for Sync
```bash
# Important: Sync only triggers on main/master branch pushes
git checkout main
git merge feature-branch
git push origin main  # This triggers the Qiita sync workflow
```

## Article Format Requirements

Articles must have proper YAML frontmatter for sync to work:

```yaml
---
title: "Article Title"
emoji: "😊" 
type: "tech"  # tech: technical / idea: ideas
topics: ["JavaScript", "React", "TypeScript"]
published: true  # Required for Qiita sync
---
```

## Sync Configuration

### Required GitHub Secrets
- `QIITA_TOKEN`: Qiita API token with `read_qiita` and `write_qiita` scopes

### Workflow Triggers
- Push to `main` or `master` branches
- Manual dispatch via GitHub Actions UI
- Only processes articles with `published: true`
- Uses duplicate prevention logic to avoid re-posting existing articles

## Cross-Platform Scripts

### Manual Cross-Posting
The `scripts/cross_post.py` requires configuration file at `~/.cross_post_config.json`:

```json
{
  "qiita": {
    "access_token": "your_token",
    "enabled": true
  },
  "wordpress": {
    "url": "your_wp_url", 
    "username": "username",
    "password": "password",
    "enabled": true
  }
}
```

### Export Formats
- **Qiita**: Markdown with Qiita-specific frontmatter
- **WordPress**: HTML with WordPress metadata comments
- **Hatena**: Markdown with Hatena Blog frontmatter

## Troubleshooting Sync Issues

### Common Problems
1. **Articles not syncing**: Check if working on feature branch instead of main
2. **Authentication errors**: Verify `QIITA_TOKEN` secret is properly set
3. **Workflow not triggering**: Ensure push is to main/master branch
4. **Duplicate articles**: Sync includes duplicate prevention logic

### Debugging Steps
1. Check GitHub Actions tab for workflow execution logs
2. Verify article has `published: true` in frontmatter
3. Confirm push was made to main/master branch
4. Check that `QIITA_TOKEN` has correct permissions

## File Naming Conventions

- Article files use descriptive names matching content topics
- Both English and Japanese filenames are supported
- Images should be placed in `images/` directory
- Generated Qiita files maintain same filename in `qiita/public/`