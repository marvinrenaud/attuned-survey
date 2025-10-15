/**
 * Standalone Test Runner for Compatibility Algorithm
 * Run this with: node runTest.js
 */

import { calculateCompatibilityDetailed } from '../compatibilityMapper.js';
import { calculatePowerComplement } from '../../scoring/powerCalculator.js';
import { calculateTruthOverlap } from '../../scoring/truthTopicsCalculator.js';
import { profileBBH, profileQuickCheck } from './testProfiles.js';

console.log('\n' + '═'.repeat(70));
console.log('COMPATIBILITY ALGORITHM TEST');
console.log('Testing: BBH (Top) vs Quick Check (Bottom)');
console.log('═'.repeat(70) + '\n');

console.log('Profile 1 (BBH - Top):');
console.log('  Power:', profileBBH.power_dynamic.orientation, 
  `(Top: ${profileBBH.power_dynamic.top_score}, Bottom: ${profileBBH.power_dynamic.bottom_score})`);
console.log('  Confidence:', profileBBH.power_dynamic.confidence);
console.log('  Domains:', JSON.stringify(profileBBH.domain_scores));
console.log('');

console.log('Profile 2 (Quick Check - Bottom):');
console.log('  Power:', profileQuickCheck.power_dynamic.orientation,
  `(Top: ${profileQuickCheck.power_dynamic.top_score}, Bottom: ${profileQuickCheck.power_dynamic.bottom_score})`);
console.log('  Confidence:', profileQuickCheck.power_dynamic.confidence);
console.log('  Domains:', JSON.stringify(profileQuickCheck.domain_scores));
console.log('');

console.log('─'.repeat(70));
console.log('CALCULATING COMPATIBILITY...');
console.log('─'.repeat(70) + '\n');

try {
  const result = calculateCompatibilityDetailed(
    profileBBH.power_dynamic,
    profileQuickCheck.power_dynamic,
    profileBBH.domain_scores,
    profileQuickCheck.domain_scores,
    profileBBH.activities,
    profileQuickCheck.activities,
    profileBBH.truth_topics,
    profileQuickCheck.truth_topics,
    profileBBH.boundaries,
    profileQuickCheck.boundaries
  );

  console.log('\n' + '═'.repeat(70));
  console.log('RESULTS');
  console.log('═'.repeat(70));
  console.log('');
  console.log('Overall Compatibility:', result.overall_compatibility.score + '%');
  console.log('Interpretation:', result.overall_compatibility.interpretation);
  console.log('');
  console.log('Breakdown:');
  console.log('  Power Complement:     ', result.breakdown.power_complement + '%');
  console.log('  Domain Similarity:    ', result.breakdown.domain_similarity + '%');
  console.log('  Activity Overlap:     ', result.breakdown.activity_overlap + '%');
  console.log('  Truth Overlap:        ', result.breakdown.truth_overlap + '%');
  console.log('  Boundary Conflicts:   ', result.breakdown.boundary_conflicts.length);
  console.log('');
  console.log('─'.repeat(70));
  console.log('EXPECTED vs ACTUAL');
  console.log('─'.repeat(70));
  console.log('Overall:         Expected ~90%,      Actual', result.overall_compatibility.score + '%');
  console.log('Power:           Expected 100%,      Actual', result.breakdown.power_complement + '%');
  console.log('Domain:          Expected ~94%,      Actual', result.breakdown.domain_similarity + '%');
  console.log('Activity:        Expected ~79%,      Actual', result.breakdown.activity_overlap + '%');
  console.log('Truth:           Expected 100%,      Actual', result.breakdown.truth_overlap + '%');
  console.log('');

  // Validation
  const overallMatch = result.overall_compatibility.score >= 85 && result.overall_compatibility.score <= 95;
  const powerMatch = result.breakdown.power_complement === 100;
  const domainMatch = result.breakdown.domain_similarity >= 90 && result.breakdown.domain_similarity <= 98;
  const activityMatch = result.breakdown.activity_overlap >= 75 && result.breakdown.activity_overlap <= 85;
  const truthMatch = result.breakdown.truth_overlap === 100;

  console.log('VALIDATION:');
  console.log('  Overall Score (85-95%):  ', overallMatch ? '✅ PASS' : '❌ FAIL');
  console.log('  Power (100%):            ', powerMatch ? '✅ PASS' : '❌ FAIL');
  console.log('  Domain (90-98%):         ', domainMatch ? '✅ PASS' : '❌ FAIL');
  console.log('  Activity (75-85%):       ', activityMatch ? '✅ PASS' : '❌ FAIL');
  console.log('  Truth (100%):            ', truthMatch ? '✅ PASS' : '❌ FAIL');
  console.log('');

  if (overallMatch && powerMatch && domainMatch && activityMatch && truthMatch) {
    console.log('🎉 ALL TESTS PASSED! Compatibility algorithm is working correctly.');
  } else {
    console.log('⚠️  SOME TESTS FAILED. Review the results above.');
  }

  console.log('\n' + '═'.repeat(70) + '\n');

} catch (error) {
  console.error('\n❌ ERROR during compatibility calculation:');
  console.error(error);
  console.error('\nStack trace:');
  console.error(error.stack);
  process.exit(1);
}

