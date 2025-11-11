#!/usr/bin/env python3
"""
Update specific profiles to use new activity key naming.

This script:
1. Takes answers for new B22a/b and B23a/b questions
2. Converts old activity keys to new naming convention
3. Updates profiles in database
4. Recalculates compatibility
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.main import app
from src.models.profile import Profile
from src.compatibility.calculator import calculate_compatibility


def convert_ymn(answer):
    """Convert Y/M/N to numeric value."""
    answer = answer.upper().strip()
    if answer == 'Y':
        return 1.0
    elif answer == 'M':
        return 0.5
    else:
        return 0.0


def update_profile_activities(profile_model, new_answers):
    """
    Update a profile's activities with new question answers and key naming.
    
    Args:
        profile_model: Profile model from database
        new_answers: Dict with B22a, B22b, B23a, B23b answers (Y/M/N)
    
    Returns:
        Updated activities dict
    """
    activities = profile_model.activities.copy()
    
    # Update verbal_roleplay with new split questions
    if 'verbal_roleplay' in activities:
        verbal = activities['verbal_roleplay'].copy()
        
        # Remove old keys
        if 'commands' in verbal:
            del verbal['commands']
        if 'begging' in verbal:
            del verbal['begging']
        
        # Add new split keys
        verbal['commands_receive'] = convert_ymn(new_answers.get('B22a', 'N'))
        verbal['commands_give'] = convert_ymn(new_answers.get('B22b', 'N'))
        verbal['begging_receive'] = convert_ymn(new_answers.get('B23a', 'N'))
        verbal['begging_give'] = convert_ymn(new_answers.get('B23b', 'N'))
        
        activities['verbal_roleplay'] = verbal
    
    # Update power_exchange: protocols_follow → protocols_receive
    if 'power_exchange' in activities:
        power = activities['power_exchange'].copy()
        
        if 'protocols_follow' in power:
            power['protocols_receive'] = power.pop('protocols_follow')
        
        activities['power_exchange'] = power
    
    # Update display_performance: rename to _self pattern
    if 'display_performance' in activities:
        display = activities['display_performance'].copy()
        
        # Rename keys
        if 'stripping_me' in display:
            display['stripping_self'] = display.pop('stripping_me')
        if 'watched_solo_pleasure' in display:
            display['solo_pleasure_self'] = display.pop('watched_solo_pleasure')
        if 'posing' in display:
            display['posing_self'] = display.pop('posing')
            display['posing_watching'] = 0  # Add watching counterpart
        if 'dancing' in display:
            display['dancing_self'] = display.pop('dancing')
            display['dancing_watching'] = 0  # Add watching counterpart
        if 'revealing_clothing' in display:
            display['revealing_clothing_self'] = display.pop('revealing_clothing')
            display['revealing_clothing_watching'] = 0  # Add watching counterpart
        
        activities['display_performance'] = display
    
    return activities


def main():
    # Profile IDs
    profile_a_submission = '1760537681785-vio2041ue'
    profile_b_submission = '1761013748932-gfggxk2lk'
    
    print("\n" + "="*70)
    print("PROFILE UPDATE SCRIPT")
    print("="*70)
    
    # Get answers from command line or interactive
    if len(sys.argv) == 9:
        # Command line: B22a B22b B23a B23b for A, then same for B
        answers_a = {
            'B22a': sys.argv[1],
            'B22b': sys.argv[2],
            'B23a': sys.argv[3],
            'B23b': sys.argv[4]
        }
        answers_b = {
            'B22a': sys.argv[5],
            'B22b': sys.argv[6],
            'B23a': sys.argv[7],
            'B23b': sys.argv[8]
        }
    else:
        # Interactive
        print("\nEnter answers (Y/M/N) for Profile A (Top):")
        answers_a = {
            'B22a': input("  B22a (receive commands): "),
            'B22b': input("  B22b (give commands): "),
            'B23a': input("  B23a (do begging): "),
            'B23b': input("  B23b (hear begging): ")
        }
        
        print("\nEnter answers (Y/M/N) for Profile B (Bottom):")
        answers_b = {
            'B22a': input("  B22a (receive commands): "),
            'B22b': input("  B22b (give commands): "),
            'B23a': input("  B23a (do begging): "),
            'B23b': input("  B23b (hear begging): ")
        }
    
    with app.app_context():
        # Load profiles
        profile_a = Profile.query.filter_by(submission_id=profile_a_submission).first()
        profile_b = Profile.query.filter_by(submission_id=profile_b_submission).first()
        
        if not profile_a or not profile_b:
            print("❌ One or both profiles not found!")
            sys.exit(1)
        
        print("\n" + "="*70)
        print("UPDATING PROFILES")
        print("="*70)
        
        # Show before
        print(f"\n📋 Profile A BEFORE:")
        print(f"   commands: {profile_a.activities.get('verbal_roleplay', {}).get('commands', 'N/A')}")
        print(f"   begging: {profile_a.activities.get('verbal_roleplay', {}).get('begging', 'N/A')}")
        
        # Update Profile A
        print(f"\n✏️  Updating Profile A with:")
        for key, val in answers_a.items():
            print(f"   {key}: {val}")
        profile_a.activities = update_profile_activities(profile_a, answers_a)
        
        print(f"\n📋 Profile A AFTER:")
        verbal_a = profile_a.activities.get('verbal_roleplay', {})
        print(f"   commands_receive: {verbal_a.get('commands_receive', 'N/A')}")
        print(f"   commands_give: {verbal_a.get('commands_give', 'N/A')}")
        print(f"   begging_receive: {verbal_a.get('begging_receive', 'N/A')}")
        print(f"   begging_give: {verbal_a.get('begging_give', 'N/A')}")
        
        # Show before
        print(f"\n📋 Profile B BEFORE:")
        print(f"   commands: {profile_b.activities.get('verbal_roleplay', {}).get('commands', 'N/A')}")
        print(f"   begging: {profile_b.activities.get('verbal_roleplay', {}).get('begging', 'N/A')}")
        
        # Update Profile B
        print(f"\n✏️  Updating Profile B with:")
        for key, val in answers_b.items():
            print(f"   {key}: {val}")
        profile_b.activities = update_profile_activities(profile_b, answers_b)
        
        print(f"\n📋 Profile B AFTER:")
        verbal_b = profile_b.activities.get('verbal_roleplay', {})
        print(f"   commands_receive: {verbal_b.get('commands_receive', 'N/A')}")
        print(f"   commands_give: {verbal_b.get('commands_give', 'N/A')}")
        print(f"   begging_receive: {verbal_b.get('begging_receive', 'N/A')}")
        print(f"   begging_give: {verbal_b.get('begging_give', 'N/A')}")
        
        # Commit changes
        from src.extensions import db
        db.session.commit()
        
        print("\n✅ Profiles updated successfully!")
        
        # Now recalculate compatibility
        print("\n" + "="*70)
        print("RECALCULATING COMPATIBILITY")
        print("="*70)
        
        # Convert for calculator
        def flatten_activities(activities_dict):
            flat = {}
            for category, activities in activities_dict.items():
                if isinstance(activities, dict):
                    for key, value in activities.items():
                        flat[key] = value
            return flat
        
        def convert_domains(domain_dict):
            return {k: v/100.0 for k, v in domain_dict.items()}
        
        def calc_intensity(power_dynamic):
            top = power_dynamic.get('top_score', 0) / 100.0
            bottom = power_dynamic.get('bottom_score', 0) / 100.0
            return max(top, bottom)
        
        profile_a_calc = {
            'user_id': profile_a.submission_id,
            'power_dynamic': {
                'orientation': profile_a.power_dynamic['orientation'],
                'intensity': calc_intensity(profile_a.power_dynamic)
            },
            'domain_scores': convert_domains(profile_a.domain_scores),
            'activities': flatten_activities(profile_a.activities),
            'truth_topics': profile_a.truth_topics,
            'boundaries': profile_a.boundaries
        }
        
        profile_b_calc = {
            'user_id': profile_b.submission_id,
            'power_dynamic': {
                'orientation': profile_b.power_dynamic['orientation'],
                'intensity': calc_intensity(profile_b.power_dynamic)
            },
            'domain_scores': convert_domains(profile_b.domain_scores),
            'activities': flatten_activities(profile_b.activities),
            'truth_topics': profile_b.truth_topics,
            'boundaries': profile_b.boundaries
        }
        
        result = calculate_compatibility(profile_a_calc, profile_b_calc)
        
        print(f"\n🎯 NEW Overall Compatibility: {result['overall_compatibility']['score']}%")
        print(f"   {result['overall_compatibility']['interpretation']}")
        
        print(f"\n📊 Component Breakdown:")
        print(f"   Power Complement:  {result['breakdown']['power_complement']}%")
        print(f"   Domain Similarity: {result['breakdown']['domain_similarity']}%")
        print(f"   Activity Overlap:  {result['breakdown']['activity_overlap']}% ⬆️")
        print(f"   Truth Overlap:     {result['breakdown']['truth_overlap']}%")
        
        print("\n" + "="*70)
        print("COMPARISON")
        print("="*70)
        print("BEFORE updates:")
        print("  - Activity Overlap: 29%")
        print("  - Overall Score: 64%")
        print(f"\nAFTER updates:")
        print(f"  - Activity Overlap: {result['breakdown']['activity_overlap']}%")
        print(f"  - Overall Score: {result['overall_compatibility']['score']}%")
        print(f"\nImprovement: +{result['breakdown']['activity_overlap'] - 29} points in activity overlap")
        print(f"             +{result['overall_compatibility']['score'] - 64} points overall")
        print("="*70)


if __name__ == '__main__':
    main()

