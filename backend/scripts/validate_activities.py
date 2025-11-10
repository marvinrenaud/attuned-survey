#!/usr/bin/env python3
"""
Comprehensive validation script for activities table.
Checks schema, data integrity, and constraint compliance.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from src.models.activity import Activity, ALLOWED_BOUNDARIES, ALLOWED_BODYPARTS
from sqlalchemy import text


def check_no_null_required_fields():
    """Check that required fields are not null."""
    with app.app_context():
        null_checks = {
            'type': Activity.query.filter(Activity.type.is_(None)).count(),
            'rating': Activity.query.filter(Activity.rating.is_(None)).count(),
            'intensity': Activity.query.filter(Activity.intensity.is_(None)).count(),
            'is_active': Activity.query.filter(Activity.is_active.is_(None)).count(),
            'approved': Activity.query.filter(Activity.approved.is_(None)).count(),
        }
        
        passed = all(count == 0 for count in null_checks.values())
        return {
            'name': 'No NULL required fields',
            'passed': passed,
            'details': null_checks if not passed else None
        }


def check_boundary_keys_valid():
    """Check that all boundary keys are in allowed list."""
    with app.app_context():
        activities = Activity.query.filter(Activity.hard_boundaries.isnot(None)).all()
        
        invalid = []
        for activity in activities:
            boundaries = activity.hard_boundaries or []
            for boundary in boundaries:
                if boundary not in ALLOWED_BOUNDARIES:
                    invalid.append({
                        'activity_id': activity.activity_id,
                        'invalid_key': boundary
                    })
        
        passed = len(invalid) == 0
        return {
            'name': 'All boundary keys valid',
            'passed': passed,
            'details': f"Found {len(invalid)} invalid keys" if not passed else f"Checked {len(activities)} activities"
        }


def check_bodyparts_structure():
    """Check that required_bodyparts has correct structure."""
    with app.app_context():
        activities = Activity.query.all()
        
        invalid = []
        for activity in activities:
            bodyparts = activity.required_bodyparts
            if not isinstance(bodyparts, dict):
                invalid.append(f"Activity {activity.activity_id}: not a dict")
                continue
            
            if 'active' not in bodyparts or 'partner' not in bodyparts:
                invalid.append(f"Activity {activity.activity_id}: missing keys")
                continue
            
            for part in bodyparts.get('active', []):
                if part not in ALLOWED_BODYPARTS:
                    invalid.append(f"Activity {activity.activity_id}: invalid active part '{part}'")
            
            for part in bodyparts.get('partner', []):
                if part not in ALLOWED_BODYPARTS:
                    invalid.append(f"Activity {activity.activity_id}: invalid partner part '{part}'")
        
        passed = len(invalid) == 0
        return {
            'name': 'Required bodyparts structure valid',
            'passed': passed,
            'details': invalid[:5] if not passed else f"Checked {len(activities)} activities"
        }


def check_audience_scope_valid():
    """Check that audience_scope values are valid."""
    with app.app_context():
        invalid = Activity.query.filter(
            ~Activity.audience_scope.in_(['couples', 'groups', 'all'])
        ).count()
        
        passed = invalid == 0
        return {
            'name': 'Audience scope values valid',
            'passed': passed,
            'details': f"Found {invalid} invalid values" if not passed else "All values valid"
        }


def check_activity_uid_unique():
    """Check that activity_uid is unique."""
    with app.app_context():
        result = db.session.execute(text("""
            SELECT activity_uid, COUNT(*) as count
            FROM activities
            WHERE activity_uid IS NOT NULL
            GROUP BY activity_uid
            HAVING COUNT(*) > 1
        """))
        
        duplicates = list(result)
        passed = len(duplicates) == 0
        return {
            'name': 'Activity UID unique',
            'passed': passed,
            'details': f"Found {len(duplicates)} duplicates" if not passed else "All UIDs unique"
        }


def check_enrichment_coverage():
    """Check enrichment coverage (AI tags)."""
    with app.app_context():
        total = Activity.query.filter_by(is_active=True).count()
        with_power_role = Activity.query.filter(
            Activity.is_active == True,
            Activity.power_role.isnot(None)
        ).count()
        with_preferences = Activity.query.filter(
            Activity.is_active == True,
            Activity.preference_keys.isnot(None)
        ).count()
        
        coverage_pct = (with_power_role / total * 100) if total > 0 else 0
        passed = coverage_pct > 50  # At least 50% coverage
        
        return {
            'name': 'Enrichment coverage',
            'passed': passed,
            'details': f"{with_power_role}/{total} activities ({coverage_pct:.1f}%) have AI tags"
        }


def check_indexes_exist():
    """Check that required indexes exist."""
    with app.app_context():
        result = db.session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'activities'
        """))
        
        indexes = {row[0] for row in result}
        required = {
            'idx_activities_hard_boundaries',
            'idx_activities_required_bodyparts',
            'idx_activities_audience_scope',
            'idx_activities_activity_uid',
            'idx_activities_is_active',
            'idx_activities_active_lookup'
        }
        
        missing = required - indexes
        passed = len(missing) == 0
        
        return {
            'name': 'Required indexes exist',
            'passed': passed,
            'details': f"Missing: {missing}" if not passed else f"All {len(required)} indexes present"
        }


def generate_validation_report(checks):
    """Generate a formatted validation report."""
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("Activity Validation Report")
    report_lines.append("=" * 70)
    report_lines.append("")
    
    passed_count = sum(1 for c in checks if c['passed'])
    failed_count = len(checks) - passed_count
    
    for check in checks:
        status = "✅ PASS" if check['passed'] else "❌ FAIL"
        report_lines.append(f"{status}: {check['name']}")
        if check.get('details'):
            report_lines.append(f"       {check['details']}")
        report_lines.append("")
    
    report_lines.append("=" * 70)
    report_lines.append(f"Summary: {passed_count} passed, {failed_count} failed")
    report_lines.append("=" * 70)
    
    return "\n".join(report_lines)


def save_report(report, output_path):
    """Save report to file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"\n✓ Report saved to {output_path}")


def validate_activities():
    """Run all validation checks."""
    print("=" * 70)
    print("Activity Validation")
    print("=" * 70)
    print()
    
    checks = [
        check_no_null_required_fields(),
        check_boundary_keys_valid(),
        check_bodyparts_structure(),
        check_audience_scope_valid(),
        check_activity_uid_unique(),
        check_enrichment_coverage(),
        check_indexes_exist(),
    ]
    
    report = generate_validation_report(checks)
    print(report)
    
    # Save report
    save_report(report, 'reports/validation_report.md')
    
    # Return exit code
    if all(c['passed'] for c in checks):
        print("\n✅ All validation checks passed")
        return 0
    else:
        print("\n❌ Some validation checks failed")
        return 1


if __name__ == '__main__':
    with app.app_context():
        exit_code = validate_activities()
    sys.exit(exit_code)

