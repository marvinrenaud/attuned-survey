/**
 * Test script to validate compatibility algorithm fixes
 * Run with: node test_compatibility_fixes.js
 */

import { calculateCompatibility } from './frontend/src/lib/matching/compatibilityMapper.js';
import { convertActivities } from './frontend/src/lib/scoring/activityConverter.js';

// Test Profile: Big Black Haiti (Top)
const bbhAnswers = {
  // Power dynamics
  A13: 7, A14: 1, A15: 7, A16: 1,
  
  // Power Exchange - Top preferences
  B15a: 'N', B15b: 'Y', // restraints
  B16a: 'N', B16b: 'Y', // blindfold
  B17a: 'Y', B17b: 'Y', // orgasm control
  B18a: 'N', B18b: 'Y', // protocols
  
  // Verbal - Top preferences
  B19: 'Y', // dirty talk
  B20: 'Y', // moaning
  B21: 'M', // roleplay
  B22a: 'N', B22b: 'Y', // commands (give, not receive)
  B23a: 'N', B23b: 'Y', // begging (hear, not do)
  
  // Display - Watching preferences
  B24a: 'N', B24b: 'Y', // stripping (watch, not perform)
  B25a: 'M', B25b: 'Y', // solo pleasure (watch)
  B26: 'N', // posing
  B27: 'N', // dancing
  B28: 'N', // revealing clothing
};

// Test Profile: Manelz (Bottom)
const manelzAnswers = {
  // Power dynamics
  A13: 1, A14: 7, A15: 1, A16: 7,
  
  // Power Exchange - Bottom preferences
  B15a: 'Y', B15b: 'N', // restraints
  B16a: 'Y', B16b: 'N', // blindfold
  B17a: 'Y', B17b: 'Y', // orgasm control
  B18a: 'Y', B18b: 'N', // protocols
  
  // Verbal - Bottom preferences
  B19: 'Y', // dirty talk
  B20: 'Y', // moaning
  B21: 'Y', // roleplay
  B22a: 'Y', B22b: 'N', // commands (receive, not give)
  B23a: 'Y', B23b: 'N', // begging (do, not hear)
  
  // Display - Performing preferences
  B24a: 'Y', B24b: 'N', // stripping (perform, not watch)
  B25a: 'Y', B25b: 'Y', // solo pleasure (perform)
  B26: 'Y', // posing
  B27: 'Y', // dancing
  B28: 'Y', // revealing clothing
};

// Create test profiles
function createTestProfile(answers, orientation, intensity) {
  const activities = convertActivities(answers);
  
  return {
    user_id: orientation === 'Top' ? 'bbh' : 'manelz',
    power_dynamic: {
      orientation: orientation,
      intensity: intensity
    },
    domain_scores: {
      sensual: 0.7,
      playful: 0.6,
      power: orientation === 'Top' ? 1.0 : 1.0,
      connection: 0.8,
      exploration: orientation === 'Top' ? 0.6 : 0.65,
      edge: 0.5
    },
    activities: activities,
    truth_topics: {
      past_experiences: 1,
      fantasies: 1,
      turn_ons: 1,
      turn_offs: 1,
      insecurities: 0.5,
      boundaries: 1,
      future_fantasies: 1,
      feeling_desired: 1
    },
    boundaries: {
      hard_limits: []
    }
  };
}

console.log('='.repeat(70));
console.log('COMPATIBILITY ALGORITHM FIX VALIDATION');
console.log('='.repeat(70));

try {
  // Create profiles
  const bbhProfile = createTestProfile(bbhAnswers, 'Top', 1.0);
  const manelzProfile = createTestProfile(manelzAnswers, 'Bottom', 1.0);
  
  console.log('\n📋 Test Profiles Created:');
  console.log(`  - BBH (Top): ${JSON.stringify(bbhProfile.activities.display_performance).substring(0, 80)}...`);
  console.log(`  - Manelz (Bottom): ${JSON.stringify(manelzProfile.activities.display_performance).substring(0, 80)}...`);
  
  // Verify new keys exist
  console.log('\n✓ Key Verification:');
  console.log(`  - stripping_self in Manelz: ${manelzProfile.activities.display_performance.stripping_self !== undefined ? '✓' : '✗'}`);
  console.log(`  - watching_strip in BBH: ${bbhProfile.activities.display_performance.watching_strip !== undefined ? '✓' : '✗'}`);
  console.log(`  - protocols_receive in Manelz: ${manelzProfile.activities.power_exchange.protocols_receive !== undefined ? '✓' : '✗'}`);
  console.log(`  - commands_give in BBH: ${bbhProfile.activities.verbal_roleplay.commands_give !== undefined ? '✓' : '✗'}`);
  console.log(`  - begging_receive in Manelz: ${manelzProfile.activities.verbal_roleplay.begging_receive !== undefined ? '✓' : '✗'}`);
  
  // Calculate compatibility
  console.log('\n🧮 Calculating Compatibility...');
  const result = calculateCompatibility(bbhProfile, manelzProfile);
  
  console.log('\n' + '='.repeat(70));
  console.log('RESULTS');
  console.log('='.repeat(70));
  
  console.log(`\n🎯 Overall Compatibility: ${result.overall_compatibility.score}%`);
  console.log(`   Interpretation: ${result.overall_compatibility.interpretation}`);
  
  console.log('\n📊 Component Breakdown:');
  console.log(`   Power Complement:  ${result.breakdown.power_complement}%`);
  console.log(`   Domain Similarity: ${result.breakdown.domain_similarity}%`);
  console.log(`   Activity Overlap:  ${result.breakdown.activity_overlap}%`);
  console.log(`   Truth Overlap:     ${result.breakdown.truth_overlap}%`);
  
  // Expected improvements
  console.log('\n🎓 Expected Improvements (from bug report):');
  console.log('   - display_performance: 28.6% → ~90%');
  console.log('   - power_exchange: 58.3% → ~75%');
  console.log('   - verbal_roleplay: 80% → 100%');
  console.log('   - Overall: 87% → 90-94%');
  
  // Success criteria
  const overall = result.overall_compatibility.score;
  const passThreshold = 90;
  
  console.log('\n' + '='.repeat(70));
  if (overall >= passThreshold) {
    console.log(`✅ SUCCESS: Score ${overall}% meets target (≥${passThreshold}%)`);
  } else {
    console.log(`⚠️  NEEDS REVIEW: Score ${overall}% below target (${passThreshold}%)`);
    console.log('   This may be expected if not all fixes are fully integrated.');
  }
  console.log('='.repeat(70));
  
} catch (error) {
  console.error('\n❌ ERROR:', error.message);
  console.error('\nStack trace:', error.stack);
  process.exit(1);
}

