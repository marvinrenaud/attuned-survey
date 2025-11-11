#!/usr/bin/env python3
"""
Test compatibility calculation for existing users.

This script loads two existing profiles from the database and calculates
their compatibility using the updated algorithm.
"""
import sys
import os
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import Flask app first to initialize everything
from main import app
from models.profile import Profile
from compatibility.calculator import calculate_compatibility


def load_profile_by_user_id(user_id: str) -> dict:
    """Load a profile from the database by user_id."""
    from extensions import db
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None
    
    return {
        'user_id': profile.user_id,
        'power_dynamic': profile.power_dynamic,
        'domain_scores': profile.domain_scores,
        'activities': profile.activities,
        'truth_topics': profile.truth_topics,
        'boundaries': profile.boundaries
    }


def load_profile_by_id(profile_id: int) -> dict:
    """Load a profile from the database by profile_id."""
    from extensions import db
    
    profile = Profile.query.get(profile_id)
    if not profile:
        return None
    
    return {
        'user_id': profile.user_id,
        'power_dynamic': profile.power_dynamic,
        'domain_scores': profile.domain_scores,
        'activities': profile.activities,
        'truth_topics': profile.truth_topics,
        'boundaries': profile.boundaries
    }


def list_available_profiles():
    """List all profiles in the database."""
    from extensions import db
    
    profiles = Profile.query.all()
    
    print("\n" + "="*70)
    print("AVAILABLE PROFILES")
    print("="*70)
    
    if not profiles:
        print("No profiles found in database.")
        return
    
    for profile in profiles:
        orientation = profile.power_dynamic.get('orientation', 'Unknown')
        intensity = profile.power_dynamic.get('intensity', 0)
        print(f"  ID: {profile.profile_id:3d} | User: {profile.user_id:20s} | {orientation:6s} ({intensity:.1f})")
    
    print("="*70 + "\n")


def test_compatibility(profile_a_id, profile_b_id, verbose=True):
    """
    Test compatibility between two profiles.
    
    Args:
        profile_a_id: Either profile_id (int) or user_id (str)
        profile_b_id: Either profile_id (int) or user_id (str)
        verbose: Print detailed output
    """
    # Load profiles
    if isinstance(profile_a_id, int):
        profile_a = load_profile_by_id(profile_a_id)
    else:
        profile_a = load_profile_by_user_id(profile_a_id)
    
    if isinstance(profile_b_id, int):
        profile_b = load_profile_by_id(profile_b_id)
    else:
        profile_b = load_profile_by_user_id(profile_b_id)
    
    if not profile_a:
        print(f"❌ Profile A not found: {profile_a_id}")
        return None
    
    if not profile_b:
        print(f"❌ Profile B not found: {profile_b_id}")
        return None
    
    if verbose:
        print("\n" + "="*70)
        print("COMPATIBILITY TEST")
        print("="*70)
        print(f"\n👤 Profile A: {profile_a['user_id']}")
        print(f"   Power: {profile_a['power_dynamic'].get('orientation')} "
              f"({profile_a['power_dynamic'].get('intensity', 0):.1f})")
        
        print(f"\n👤 Profile B: {profile_b['user_id']}")
        print(f"   Power: {profile_b['power_dynamic'].get('orientation')} "
              f"({profile_b['power_dynamic'].get('intensity', 0):.1f})")
    
    # Calculate compatibility
    result = calculate_compatibility(profile_a, profile_b)
    
    if verbose:
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        print(f"\n🎯 Overall Compatibility: {result['overall_compatibility']['score']}%")
        print(f"   {result['overall_compatibility']['interpretation']}")
        
        print("\n📊 Breakdown:")
        print(f"   Power Complement:  {result['breakdown']['power_complement']}%")
        print(f"   Domain Similarity: {result['breakdown']['domain_similarity']}%")
        print(f"   Activity Overlap:  {result['breakdown']['activity_overlap']}%")
        print(f"   Truth Overlap:     {result['breakdown']['truth_overlap']}%")
        
        if result.get('boundary_conflicts'):
            print(f"\n⚠️  Boundary Conflicts: {len(result['boundary_conflicts'])}")
            for conflict in result['boundary_conflicts']:
                print(f"   - {conflict}")
        
        # Show key activities
        print("\n🎭 Key Activities (Profile A vs Profile B):")
        
        # Display activities
        display_a = profile_a['activities'].get('display_performance', {})
        display_b = profile_b['activities'].get('display_performance', {})
        
        print("   Display/Performance:")
        for key in ['stripping_self', 'watching_strip', 'posing_self', 'dancing_self']:
            val_a = display_a.get(key, 0)
            val_b = display_b.get(key, 0)
            if val_a > 0 or val_b > 0:
                print(f"     {key:25s}: {val_a:.1f} vs {val_b:.1f}")
        
        # Power exchange
        power_a = profile_a['activities'].get('power_exchange', {})
        power_b = profile_b['activities'].get('power_exchange', {})
        
        print("   Power Exchange:")
        for key in ['protocols_receive', 'protocols_give']:
            val_a = power_a.get(key, 0)
            val_b = power_b.get(key, 0)
            if val_a > 0 or val_b > 0:
                print(f"     {key:25s}: {val_a:.1f} vs {val_b:.1f}")
        
        # Verbal
        verbal_a = profile_a['activities'].get('verbal_roleplay', {})
        verbal_b = profile_b['activities'].get('verbal_roleplay', {})
        
        print("   Verbal/Roleplay:")
        for key in ['commands_receive', 'commands_give', 'begging_receive', 'begging_give']:
            val_a = verbal_a.get(key, 0)
            val_b = verbal_b.get(key, 0)
            if val_a > 0 or val_b > 0:
                print(f"     {key:25s}: {val_a:.1f} vs {val_b:.1f}")
        
        print("\n" + "="*70 + "\n")
    
    return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test compatibility for existing users')
    parser.add_argument('--list', action='store_true', help='List all available profiles')
    parser.add_argument('--user-a', type=str, help='User ID for profile A')
    parser.add_argument('--user-b', type=str, help='User ID for profile B')
    parser.add_argument('--id-a', type=int, help='Profile ID for profile A')
    parser.add_argument('--id-b', type=int, help='Profile ID for profile B')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Initialize Flask app context
    with app.app_context():
        if args.list:
            list_available_profiles()
            return
        
        # Determine which profiles to test
        profile_a_id = args.id_a if args.id_a else args.user_a
        profile_b_id = args.id_b if args.id_b else args.user_b
        
        if not profile_a_id or not profile_b_id:
            print("Usage:")
            print("  List profiles:    python test_existing_users_compatibility.py --list")
            print("  Test by user ID:  python test_existing_users_compatibility.py --user-a USER1 --user-b USER2")
            print("  Test by ID:       python test_existing_users_compatibility.py --id-a 1 --id-b 2")
            sys.exit(1)
        
        # Run test
        result = test_compatibility(profile_a_id, profile_b_id, verbose=not args.json)
        
        if args.json and result:
            print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

