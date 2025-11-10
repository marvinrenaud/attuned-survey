#!/usr/bin/env python3
"""
Run diagnostic queries on activities table and generate metrics report.
"""
import sys
import os
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from src.models.activity import Activity
from sqlalchemy import text, func


def count_by_audience_scope():
    """Count activities by audience scope."""
    with app.app_context():
        results = db.session.query(
            Activity.audience_scope,
            func.count(Activity.activity_id)
        ).filter(
            Activity.is_active == True
        ).group_by(Activity.audience_scope).all()
        
        return {scope: count for scope, count in results}


def count_by_anatomy():
    """Count activities with anatomy requirements."""
    with app.app_context():
        total = Activity.query.filter_by(is_active=True).count()
        
        # Count activities with any active anatomy requirement
        active_anatomy = 0
        partner_anatomy = 0
        both_anatomy = 0
        neither_anatomy = 0
        
        activities = Activity.query.filter_by(is_active=True).all()
        for activity in activities:
            bodyparts = activity.required_bodyparts or {"active": [], "partner": []}
            active_parts = bodyparts.get('active', [])
            partner_parts = bodyparts.get('partner', [])
            
            if active_parts and partner_parts:
                both_anatomy += 1
            elif active_parts:
                active_anatomy += 1
            elif partner_parts:
                partner_anatomy += 1
            else:
                neither_anatomy += 1
        
        return {
            'total': total,
            'with_active_anatomy': active_anatomy,
            'with_partner_anatomy': partner_anatomy,
            'with_both_anatomy': both_anatomy,
            'with_no_anatomy': neither_anatomy
        }


def count_boundary_distribution():
    """Count boundary usage distribution."""
    with app.app_context():
        activities = Activity.query.filter_by(is_active=True).all()
        
        boundary_counter = Counter()
        for activity in activities:
            boundaries = activity.hard_boundaries or []
            for boundary in boundaries:
                boundary_counter[boundary] += 1
        
        return boundary_counter


def count_enrichment_coverage():
    """Count AI enrichment coverage."""
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
        
        # Count by power role
        power_role_counts = db.session.query(
            Activity.power_role,
            func.count(Activity.activity_id)
        ).filter(
            Activity.is_active == True,
            Activity.power_role.isnot(None)
        ).group_by(Activity.power_role).all()
        
        return {
            'total': total,
            'with_power_role': with_power_role,
            'with_preferences': with_preferences,
            'power_role_distribution': {role: count for role, count in power_role_counts}
        }


def check_index_usage():
    """Check index usage statistics."""
    with app.app_context():
        result = db.session.execute(text("""
            SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE tablename = 'activities'
            ORDER BY idx_scan DESC
        """))
        
        indexes = []
        for row in result:
            indexes.append({
                'name': row[2],
                'scans': row[3],
                'tuples_read': row[4],
                'tuples_fetched': row[5]
            })
        
        return indexes


def count_by_rating_and_intensity():
    """Count activities by rating and intensity."""
    with app.app_context():
        results = db.session.query(
            Activity.rating,
            Activity.intensity,
            func.count(Activity.activity_id)
        ).filter(
            Activity.is_active == True
        ).group_by(Activity.rating, Activity.intensity).all()
        
        distribution = {}
        for rating, intensity, count in results:
            if rating not in distribution:
                distribution[rating] = {}
            distribution[rating][intensity] = count
        
        return distribution


def simulate_filtering():
    """Simulate session filtering to show candidate counts."""
    with app.app_context():
        # Simulate a couples session with R-rating
        couples_r = Activity.query.filter(
            Activity.is_active == True,
            Activity.approved == True,
            Activity.rating == 'R',
            Activity.audience_scope.in_(['couples', 'all'])
        ).count()
        
        # Simulate a groups session with R-rating
        groups_r = Activity.query.filter(
            Activity.is_active == True,
            Activity.approved == True,
            Activity.rating == 'R',
            Activity.audience_scope.in_(['groups', 'all'])
        ).count()
        
        # Count activities with specific boundaries
        with_boundaries = Activity.query.filter(
            Activity.is_active == True,
            Activity.hard_boundaries != []
        ).count()
        
        # Count activities with anatomy requirements
        activities = Activity.query.filter_by(is_active=True).all()
        with_anatomy = 0
        for activity in activities:
            bodyparts = activity.required_bodyparts or {"active": [], "partner": []}
            if bodyparts.get('active') or bodyparts.get('partner'):
                with_anatomy += 1
        
        return {
            'couples_r_rated': couples_r,
            'groups_r_rated': groups_r,
            'with_boundaries': with_boundaries,
            'with_anatomy_requirements': with_anatomy
        }


