#!/usr/bin/env python3
"""
Batch tag truth activities with truth_topics using AI analysis.

This script:
1. Queries all truth-type activities from the database
2. Analyzes each using the LLM to determine applicable truth_topics
3. Updates the activities table with the tags

Usage:
    python scripts/tag_truth_topics.py --dry-run     # Preview without saving
    python scripts/tag_truth_topics.py --apply       # Apply changes to database
    python scripts/tag_truth_topics.py --apply --limit 10  # Process only 10 activities
"""

import sys
import os
import argparse
import time
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import app
from src.extensions import db
from src.models.activity import Activity
from src.llm.activity_analyzer import analyze_activity, TRUTH_TOPICS
from sqlalchemy import text


def get_truth_activities(limit: Optional[int] = None) -> List[Dict]:
    """Get all truth-type activities from database."""
    with app.app_context():
        query = Activity.query.filter(Activity.type == 'truth')

        if limit:
            query = query.limit(limit)

        activities = query.all()

        results = []
        for a in activities:
            # Extract description from script
            script = a.script or {}
            steps = script.get('steps', [])
            # Combine all step descriptions into one string
            description_parts = [step.get('do', '') for step in steps if step.get('do')]
            description = ' '.join(description_parts)

            results.append({
                'id': str(a.activity_id),
                'description': description,
                'type': a.type,
                'rating': a.rating,
                'intensity': a.intensity,
                'current_truth_topics': a.truth_topics or [],
            })
        return results


def analyze_truth_topics_only(activity: Dict) -> List[str]:
    """
    Analyze activity to extract truth_topics only.

    Uses a focused prompt to classify which sensitive topics
    the truth activity might explore.
    """
    description = activity.get('description', '')

    # Use the full analyze_activity which now includes truth_topics
    try:
        result = analyze_activity(
            description=description,
            activity_type='truth',
            intimacy_level=activity.get('rating', 'R'),
            row_id=activity.get('id', 'unknown')
        )
        return result.get('truth_topics', [])
    except Exception as e:
        print(f"    Error analyzing {activity['id']}: {e}")
        return []


def update_activity_truth_topics(activity_id: str, truth_topics: List[str]) -> bool:
    """Update a single activity's truth_topics in the database."""
    with app.app_context():
        try:
            activity = Activity.query.filter_by(activity_id=int(activity_id)).first()
            if activity:
                activity.truth_topics = truth_topics
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"    Error updating {activity_id}: {e}")
            return False


def run_batch_tagging(dry_run: bool = True, limit: Optional[int] = None, delay: float = 0.5, retag: bool = False):
    """
    Run batch tagging of truth activities.

    Args:
        dry_run: If True, only preview changes without saving
        limit: Maximum number of activities to process
        delay: Delay between API calls (rate limiting)
        retag: If True, re-tag activities even if already tagged
    """
    print("=" * 70)
    print("  TRUTH TOPIC BATCH TAGGING")
    print("=" * 70)

    # Get activities
    print("\nFetching truth activities from database...")
    activities = get_truth_activities(limit)
    print(f"Found {len(activities)} truth activities to process")

    if not activities:
        print("No activities to process.")
        return

    # Process each activity
    results = {
        'processed': 0,
        'tagged': 0,
        'skipped': 0,
        'errors': 0,
        'topics_distribution': {topic: 0 for topic in TRUTH_TOPICS},
        'untagged': 0,
    }

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing activities...")
    print("-" * 70)

    for i, activity in enumerate(activities, 1):
        activity_id = activity['id']
        description = activity['description'][:60] if activity['description'] else '(no description)'
        current_topics = activity['current_truth_topics']

        print(f"\n[{i}/{len(activities)}] {description}...")

        # Skip if already tagged (unless retag is enabled)
        if current_topics and not retag:
            print(f"    Already tagged: {current_topics}")
            results['skipped'] += 1
            continue
        elif current_topics and retag:
            print(f"    Re-tagging (was: {current_topics})")

        # Analyze activity
        try:
            truth_topics = analyze_truth_topics_only(activity)
            results['processed'] += 1

            if truth_topics:
                print(f"    Topics identified: {truth_topics}")
                results['tagged'] += 1
                for topic in truth_topics:
                    results['topics_distribution'][topic] += 1
            else:
                print(f"    No topics identified (will bypass filter)")
                results['untagged'] += 1

            # Update database if not dry run
            if not dry_run:
                if update_activity_truth_topics(activity_id, truth_topics):
                    print(f"    Saved to database")
                else:
                    print(f"    Failed to save")
                    results['errors'] += 1

            # Rate limiting
            time.sleep(delay)

        except Exception as e:
            print(f"    Error: {e}")
            results['errors'] += 1

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"\n  Total activities:     {len(activities)}")
    print(f"  Processed:            {results['processed']}")
    print(f"  Already tagged:       {results['skipped']}")
    print(f"  Newly tagged:         {results['tagged']}")
    print(f"  No topics (bypass):   {results['untagged']}")
    print(f"  Errors:               {results['errors']}")

    print(f"\n  Topic Distribution:")
    for topic, count in sorted(results['topics_distribution'].items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"    {topic}: {count}")

    if dry_run:
        print(f"\n  [DRY RUN] No changes were saved to database.")
        print(f"  Run with --apply to save changes.")


def main():
    parser = argparse.ArgumentParser(
        description='Batch tag truth activities with truth_topics',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                       help='Preview changes without saving')
    group.add_argument('--apply', action='store_true',
                       help='Apply changes to database')

    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of activities to process')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between API calls in seconds (default: 0.5)')
    parser.add_argument('--retag', action='store_true',
                       help='Re-tag activities even if already tagged')

    args = parser.parse_args()

    run_batch_tagging(
        dry_run=args.dry_run,
        limit=args.limit,
        delay=args.delay,
        retag=args.retag
    )


if __name__ == '__main__':
    main()
