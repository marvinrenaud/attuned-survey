---
name: attuned-git-workflow
description: Git branching strategy, commit conventions, and version control workflow for Attuned
---

# Attuned Git Workflow

## Branch Strategy

```
main          # Production-ready, always stable, tagged releases
└── develop   # Integration branch
    ├── feature/subscription-webhooks
    ├── feature/promo-code-system
    ├── fix/compatibility-score-bug
    └── hotfix/critical-auth-fix
```

### Branch Naming
- `feature/` — new functionality
- `fix/` — bug fixes (non-urgent)
- `hotfix/` — critical production fixes
- `refactor/` — code restructure
- `test/` — test additions/improvements

## Commit Conventions

Use conventional commits:

```
feat: add RevenueCat webhook handler
fix: promo code case sensitivity issue
test: add auth tests for subscription endpoints
refactor: extract activity selection logic
docs: update API documentation
chore: upgrade psycopg to 3.1.2
```

Format: `type: short description (imperative mood)`

### Commit Message Rules
- Use imperative mood ("add" not "added")
- Keep first line under 72 characters
- Reference issue numbers when applicable: `fix: resolve #42 promo validation`

## Workflow

### Starting New Work
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### During Development
```bash
# Commit incrementally, not one giant commit
git add -p  # Stage selectively
git commit -m "feat: add webhook signature verification"

# Keep branch updated
git fetch origin
git rebase origin/develop
```

### Before Completing Work
```bash
# 1. Run tests
cd backend && pytest tests/ -v

# 2. Check for uncommitted changes
git status

# 3. Rebase on latest develop
git fetch origin
git rebase origin/develop

# 4. Squash if needed (interactive rebase)
git rebase -i origin/develop
```

### Merging
```bash
git checkout develop
git merge --no-ff feature/your-feature-name
git push origin develop

# Delete feature branch
git branch -d feature/your-feature-name
```

## Tagging Releases

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Initial launch release"

# Push tags
git push origin --tags

# List tags
git tag -l
```

### Version Format
- `v1.0.0` — major.minor.patch
- Major: breaking changes
- Minor: new features (backwards compatible)
- Patch: bug fixes

## Reverting

### Revert Last Commit (keeps history)
```bash
git revert HEAD
```

### Revert Specific Commit
```bash
git revert <commit-hash>
```

### Reset to Known Good State (destructive)
```bash
# Find the good commit
git log --oneline

# Reset (WARNING: loses commits after this point)
git reset --hard <commit-hash>

# If already pushed, force push (coordinate with team)
git push --force-with-lease origin branch-name
```

### Recover from Bad Merge
```bash
git revert -m 1 <merge-commit-hash>
```

## Pre-Merge Checklist

- [ ] All tests pass locally
- [ ] Branch is rebased on latest develop
- [ ] Commits follow conventional format
- [ ] No debug code or console.logs
- [ ] Auth tests exist for new endpoints
- [ ] Coverage maintained or improved
