---
name: attuned-migrations
description: Use when running database migrations, rollbacks, or schema changes against Supabase. Covers targeted migrations, bulk migrations, and common errors like psql not found or PgBouncer constraints.
---

# Attuned Migrations Skill

## Overview

Run SQL migrations against Supabase PostgreSQL using Python/Flask (not psql, which may not be installed locally).

## Quick Reference

| Task | Command |
|------|---------|
| Run specific migration | `python scripts/run_migration.py 033` |
| Run rollback | `python scripts/run_migration.py rollback_033` |
| Run all migrations | `python scripts/run_migrations.py --apply` |
| Dry run (preview) | `python scripts/run_migrations.py --dry-run` |
| Direct Python execution | See "Running via Flask Context" below |

## Migration File Conventions

```
migrations/
├── 000_APPLY_ALL_MIGRATIONS.sql    # Consolidated script
├── 000_ROLLBACK_ALL_MIGRATIONS.sql # Full rollback
├── 001_add_activity_extensions.sql # Forward migration
├── rollback_001.sql                # Paired rollback
├── 033_disable_apple_flagged.sql   # Forward migration
├── rollback_033.sql                # Paired rollback
```

**Naming:** `{number}_{description}.sql` and `rollback_{number}.sql`

## Running via Flask Context (Recommended)

When `psql` is not available or you need programmatic control:

```python
# Run from backend/ directory with venv activated
source venv/bin/activate && python3 -c "
from src.main import create_app, db
from src.models.activity import Activity  # Import models as needed
from datetime import datetime

app = create_app()

with app.app_context():
    # Option 1: Execute raw SQL
    from sqlalchemy import text
    sql = '''
    UPDATE activities
    SET is_active = false
    WHERE activity_id IN (822, 823, 824)
    '''
    result = db.session.execute(text(sql))
    db.session.commit()
    print(f'Rows affected: {result.rowcount}')

    # Option 2: Use ORM for complex operations
    updated = Activity.query.filter(
        Activity.activity_id.in_([822, 823, 824])
    ).update({'is_active': False}, synchronize_session='fetch')
    db.session.commit()
    print(f'Updated: {updated}')
"
```

## Running Specific Migration File

```python
source venv/bin/activate && python3 -c "
from src.main import create_app, db
from sqlalchemy import text
from pathlib import Path

app = create_app()

migration_file = Path('migrations/033_disable_apple_flagged_activities.sql')
sql_content = migration_file.read_text()

with app.app_context():
    db.session.execute(text(sql_content))
    db.session.commit()
    print(f'Migration {migration_file.name} applied successfully')
"
```

## Running Rollback

Same pattern, just use the rollback file:

```python
migration_file = Path('migrations/rollback_033.sql')
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `command not found: psql` | psql not installed locally | Use Python/Flask method above |
| `cannot execute DDL` | PgBouncer transaction mode | Use direct connection for DDL, or run via Supabase SQL Editor |
| `relation does not exist` | Migration order issue | Check dependencies, run prerequisite migrations first |
| `duplicate key` | Migration already applied | Check if data already exists, make migration idempotent |

## PgBouncer Constraints

Supabase uses PgBouncer in transaction mode. This means:

- **Cannot run**: `CREATE INDEX CONCURRENTLY`, `VACUUM`, `ALTER TYPE`
- **Can run**: Most DML (INSERT, UPDATE, DELETE) and simple DDL

For DDL operations, use the Supabase SQL Editor directly or the direct connection string (port 5432 instead of 6543).

## Idempotent Migration Patterns

Always write migrations that can be re-run safely:

```sql
-- Good: IF NOT EXISTS
CREATE INDEX IF NOT EXISTS idx_activities_is_active ON activities(is_active);
ALTER TABLE activities ADD COLUMN IF NOT EXISTS new_col TEXT;

-- Good: Check before update
UPDATE activities SET is_active = false
WHERE activity_id IN (822, 823) AND is_active = true;

-- Bad: Will fail on re-run
CREATE INDEX idx_activities_is_active ON activities(is_active);
```

## Verification After Migration

Always verify the migration worked:

```python
with app.app_context():
    # Check counts
    result = db.session.execute(text('''
        SELECT
            COUNT(*) FILTER (WHERE is_active = true) as active,
            COUNT(*) FILTER (WHERE is_active = false) as inactive
        FROM activities
    '''))
    row = result.fetchone()
    print(f'Active: {row[0]}, Inactive: {row[1]}')
```

## Creating New Migrations

1. Find next migration number: `ls migrations/*.sql | grep -E '^migrations/[0-9]{3}_' | tail -1`
2. Create migration file: `migrations/{number}_{description}.sql`
3. Create rollback file: `migrations/rollback_{number}.sql`
4. Test locally with `--dry-run` first
5. Apply and verify

## Checklist

- [ ] Migration file follows naming convention
- [ ] Rollback file created
- [ ] Migration is idempotent (can re-run safely)
- [ ] Tested with dry-run first
- [ ] Verified results after applying
- [ ] Committed to git on feature branch
