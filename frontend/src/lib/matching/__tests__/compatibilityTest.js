/**
 * Compatibility Algorithm Test Runner
 * Tests current implementation and verifies fixes
 */

import { calculateCompatibility } from '../compatibilityMapper.js';
import { profileBBH, profileQuickCheck, profileSwitchA, profileTopA, profileTopB, profileBottomA, profileBottomB } from './testProfiles.js';

/**
 * Run baseline test with current implementation
 */
export function runBaselineTest() {
  console.log('\n═══════════════════════════════════════════════════════');
  console.log('BASELINE TEST: BBH (Top) vs Quick Check (Bottom)');
  console.log('═══════════════════════════════════════════════════════\n');
  
  console.log('Profile 1 (BBH):');
  console.log('  Power:', profileBBH.power_dynamic.orientation, '- Score:', profileBBH.power_dynamic.top_score);
  console.log('  Domains:', profileBBH.domain_scores);
  console.log('');
  
  console.log('Profile 2 (Quick Check):');
  console.log('  Power:', profileQuickCheck.power_dynamic.orientation, '- Score:', profileQuickCheck.power_dynamic.bottom_score);
  console.log('  Domains:', profileQuickCheck.domain_scores);
  console.log('');
  
  try {
    const result = calculateCompatibility(profileBBH, profileQuickCheck);
    
    console.log('CURRENT IMPLEMENTATION RESULTS:');
    console.log('───────────────────────────────────────────────────────');
    console.log('Overall Compatibility:', result.overall_compatibility.score + '%');
    console.log('Interpretation:', result.overall_compatibility.interpretation);
    console.log('');
    console.log('Breakdown:');
    console.log('  Power Complement:    ', result.breakdown.power_complement + '%');
    console.log('  Domain Similarity:   ', result.breakdown.domain_similarity + '%');
    console.log('  Activity Overlap:    ', result.breakdown.activity_overlap + '%');
    console.log('  Truth Overlap:       ', result.breakdown.truth_overlap + '%');
    console.log('  Boundary Conflicts:  ', result.breakdown.boundary_conflicts.length);
    console.log('');
    console.log('Expected: ~90% total (Power=100%, Domain=~94%, Activity=~79%, Truth=100%)');
    console.log('');
    
    if (result.overall_compatibility.score < 70) {
      console.log('⚠️  BUG CONFIRMED: Score is', result.overall_compatibility.score + '%', 'when it should be ~90%');
    } else if (result.overall_compatibility.score >= 85) {
      console.log('✅ PASS: Score is in expected range');
    } else {
      console.log('⚠️  PARTIAL: Score is', result.overall_compatibility.score + '%', '(better than 60%, but should be ~90%)');
    }
    
    return result;
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    console.error(error.stack);
    return null;
  }
}

/**
 * Run comprehensive tests after fixes are applied
 */
export function runComprehensiveTests() {
  console.log('\n═══════════════════════════════════════════════════════');
  console.log('COMPREHENSIVE COMPATIBILITY TESTS');
  console.log('═══════════════════════════════════════════════════════\n');
  
  const tests = [
    {
      name: 'Test 1: Perfect Top/Bottom (BBH vs Quick Check)',
      profileA: profileBBH,
      profileB: profileQuickCheck,
      expectedMin: 85,
      expectedMax: 95,
      expectedBreakdown: {
        power: 100,
        domain: 90,
        activity: 75,
        truth: 100
      }
    },
    {
      name: 'Test 2: Top/Top (Incompatible)',
      profileA: profileTopA,
      profileB: profileTopB,
      expectedMin: 35,
      expectedMax: 45,
      expectedBreakdown: {
        power: 40,
        domain: 80,
        activity: 60,
        truth: 85
      }
    },
    {
      name: 'Test 3: Bottom/Bottom (Incompatible)',
      profileA: profileBottomA,
      profileB: profileBottomB,
      expectedMin: 35,
      expectedMax: 45,
      expectedBreakdown: {
        power: 40,
        domain: 80,
        activity: 60,
        truth: 85
      }
    },
    {
      name: 'Test 4: Switch/Switch',
      profileA: profileSwitchA,
      profileB: profileSwitchA, // Same profile for simplicity
      expectedMin: 85,
      expectedMax: 95,
      expectedBreakdown: {
        power: 90,
        domain: 100,
        activity: 100,
        truth: 100
      }
    }
  ];
  
  let passCount = 0;
  let failCount = 0;
  
  tests.forEach(test => {
    console.log('\n' + test.name);
    console.log('─'.repeat(60));
    
    try {
      const result = calculateCompatibility(test.profileA, test.profileB);
      const score = result.overall_compatibility.score;
      
      console.log('Score:', score + '%', 
        `(expected: ${test.expectedMin}-${test.expectedMax}%)`);
      console.log('Breakdown:');
      console.log('  Power:    ', result.breakdown.power_complement + '%',
        `(~${test.expectedBreakdown.power}%)`);
      console.log('  Domain:   ', result.breakdown.domain_similarity + '%',
        `(~${test.expectedBreakdown.domain}%)`);
      console.log('  Activity: ', result.breakdown.activity_overlap + '%',
        `(~${test.expectedBreakdown.activity}%)`);
      console.log('  Truth:    ', result.breakdown.truth_overlap + '%',
        `(~${test.expectedBreakdown.truth}%)`);
      
      const passed = score >= test.expectedMin && score <= test.expectedMax;
      if (passed) {
        console.log('✅ PASS');
        passCount++;
      } else {
        console.log('❌ FAIL: Score outside expected range');
        failCount++;
      }
    } catch (error) {
      console.error('❌ ERROR:', error.message);
      failCount++;
    }
  });
  
  console.log('\n═══════════════════════════════════════════════════════');
  console.log('TEST SUMMARY');
  console.log('═══════════════════════════════════════════════════════');
  console.log('Passed:', passCount + '/' + tests.length);
  console.log('Failed:', failCount + '/' + tests.length);
  console.log('');
  
  return { passCount, failCount, total: tests.length };
}

/**
 * Run tests in browser console
 * Usage: import and call runTests() in your console
 */
export function runTests() {
  console.log('Starting compatibility algorithm tests...\n');
  
  // First, run baseline test
  const baseline = runBaselineTest();
  
  // Then run comprehensive tests
  const comprehensive = runComprehensiveTests();
  
  return {
    baseline,
    comprehensive
  };
}

// For direct browser console testing
if (typeof window !== 'undefined') {
  window.runCompatibilityTests = runTests;
  window.runBaselineTest = runBaselineTest;
  window.runComprehensiveTests = runComprehensiveTests;
  console.log('✅ Compatibility tests loaded. Run: window.runCompatibilityTests()');
}

