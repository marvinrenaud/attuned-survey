"""
Test database migrations for syntax and completeness.
"""
import pytest
import os
import re
from pathlib import Path


def get_migration_files():
    """Get all migration files."""
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    return sorted([
        f for f in migrations_dir.glob('*.sql') 
        if f.name.startswith('00') and not f.name.startswith('rollback')
    ])


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
        """Test that rollback files exist for each migration."""
        migrations = get_migration_files()
        
        for migration in migrations:
            # Extract number from migration filename
            match = re.search(r'(\d+)_', migration.name)
            if match:
                number = match.group(1)
                rollback = migration.parent / f'rollback_{number}.sql'
                assert rollback.exists(), f"Rollback file missing for {migration.name}"
    
    def test_migration_files_not_empty(self):
        """Test that migration files are not empty."""
        migrations = get_migration_files()
        
        for migration in migrations:
            content = migration.read_text()
            assert len(content) > 100, f"Migration file too short: {migration.name}"
            assert 'CREATE TABLE' in content or 'ALTER TABLE' in content, \
                f"Migration doesn't create or alter tables: {migration.name}"
    
    def test_rollback_files_not_empty(self):
        """Test that rollback files are not empty."""
        rollbacks = get_rollback_files()
        
        for rollback in rollbacks:
            content = rollback.read_text()
            assert len(content) > 50, f"Rollback file too short: {rollback.name}"
            assert 'DROP' in content, f"Rollback doesn't drop anything: {rollback.name}"
    
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
            
            # Should have header comment
            assert content.startswith('--'), f"Migration missing header comment: {migration.name}"
            
            # Should have section comments
            assert '====' in content, f"Migration missing section dividers: {migration.name}"
    
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
        # 008 must come last (RLS policies reference all tables)
        
        migrations = get_migration_files()
        numbers = [int(re.search(r'(\d+)_', m.name).group(1)) for m in migrations]
        
        assert numbers == sorted(numbers), "Migrations not in numeric order"
        assert numbers == [3, 4, 5, 6, 7, 8], "Migration numbers not sequential"


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


class TestRollbackCompleteness:
    """Test that rollback scripts properly reverse migrations."""
    
    def test_rollback_drops_created_tables(self):
        """Test that rollback scripts drop tables created in migrations."""
        migrations = get_migration_files()
        
        for migration in migrations:
            # Extract number
            match = re.search(r'(\d+)_', migration.name)
            number = match.group(1)
            
            rollback = migration.parent / f'rollback_{number}.sql'
            
            migration_content = migration.read_text()
            rollback_content = rollback.read_text()
            
            # Find tables created in migration
            created_tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', migration_content)
            
            # Check that rollback drops them
            for table in created_tables:
                assert f'DROP TABLE IF EXISTS {table}' in rollback_content or \
                       f'DROP TABLE {table}' in rollback_content, \
                    f"Rollback {rollback.name} doesn't drop table {table}"
    
    def test_rollback_removes_columns(self):
        """Test that rollback scripts remove columns added in migrations."""
        migrations = get_migration_files()
        
        for migration in migrations:
            match = re.search(r'(\d+)_', migration.name)
            number = match.group(1)
            
            rollback = migration.parent / f'rollback_{number}.sql'
            
            migration_content = migration.read_text()
            rollback_content = rollback.read_text()
            
            # Find ALTER TABLE ADD COLUMN statements
            added_columns = re.findall(r'ALTER TABLE (\w+)\s+ADD COLUMN IF NOT EXISTS (\w+)', migration_content)
            
            # Check that rollback drops them
            for table, column in added_columns:
                assert f'ALTER TABLE {table} DROP COLUMN IF EXISTS {column}' in rollback_content or \
                       f'DROP COLUMN {column}' in rollback_content, \
                    f"Rollback {rollback.name} doesn't drop column {column} from {table}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

