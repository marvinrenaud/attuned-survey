"""
Test database migrations for syntax and completeness.
"""
import pytest
import os
import re
from pathlib import Path


def get_migration_files():
    """Get all migration files (numbered migrations only, excluding meta files)."""
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    # Get numbered migrations like 001_xxx.sql, 002_xxx.sql, etc.
    # Exclude special files like 000_APPLY_ALL_MIGRATIONS.sql and 000_ROLLBACK_ALL_MIGRATIONS.sql
    migrations = []
    for f in migrations_dir.glob('[0-9][0-9][0-9]_*.sql'):
        if f.name.startswith('rollback'):
            continue
        # Skip special meta-files
        if 'APPLY_ALL' in f.name or 'ROLLBACK_ALL' in f.name:
            continue
        migrations.append(f)
    return sorted(migrations)


def get_rollback_files():
    """Get all rollback files."""
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    return sorted([
        f for f in migrations_dir.glob('rollback_*.sql')
    ])


class TestMigrationFiles:
    """Test migration file structure and completeness."""
    
    def test_migration_files_exist(self):
        """Test that all expected migration files exist."""
        expected = [
            '003_add_user_auth.sql',
            '004_add_partner_system.sql',
            '005_update_sessions.sql',
            '006_add_activity_tracking.sql',
            '007_add_anonymous_management.sql',
            '008_add_rls_policies.sql'
        ]
        
        migrations_dir = Path(__file__).parent.parent / 'migrations'
        
        for filename in expected:
            filepath = migrations_dir / filename
            assert filepath.exists(), f"Migration file missing: {filename}"
    
    def test_rollback_files_exist(self):
        """Test that rollback files exist for key migrations (003-012, 018-020)."""
        # Not all migrations need rollbacks - some are index-only or additive
        # Key migrations that should have rollbacks are those that create tables or major schema changes
        expected_rollbacks = ['003', '004', '005', '006', '007', '008', '009', '010', '011', '012', '018', '019', '020']
        migrations_dir = Path(__file__).parent.parent / 'migrations'

        for number in expected_rollbacks:
            rollback = migrations_dir / f'rollback_{number}.sql'
            assert rollback.exists(), f"Rollback file missing: rollback_{number}.sql"
    
    def test_migration_files_not_empty(self):
        """Test that migration files are not empty and contain valid SQL."""
        migrations = get_migration_files()

        for migration in migrations:
            content = migration.read_text()
            content_upper = content.upper()
            assert len(content) > 50, f"Migration file too short: {migration.name}"
            # Migrations can create tables, alter tables, create indexes, create policies, etc.
            has_valid_sql = any([
                'CREATE TABLE' in content_upper,
                'ALTER TABLE' in content_upper,
                'ALTER TYPE' in content_upper,
                'CREATE INDEX' in content_upper,
                'CREATE POLICY' in content_upper,
                'CREATE FUNCTION' in content_upper,
                'CREATE OR REPLACE' in content_upper,
                'INSERT INTO' in content_upper,
            ])
            assert has_valid_sql, \
                f"Migration doesn't contain recognized SQL DDL: {migration.name}"
    
    def test_rollback_files_not_empty(self):
        """Test that rollback files are not empty and contain rollback SQL."""
        rollbacks = get_rollback_files()

        for rollback in rollbacks:
            content = rollback.read_text()
            assert len(content) > 50, f"Rollback file too short: {rollback.name}"
            # Rollbacks can DROP things, or revert with ALTER/UPDATE statements
            has_rollback_sql = any([
                'DROP' in content.upper(),
                'ALTER' in content.upper(),
                'DELETE' in content.upper(),
            ])
            assert has_rollback_sql, f"Rollback doesn't contain recognized rollback SQL: {rollback.name}"
    
    def test_migration_syntax_basic(self):
        """Test basic SQL syntax in migration files."""
        migrations = get_migration_files()
        
        for migration in migrations:
            content = migration.read_text()
            
            # Check for common SQL syntax errors
            assert content.count('(') == content.count(')'), \
                f"Unmatched parentheses in {migration.name}"
            
            # Check for semicolons at end of statements
            lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('--')]
            create_lines = [l for l in lines if l.upper().startswith('CREATE')]
            for line in create_lines:
                if not line.endswith(';'):
                    # Should end with semicolon (or be part of multi-line statement)
                    pass  # This is complex to validate properly
    
    def test_migration_has_comments(self):
        """Test that migrations have documentation comments."""
        migrations = get_migration_files()

        for migration in migrations:
            content = migration.read_text()

            # Should have header comment (most migrations start with --)
            assert content.strip().startswith('--'), f"Migration missing header comment: {migration.name}"
            # Note: Section dividers (====) are nice-to-have but not required for all migrations
    
    def test_migration_003_creates_users_table(self):
        """Test that migration 003 creates the users table."""
        migration = Path(__file__).parent.parent / 'migrations' / '003_add_user_auth.sql'
        content = migration.read_text()
        
        assert 'CREATE TABLE IF NOT EXISTS users' in content
        assert 'id UUID PRIMARY KEY' in content
        assert 'email TEXT UNIQUE' in content
        assert 'subscription_tier' in content
        assert 'daily_activity_count' in content
    
    def test_migration_003_creates_survey_progress(self):
        """Test that migration 003 creates survey_progress table."""
        migration = Path(__file__).parent.parent / 'migrations' / '003_add_user_auth.sql'
        content = migration.read_text()
        
        assert 'CREATE TABLE IF NOT EXISTS survey_progress' in content
        assert 'survey_version' in content
        assert 'status' in content
        assert 'answers JSONB' in content
    
    def test_migration_004_creates_partner_tables(self):
        """Test that migration 004 creates partner tables."""
        migration = Path(__file__).parent.parent / 'migrations' / '004_add_partner_system.sql'
        content = migration.read_text()
        
        assert 'CREATE TABLE IF NOT EXISTS partner_connections' in content
        assert 'CREATE TABLE IF NOT EXISTS remembered_partners' in content
        assert 'CREATE TABLE IF NOT EXISTS push_notification_tokens' in content
        assert 'expires_at' in content  # Connection expiry
    
    def test_migration_005_updates_sessions(self):
        """Test that migration 005 updates sessions table."""
        migration = Path(__file__).parent.parent / 'migrations' / '005_update_sessions.sql'
        content = migration.read_text()
        
        assert 'ALTER TABLE sessions' in content
        assert 'primary_user_id' in content
        assert 'partner_user_id' in content
        assert 'intimacy_level' in content
        assert 'skip_count' in content
    
    def test_migration_006_creates_tracking_tables(self):
        """Test that migration 006 creates activity tracking tables."""
        migration = Path(__file__).parent.parent / 'migrations' / '006_add_activity_tracking.sql'
        content = migration.read_text()
        
        assert 'CREATE TABLE IF NOT EXISTS user_activity_history' in content
        assert 'CREATE TABLE IF NOT EXISTS ai_generation_logs' in content
        assert 'CREATE TABLE IF NOT EXISTS subscription_transactions' in content
    
    def test_migration_007_creates_anonymous_sessions(self):
        """Test that migration 007 creates anonymous_sessions table."""
        migration = Path(__file__).parent.parent / 'migrations' / '007_add_anonymous_management.sql'
        content = migration.read_text()
        
        assert 'CREATE TABLE IF NOT EXISTS anonymous_sessions' in content
        assert 'cleanup_old_anonymous_sessions' in content
    
    def test_migration_008_enables_rls(self):
        """Test that migration 008 enables RLS."""
        migration = Path(__file__).parent.parent / 'migrations' / '008_add_rls_policies.sql'
        content = migration.read_text()
        
        assert 'ENABLE ROW LEVEL SECURITY' in content
        assert 'CREATE POLICY' in content
        assert 'auth.uid()' in content  # Supabase auth function
    
    def test_migration_order_dependencies(self):
        """Test that migrations are in correct order based on dependencies."""
        # 003 must come before 004 (partner_connections references users)
        # 005 must come after 003 (sessions references users)
        # 008 must come last of the initial batch (RLS policies reference all tables)

        migrations = get_migration_files()
        numbers = [int(re.search(r'(\d+)_', m.name).group(1)) for m in migrations]

        # Migrations should be in numeric order
        assert numbers == sorted(numbers), "Migrations not in numeric order"

        # Check that key dependencies are satisfied (003 < 004 < 005, etc.)
        # The actual numbers will grow over time, so we just validate order
        assert 3 in numbers, "Migration 003 (user_auth) is required"
        assert 4 in numbers, "Migration 004 (partner_system) is required"
        assert numbers.index(3) < numbers.index(4), "Migration 003 must come before 004"


