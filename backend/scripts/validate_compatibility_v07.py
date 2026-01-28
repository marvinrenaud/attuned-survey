#!/usr/bin/env python
"""
Validate compatibility algorithm v0.7 against real user profiles.

This script queries the production database for accepted partner connections,
retrieves their profiles, and runs the compatibility algorithm to validate
that scores fall within expected ranges for real couples.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/validate_compatibility_v07.py
"""

import os
import sys
from pathlib import Path

# Change to backend directory and add src to path
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir / "src"))

from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

# Import using the package structure
from src.main import create_app
from src.extensions import db
from src.models.profile import Profile
from src.models.partner import PartnerConnection
from src.models.user import User
from src.compatibility.calculator import calculate_compatibility


def get_accepted_connections() -> List[PartnerConnection]:
    """Get all accepted partner connections."""
    return PartnerConnection.query.filter_by(status='accepted').all()


def get_profile_for_user(user_id: str) -> Optional[Profile]:
    """Get the most recent profile for a user."""
    return Profile.query.filter_by(user_id=user_id).order_by(Profile.created_at.desc()).first()


def profile_to_compat_format(profile: Profile) -> Dict[str, Any]:
    """Convert a Profile model to the format expected by calculate_compatibility."""
    return {
        'power_dynamic': profile.power_dynamic or {},
        'arousal_propensity': profile.arousal_propensity or {},
        'domain_scores': profile.domain_scores or {},
        'activities': profile.activities or {},
        'truth_topics': profile.truth_topics or {},
        'boundaries': profile.boundaries or {},
    }