def generate_diagnostics_report():
    """Generate comprehensive diagnostics report."""
    print("=" * 70)
    print("Activity Bank Diagnostics")
    print("=" * 70)
    print()
    
    # Audience scope distribution
    print("Activity Counts by Audience Scope:")
    print("─" * 70)
    audience_counts = count_by_audience_scope()
    for scope, count in sorted(audience_counts.items()):
        print(f"  {scope}: {count}")
    print()
    
    # Anatomy requirements
    print("Activities with Anatomy Requirements:")
    print("─" * 70)
    anatomy_stats = count_by_anatomy()
    print(f"  Total active activities: {anatomy_stats['total']}")
    print(f"  With active anatomy requirements: {anatomy_stats['with_active_anatomy']}")
    print(f"  With partner anatomy requirements: {anatomy_stats['with_partner_anatomy']}")
    print(f"  With both anatomy requirements: {anatomy_stats['with_both_anatomy']}")
    print(f"  With no anatomy requirements: {anatomy_stats['with_no_anatomy']}")
    print()
    
    # Boundary distribution
    print("Boundary Flags Distribution:")
    print("─" * 70)
    boundary_dist = count_boundary_distribution()
    if boundary_dist:
        for boundary, count in boundary_dist.most_common():
            print(f"  {boundary}: {count} activities")
    else:
        print("  No boundary flags found")
    print()
    
    # Enrichment coverage
    print("AI Enrichment Coverage:")
    print("─" * 70)
    enrichment = count_enrichment_coverage()
    coverage_pct = (enrichment['with_power_role'] / enrichment['total'] * 100) if enrichment['total'] > 0 else 0
    print(f"  Total activities: {enrichment['total']}")
    print(f"  With power role tags: {enrichment['with_power_role']} ({coverage_pct:.1f}%)")
    print(f"  With preference keys: {enrichment['with_preferences']}")
    
    if enrichment['power_role_distribution']:
        print(f"\n  Power Role Distribution:")
        for role, count in sorted(enrichment['power_role_distribution'].items()):
            print(f"    {role}: {count}")
    print()
    
    # Rating and intensity distribution
    print("Activities by Rating and Intensity:")
    print("─" * 70)
    rating_dist = count_by_rating_and_intensity()
    for rating in ['G', 'R', 'X']:
        if rating in rating_dist:
            print(f"  {rating}-rated:")
            for intensity in sorted(rating_dist[rating].keys()):
                print(f"    Intensity {intensity}: {rating_dist[rating][intensity]}")
    print()
    
    # Filtering simulation
    print("Session Filtering Simulation:")
    print("─" * 70)
    simulation = simulate_filtering()
    print(f"  Couples R-rated candidates: {simulation['couples_r_rated']}")
    print(f"  Groups R-rated candidates: {simulation['groups_r_rated']}")
    print(f"  Activities with boundary flags: {simulation['with_boundaries']}")
    print(f"  Activities with anatomy requirements: {simulation['with_anatomy_requirements']}")
    print()
    
    # Index usage
    print("Index Usage Statistics:")
    print("─" * 70)
    indexes = check_index_usage()
    if indexes:
        for idx in indexes[:10]:  # Top 10
            print(f"  {idx['name']}")
            print(f"    Scans: {idx['scans']}, Tuples read: {idx['tuples_read']}")
    else:
        print("  No index statistics available")
    print()
    
    print("=" * 70)
    print("✅ Diagnostics complete")
    print("=" * 70)


if __name__ == '__main__':
    with app.app_context():
        generate_diagnostics_report()
    sys.exit(0)