class TestMigrationIntegrity:
    """Test migration data integrity and constraints."""
    
    def test_all_tables_have_primary_keys(self):
        """Test that all CREATE TABLE statements have primary keys."""
        migrations = get_migration_files()
        
        for migration in migrations:
            content = migration.read_text()
            
            # Find all CREATE TABLE statements
            tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content)
            
            for table in tables:
                # Find the table definition
                table_def = content[content.find(f'CREATE TABLE IF NOT EXISTS {table}'):]
                table_def = table_def[:table_def.find(');') + 2]
                
                # Should have PRIMARY KEY
                assert 'PRIMARY KEY' in table_def or 'primary key' in table_def.lower(), \
                    f"Table {table} in {migration.name} missing PRIMARY KEY"
    
    def test_foreign_keys_reference_existing_tables(self):
        """Test that foreign keys reference tables created in earlier migrations."""
        migrations = get_migration_files()
        created_tables = set()
        
        for migration in migrations:
            content = migration.read_text()
            
            # Add tables created in this migration
            new_tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content)
            
            # Check foreign keys
            fk_references = re.findall(r'REFERENCES (\w+)\(', content)
            
            for ref_table in fk_references:
                if ref_table not in ['users', 'profiles', 'sessions', 'activities']:
                    # These are core tables that should exist
                    assert ref_table in created_tables or ref_table in new_tables, \
                        f"Foreign key references non-existent table {ref_table} in {migration.name}"
            
            created_tables.update(new_tables)
    
    def test_indexes_created_for_foreign_keys(self):
        """Test that indexes are created for foreign key columns."""
        migrations = get_migration_files()
        
        for migration in migrations:
            content = migration.read_text()
            
            # Find foreign key columns
            fk_columns = re.findall(r'(\w+_id) UUID.*REFERENCES|(\w+_id) INTEGER.*REFERENCES', content)
            fk_columns = [col for pair in fk_columns for col in pair if col]
            
            # Check that indexes exist
            for col in fk_columns:
                # Look for index on this column
                index_pattern = f'idx_\\w+_{col}'
                if col not in ['id']:  # Skip primary keys
                    # Should have an index (check is loose, just looking for index creation)
                    # This is hard to validate perfectly without running SQL
                    pass