def classify_score(score: int) -> str:
    """Classify a compatibility score into a human-readable category."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Moderate"
    elif score >= 45:
        return "Low"
    else:
        return "Conflict"


def analyze_power_dynamics(power_a: Dict, power_b: Dict) -> str:
    """Describe the power dynamic relationship."""
    orient_a = power_a.get('orientation', 'Unknown')
    orient_b = power_b.get('orientation', 'Unknown')

    if (orient_a == 'Top' and orient_b == 'Bottom') or \
       (orient_a == 'Bottom' and orient_b == 'Top'):
        return f"Complementary ({orient_a}/{orient_b})"
    elif orient_a == orient_b and orient_a in ('Top', 'Bottom'):
        return f"Same-pole conflict ({orient_a}/{orient_b})"
    elif orient_a == orient_b and orient_a == 'Switch':
        return f"Switch/Switch"
    elif 'Versatile' in orient_a or 'Versatile' in orient_b:
        return f"Versatile ({orient_a}/{orient_b})"
    else:
        return f"Mixed ({orient_a}/{orient_b})"


def run_validation():
    """Run validation against all accepted partner connections."""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("COMPATIBILITY ALGORITHM v0.7 - PRODUCTION VALIDATION")
        print(f"Run at: {datetime.now().isoformat()}")
        print("=" * 80)
        print()

        connections = get_accepted_connections()
        print(f"Found {len(connections)} accepted partner connections")
        print()

        results = []
        skipped = 0
        score_distribution = defaultdict(int)
        power_dynamic_stats = defaultdict(list)

        for conn in connections:
            # Get profiles for both partners
            profile_a = get_profile_for_user(conn.requester_user_id)
            profile_b = get_profile_for_user(conn.recipient_user_id)

            if not profile_a or not profile_b:
                skipped += 1
                continue

            # Convert to compatibility format
            compat_a = profile_to_compat_format(profile_a)
            compat_b = profile_to_compat_format(profile_b)

            # Run compatibility calculation
            try:
                result = calculate_compatibility(compat_a, compat_b)
                score = result['overall_compatibility']['score']
                breakdown = result['breakdown']

                power_dynamic = analyze_power_dynamics(
                    compat_a.get('power_dynamic', {}),
                    compat_b.get('power_dynamic', {})
                )

                results.append({
                    'connection_id': conn.id,
                    'score': score,
                    'breakdown': breakdown,
                    'power_dynamic': power_dynamic,
                    'category': classify_score(score),
                })

                # Track distribution
                bucket = (score // 10) * 10
                score_distribution[bucket] += 1
                power_dynamic_stats[power_dynamic].append(score)

            except Exception as e:
                print(f"Error processing connection {conn.id}: {e}")
                skipped += 1

        # Print results
        print("-" * 80)
        print("INDIVIDUAL RESULTS (Anonymized)")
        print("-" * 80)

        for i, r in enumerate(results, 1):
            print(f"Couple #{i}: {r['score']}% ({r['category']}) - {r['power_dynamic']}")
            print(f"  Power: {r['breakdown']['power_complement']}%, "
                  f"Domain: {r['breakdown']['domain_similarity']}%, "
                  f"Activity: {r['breakdown']['activity_overlap']}%, "
                  f"Truth: {r['breakdown']['truth_overlap']}%")
            if 'se_modifier' in r['breakdown']:
                print(f"  SE mod: {r['breakdown']['se_modifier']}%, "
                      f"SIS-C mod: {r['breakdown']['sisc_modifier']}%")
            print()

        # Summary statistics
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print()

        if results:
            scores = [r['score'] for r in results]
            print(f"Couples analyzed: {len(results)}")
            print(f"Couples skipped (missing profiles): {skipped}")
            print()
            print(f"Score range: {min(scores)}% - {max(scores)}%")
            print(f"Mean score: {sum(scores) / len(scores):.1f}%")
            print(f"Median score: {sorted(scores)[len(scores)//2]}%")
            print()

            print("Score distribution:")
            for bucket in sorted(score_distribution.keys()):
                count = score_distribution[bucket]
                bar = "#" * count
                print(f"  {bucket:2d}-{bucket+9:2d}%: {bar} ({count})")
            print()

            print("Scores by power dynamic:")
            for pd, pd_scores in sorted(power_dynamic_stats.items()):
                avg = sum(pd_scores) / len(pd_scores)
                print(f"  {pd}: avg {avg:.1f}% (n={len(pd_scores)})")
            print()

            # Algorithm validation checks
            print("-" * 80)
            print("ALGORITHM VALIDATION CHECKS")
            print("-" * 80)

            # Check 1: Complementary pairs should score higher than same-pole
            complementary_scores = [r['score'] for r in results if 'Complementary' in r['power_dynamic']]
            same_pole_scores = [r['score'] for r in results if 'conflict' in r['power_dynamic']]

            if complementary_scores and same_pole_scores:
                comp_avg = sum(complementary_scores) / len(complementary_scores)
                pole_avg = sum(same_pole_scores) / len(same_pole_scores)
                check = "PASS" if comp_avg > pole_avg else "FAIL"
                print(f"Complementary > Same-pole: {check}")
                print(f"  Complementary avg: {comp_avg:.1f}% (n={len(complementary_scores)})")
                print(f"  Same-pole avg: {pole_avg:.1f}% (n={len(same_pole_scores)})")
            else:
                print("Complementary > Same-pole: N/A (insufficient data)")
            print()

            # Check 2: No scores should be unreasonably low for accepted couples
            low_scores = [r for r in results if r['score'] < 40]
            if low_scores:
                print(f"WARNING: {len(low_scores)} couples scored below 40%")
                for r in low_scores:
                    print(f"  Couple #{results.index(r)+1}: {r['score']}% ({r['power_dynamic']})")
            else:
                print("Low score check: PASS (no couples below 40%)")
            print()

            # Check 3: Score distribution sanity
            high_scores = len([s for s in scores if s >= 75])
            mod_scores = len([s for s in scores if 50 <= s < 75])
            low_scores_count = len([s for s in scores if s < 50])

            print(f"Distribution sanity check:")
            print(f"  High (>=75%): {high_scores} ({100*high_scores/len(scores):.0f}%)")
            print(f"  Moderate (50-74%): {mod_scores} ({100*mod_scores/len(scores):.0f}%)")
            print(f"  Low (<50%): {low_scores_count} ({100*low_scores_count/len(scores):.0f}%)")

            # For real couples who chose each other, we'd expect most to be moderate-high
            if high_scores + mod_scores >= len(scores) * 0.7:
                print("  Result: PASS (70%+ in moderate-high range)")
            else:
                print("  Result: WARNING (less than 70% in moderate-high range)")

        else:
            print("No valid couples to analyze")

        print()
        print("=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)


if __name__ == '__main__':
    run_validation()
