# GitHub Setup Guide

Step-by-step instructions for uploading the Attuned Survey project to GitHub.

## Prerequisites

- GitHub account
- Git installed locally
- Command line access

## Step 1: Create GitHub Repository

### Option A: Via GitHub Website

1. **Go to GitHub**
   - Visit https://github.com
   - Log in to your account

2. **Create New Repository**
   - Click the "+" icon in top right
   - Select "New repository"

3. **Repository Settings**
   - **Repository name:** `attuned-survey` (or your preferred name)
   - **Description:** "Intimacy profile survey application with React and Flask"
   - **Visibility:** Choose Private or Public
   - **DO NOT** initialize with README, .gitignore, or license (we have these already)
   - Click "Create repository"

4. **Copy Repository URL**
   - You'll see a URL like: `https://github.com/YOUR_USERNAME/attuned-survey.git`
   - Keep this page open for the next steps

### Option B: Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Windows: winget install GitHub.cli
# Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Login to GitHub
gh auth login

# Create repository
gh repo create attuned-survey --private --description "Intimacy profile survey application"
```

## Step 2: Initialize Local Git Repository

Open terminal and navigate to the project directory:

```bash
cd /path/to/github-package
```

Initialize Git:

```bash
# Initialize repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Attuned Survey v1.0.0

- Complete survey implementation (92 questions)
- Scoring engine (traits, dials, archetypes)
- Compatibility matching algorithm
- Admin panel with data export
- Responsive design
- Data persistence fixes"
```

## Step 3: Connect to GitHub

Add the remote repository (replace YOUR_USERNAME with your GitHub username):

```bash
git remote add origin https://github.com/YOUR_USERNAME/attuned-survey.git
```

Verify the remote:

```bash
git remote -v
```

You should see:
```
origin  https://github.com/YOUR_USERNAME/attuned-survey.git (fetch)
origin  https://github.com/YOUR_USERNAME/attuned-survey.git (push)
```

## Step 4: Push to GitHub

### First Push

```bash
# Push to main branch
git push -u origin main
```

If you get an error about "main" vs "master":

```bash
# Rename branch to main
git branch -M main

# Push again
git push -u origin main
```

### Enter Credentials

GitHub will prompt for authentication:

**Option A: Personal Access Token (Recommended)**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Copy the token
5. Use token as password when pushing

**Option B: SSH Key**

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/attuned-survey.git

# Push
git push -u origin main
```

## Step 5: Verify Upload

1. Go to your GitHub repository page
2. You should see all files and folders
3. Check that README.md displays correctly
4. Verify .gitignore is working (node_modules, venv, etc. should NOT be uploaded)

## Step 6: Add Repository Description and Topics

1. Go to repository page
2. Click the gear icon next to "About"
3. Add description: "Intimacy profile survey application with React and Flask"
4. Add topics: `react`, `flask`, `survey`, `intimacy`, `psychology`, `matching-algorithm`
5. Add website URL if deployed
6. Save changes

## Step 7: Create Branches (Optional)

Create development branch:

```bash
# Create and switch to dev branch
git checkout -b development

# Push dev branch
git push -u origin development
```

Set main as default branch:
1. Go to Settings → Branches
2. Change default branch to `main`

## Step 8: Add Collaborators (Optional)

1. Go to Settings → Collaborators
2. Click "Add people"
3. Enter GitHub username or email
4. Select permission level
5. Send invitation

## Common Git Commands

### Daily Workflow

```bash
# Check status
git status

# Add specific files
git add path/to/file

# Add all changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push

# Pull latest changes
git pull
```

### Branching

```bash
# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Merge branch
git checkout main
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

### Undoing Changes

```bash
# Discard local changes
git checkout -- path/to/file

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

## Troubleshooting

### Authentication Failed

**Problem:** GitHub rejected username/password

**Solution:** Use Personal Access Token instead of password

### Large Files Error

**Problem:** File size exceeds GitHub limit (100MB)

**Solution:** 
```bash
# Remove large files
git rm --cached path/to/large/file

# Add to .gitignore
echo "path/to/large/file" >> .gitignore

# Commit and push
git commit -m "Remove large files"
git push
```

### Merge Conflicts

**Problem:** Conflicts when pulling/merging

**Solution:**
```bash
# Pull with rebase
git pull --rebase

# Or manually resolve conflicts
# Edit conflicted files
git add .
git commit -m "Resolve conflicts"
git push
```

### Wrong Remote URL

**Problem:** Pushed to wrong repository

**Solution:**
```bash
# Check current remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/YOUR_USERNAME/correct-repo.git

# Verify
git remote -v
```

## Best Practices

### Commit Messages

Good commit messages:
```
✅ "Add user authentication feature"
✅ "Fix data persistence bug in Result.jsx"
✅ "Update README with deployment instructions"
```

Bad commit messages:
```
❌ "update"
❌ "fix bug"
❌ "changes"
```

### Commit Frequency

- Commit often (every logical change)
- Don't commit broken code
- Test before committing

### Branch Strategy

- `main` - Production-ready code
- `development` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### .gitignore

Always ignore:
- Dependencies (`node_modules/`, `venv/`)
- Build outputs (`dist/`, `build/`)
- Environment variables (`.env`)
- IDE files (`.vscode/`, `.idea/`)
- Logs (`*.log`)

## Next Steps

After uploading to GitHub:

1. **Add GitHub Actions** for CI/CD
2. **Enable Dependabot** for security updates
3. **Add issue templates** for bug reports
4. **Create pull request template**
5. **Set up branch protection rules**
6. **Add code owners** for review requirements

## Resources

- [GitHub Docs](https://docs.github.com)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub CLI](https://cli.github.com)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

## Support

If you encounter issues:
1. Check GitHub Status: https://www.githubstatus.com
2. Search GitHub Community: https://github.community
3. Contact GitHub Support: https://support.github.com