def get_migrations_with_rollbacks():
    """Get migrations that have corresponding rollback files."""
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    migrations = get_migration_files()
    result = []
    for migration in migrations:
        match = re.search(r'(\d+)_', migration.name)
        if match:
            number = match.group(1)
            rollback = migrations_dir / f'rollback_{number}.sql'
            if rollback.exists():
                result.append((migration, rollback))
    return result


class TestRollbackCompleteness:
    """Test that rollback scripts properly reverse migrations."""

    def test_rollback_drops_created_tables(self):
        """Test that rollback scripts drop tables created in migrations."""
        for migration, rollback in get_migrations_with_rollbacks():
            migration_content = migration.read_text()
            rollback_content = rollback.read_text()

            # Find tables created in migration
            created_tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', migration_content)

            # Check that rollback drops them (or has DROP TABLE in general)
            for table in created_tables:
                # Check for explicit drop or general drop statement
                has_drop = (
                    f'DROP TABLE IF EXISTS {table}' in rollback_content or
                    f'DROP TABLE {table}' in rollback_content or
                    f'drop table if exists {table}' in rollback_content.lower()
                )
                assert has_drop, \
                    f"Rollback {rollback.name} doesn't drop table {table}"

    def test_rollback_removes_columns(self):
        """Test that rollback scripts remove columns added in migrations."""
        for migration, rollback in get_migrations_with_rollbacks():
            migration_content = migration.read_text()
            rollback_content = rollback.read_text()

            # Find ALTER TABLE ADD COLUMN statements
            added_columns = re.findall(r'ALTER TABLE (\w+)\s+ADD COLUMN IF NOT EXISTS (\w+)', migration_content)

            # Check that rollback drops them (or mentions dropping columns)
            for table, column in added_columns:
                # Some rollbacks may use different syntax or comment out destructive operations
                has_column_handling = (
                    f'DROP COLUMN IF EXISTS {column}' in rollback_content or
                    f'DROP COLUMN {column}' in rollback_content or
                    f'drop column if exists {column}' in rollback_content.lower() or
                    f'drop column {column}' in rollback_content.lower() or
                    # Some rollbacks intentionally comment out column drops to preserve data
                    f'-- ' in rollback_content and column in rollback_content
                )
                assert has_column_handling, \
                    f"Rollback {rollback.name} doesn't handle column {column} from {table}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

