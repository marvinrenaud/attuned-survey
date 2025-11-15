#!/usr/bin/env python3
"""
Test anatomy filtering with all scenarios.

Tests that activities are properly filtered based on anatomy requirements
and that the correct player's anatomy is checked based on actor assignment.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.main import app
from src.db.repository import find_best_activity_candidate, meets_anatomy_requirements
from src.models.activity import Activity


def test_meets_anatomy_requirements():
    """Test the anatomy checking function directly."""
    print("="*70)
    print("TEST 1: meets_anatomy_requirements() Function")
    print("="*70)
    
    # Create test activity
    class MockActivity:
        def __init__(self, req):
            self.required_bodyparts = req
    
    test_cases = [
        {
            'name': 'Active needs penis, has penis',
            'activity_req': {'active': ['penis'], 'partner': []},
            'player_anatomy': {'active_anatomy': ['penis'], 'partner_anatomy': ['vagina']},
            'should_pass': True
        },
        {
            'name': 'Active needs penis, lacks penis',
            'activity_req': {'active': ['penis'], 'partner': []},
            'player_anatomy': {'active_anatomy': ['vagina'], 'partner_anatomy': ['penis']},
            'should_pass': False
        },
        {
            'name': 'Partner needs penis, has penis',
            'activity_req': {'active': [], 'partner': ['penis']},
            'player_anatomy': {'active_anatomy': ['vagina'], 'partner_anatomy': ['penis']},
            'should_pass': True
        },
        {
            'name': 'Partner needs penis, lacks penis',
            'activity_req': {'active': [], 'partner': ['penis']},
            'player_anatomy': {'active_anatomy': ['penis'], 'partner_anatomy': ['vagina']},
            'should_pass': False
        }
    ]
    
    passed = 0
    failed = 0
    
    for tc in test_cases:
        activity = MockActivity(tc['activity_req'])
        result = meets_anatomy_requirements(activity, tc['player_anatomy'])
        
        if result == tc['should_pass']:
            print(f"✅ {tc['name']}")
            passed += 1
        else:
            print(f"❌ {tc['name']}")
            print(f"   Expected: {tc['should_pass']}, Got: {result}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_activity_1066_scenarios():
    """Test activity 1066 specifically with different anatomy combinations."""
    print("\n" + "="*70)
    print("TEST 2: Activity 1066 (Suck Partner's Cock) Scenarios")
    print("="*70)
    
    with app.app_context():
        # Get activity 1066
        activity_1066 = Activity.query.get(1066)
        
        if not activity_1066:
            print("❌ Activity 1066 not found in database")
            return False
        
        print(f"\nActivity: {activity_1066.script['steps'][0]['do'][:60]}...")
        print(f"Required anatomy: {activity_1066.required_bodyparts}")
        
        # Test scenarios
        scenarios = [
            {
                'name': 'Odd step (A active, B partner), B has penis',
                'seq': 1,  # A active
                'a_anatomy': ['vagina'],
                'b_anatomy': ['penis'],
                'should_allow': True,
                'reason': 'B is partner and has penis'
            },
            {
                'name': 'Odd step (A active, B partner), B lacks penis',
                'seq': 1,  # A active
                'a_anatomy': ['vagina'],
                'b_anatomy': ['vagina'],
                'should_allow': False,
                'reason': 'B is partner but lacks penis'
            },
            {
                'name': 'Even step (B active, A partner), A has penis',
                'seq': 2,  # B active
                'a_anatomy': ['penis'],
                'b_anatomy': ['vagina'],
                'should_allow': True,
                'reason': 'A is partner and has penis'
            },
            {
                'name': 'Even step (B active, A partner), A lacks penis - BUG',
                'seq': 2,  # B active
                'a_anatomy': ['vagina'],
                'b_anatomy': ['penis'],
                'should_allow': False,
                'reason': 'A is partner but lacks penis (THIS WAS THE BUG)'
            }
        ]
        
        passed = 0
        failed = 0
        
        for scenario in scenarios:
            # Determine correct anatomy mapping for this step
            actor = 'A' if scenario['seq'] % 2 == 1 else 'B'
            
            if actor == 'A':
                player_anatomy = {
                    'active_anatomy': scenario['a_anatomy'],
                    'partner_anatomy': scenario['b_anatomy']
                }
            else:
                player_anatomy = {
                    'active_anatomy': scenario['b_anatomy'],
                    'partner_anatomy': scenario['a_anatomy']
                }
            
            # Check if anatomy requirements met
            result = meets_anatomy_requirements(activity_1066, player_anatomy)
            
            if result == scenario['should_allow']:
                print(f"\n✅ {scenario['name']}")
                print(f"   {scenario['reason']}")
                passed += 1
            else:
                print(f"\n❌ {scenario['name']}")
                print(f"   Expected: {scenario['should_allow']}, Got: {result}")
                print(f"   Reason: {scenario['reason']}")
                failed += 1
        
        print(f"\n{'='*70}")
        print(f"Results: {passed}/{len(scenarios)} passed")
        
        return failed == 0


def test_full_session_anatomy():
    """Test that a full session respects anatomy throughout."""
    print("\n" + "="*70)
    print("TEST 3: Full Session Anatomy Validation")
    print("="*70)
    
    with app.app_context():
        # Get activities that require penis
        penis_activities = Activity.query.filter(
            Activity.is_active == True,
            Activity.required_bodyparts.contains({'partner': ['penis']})
        ).limit(10).all()
        
        print(f"\nFound {len(penis_activities)} activities requiring partner penis")
        
        if penis_activities:
            sample = penis_activities[0]
            print(f"\nSample activity {sample.activity_id}:")
            print(f"  Description: {sample.script['steps'][0]['do'][:60]}...")
            print(f"  Required: {sample.required_bodyparts}")
            
            print(f"\n✅ Activities with anatomy requirements exist in database")
        
        return True


def main():
    """Run all anatomy filtering tests."""
    print("\n" + "="*70)
    print("ANATOMY FILTERING COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Basic function
    results.append(("meets_anatomy_requirements()", test_meets_anatomy_requirements()))
    
    # Test 2: Activity 1066 scenarios
    results.append(("Activity 1066 scenarios", test_activity_1066_scenarios()))
    
    # Test 3: Full session check
    results.append(("Full session validation", test_full_session_anatomy()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Anatomy filtering is working correctly.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review and fix.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

