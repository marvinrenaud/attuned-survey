import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { calculateCompatibilityDetailed } from '../lib/matching/compatibilityMapper';
import { profileBBH, profileQuickCheck, profileSwitchA, profileTopA, profileTopB, profileBottomA, profileBottomB } from '../lib/matching/__tests__/testProfiles';

export default function TestCompatibility() {
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [testType, setTestType] = useState(null);

  const runBBHTest = () => {
    console.clear();
    console.log('\n═══════════════════════════════════════════════════════');
    console.log('BASELINE TEST: BBH (Top) vs Quick Check (Bottom)');
    console.log('═══════════════════════════════════════════════════════\n');
    
    console.log('Profile 1 (BBH):');
    console.log('  Power:', profileBBH.power_dynamic.orientation, '- Top Score:', profileBBH.power_dynamic.top_score);
    console.log('  Domains:', profileBBH.domain_scores);
    console.log('');
    
    console.log('Profile 2 (Quick Check):');
    console.log('  Power:', profileQuickCheck.power_dynamic.orientation, '- Bottom Score:', profileQuickCheck.power_dynamic.bottom_score);
    console.log('  Domains:', profileQuickCheck.domain_scores);
    console.log('');
    
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
    
    console.log('\nRESULTS:');
    console.log('───────────────────────────────────────────────────────');
    console.log('Overall Compatibility:', result.overall_compatibility.score + '%');
    console.log('Interpretation:', result.overall_compatibility.interpretation);
    console.log('');
    console.log('Breakdown:');
    console.log('  Power Complement:    ', result.breakdown.power_complement + '%');
    console.log('  Domain Similarity:   ', result.breakdown.domain_similarity + '%');
    console.log('  Activity Overlap:    ', result.breakdown.activity_overlap + '%');
    console.log('  Truth Overlap:       ', result.breakdown.truth_overlap + '%');
    console.log('');
    console.log('Expected vs Actual:');
    console.log('  Overall:   Expected ~90%,  Actual', result.overall_compatibility.score + '%');
    console.log('  Power:     Expected 100%,  Actual', result.breakdown.power_complement + '%');
    console.log('  Domain:    Expected ~94%,  Actual', result.breakdown.domain_similarity + '%');
    console.log('  Activity:  Expected ~79%,  Actual', result.breakdown.activity_overlap + '%');
    console.log('  Truth:     Expected 100%,  Actual', result.breakdown.truth_overlap + '%');
    console.log('');
    
    const passed = result.overall_compatibility.score >= 85 && result.overall_compatibility.score <= 95;
    if (passed) {
      console.log('✅ PASS: Score is in expected range (85-95%)');
    } else {
      console.log('⚠️  Issue: Score is', result.overall_compatibility.score + '%, expected ~90%');
    }
    
    setResults(result);
    setTestType('BBH vs Quick Check');
  };

  const runEdgeCaseTests = () => {
    console.clear();
    console.log('\n═══════════════════════════════════════════════════════');
    console.log('EDGE CASE TESTS');
    console.log('═══════════════════════════════════════════════════════\n');
    
    const tests = [
      {
        name: 'Top/Top (Should be low 35-45%)',
        profileA: profileTopA,
        profileB: profileTopB,
        expectedMin: 35,
        expectedMax: 45
      },
      {
        name: 'Bottom/Bottom (Should be low 35-45%)',
        profileA: profileBottomA,
        profileB: profileBottomB,
        expectedMin: 35,
        expectedMax: 45
      },
      {
        name: 'Switch/Switch (Should be high 85-95%)',
        profileA: profileSwitchA,
        profileB: profileSwitchA,
        expectedMin: 85,
        expectedMax: 100
      }
    ];
    
    const results = [];
    
    tests.forEach(test => {
      console.log('\n' + test.name);
      console.log('─'.repeat(60));
      
      const result = calculateCompatibilityDetailed(
        test.profileA.power_dynamic,
        test.profileB.power_dynamic,
        test.profileA.domain_scores,
        test.profileB.domain_scores,
        test.profileA.activities,
        test.profileB.activities,
        test.profileA.truth_topics,
        test.profileB.truth_topics,
        test.profileA.boundaries,
        test.profileB.boundaries
      );
      
      const score = result.overall_compatibility.score;
      const passed = score >= test.expectedMin && score <= test.expectedMax;
      
      console.log('Score:', score + '%', `(expected: ${test.expectedMin}-${test.expectedMax}%)`);
      console.log('Breakdown:', result.breakdown);
      console.log(passed ? '✅ PASS' : '❌ FAIL');
      
      results.push({ ...test, result, passed });
    });
    
    const passCount = results.filter(r => r.passed).length;
    console.log('\n═══════════════════════════════════════════════════════');
    console.log('SUMMARY:', passCount + '/' + tests.length, 'tests passed');
    console.log('═══════════════════════════════════════════════════════\n');
    
    setResults(results);
    setTestType('Edge Cases');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-pink-50">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Compatibility Algorithm Test Suite
          </h1>
          <p className="text-gray-600">Testing asymmetric Top/Bottom matching fixes</p>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Instructions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Open Browser DevTools Console (F12 or Cmd+Option+I)</li>
              <li>Click one of the test buttons below</li>
              <li>Review console output for detailed calculation breakdown</li>
              <li>Expected: ~90% overall compatibility for BBH vs Quick Check</li>
            </ol>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Test Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4 flex-wrap">
              <Button onClick={runBBHTest} className="bg-rose-600 hover:bg-rose-700">
                Run BBH vs Quick Check Test
              </Button>
              <Button onClick={runEdgeCaseTests} variant="outline">
                Run Edge Case Tests
              </Button>
              <Button onClick={() => { setResults(null); setTestType(null); }} variant="outline">
                Clear Results
              </Button>
            </div>
            <p className="text-sm text-gray-600">
              All test output is logged to the browser console. Check DevTools for details.
            </p>
          </CardContent>
        </Card>

        {results && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Test Results: {testType}</CardTitle>
            </CardHeader>
            <CardContent>
              {testType === 'BBH vs Quick Check' ? (
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-5xl font-bold text-rose-600 mb-2">
                      {results.overall_compatibility.score}%
                    </div>
                    <p className="text-gray-600">{results.overall_compatibility.interpretation}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Power Complement</div>
                      <div className="text-2xl font-bold">{results.breakdown.power_complement}%</div>
                      <div className="text-xs text-gray-500">Expected: 100%</div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Domain Similarity</div>
                      <div className="text-2xl font-bold">{results.breakdown.domain_similarity}%</div>
                      <div className="text-xs text-gray-500">Expected: ~94%</div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Activity Overlap</div>
                      <div className="text-2xl font-bold">{results.breakdown.activity_overlap}%</div>
                      <div className="text-xs text-gray-500">Expected: ~79%</div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Truth Overlap</div>
                      <div className="text-2xl font-bold">{results.breakdown.truth_overlap}%</div>
                      <div className="text-xs text-gray-500">Expected: 100%</div>
                    </div>
                  </div>

                  <div className="mt-4 p-4 bg-blue-50 rounded">
                    <div className="font-semibold mb-2">
                      {results.overall_compatibility.score >= 85 && results.overall_compatibility.score <= 95 
                        ? '✅ TEST PASSED' 
                        : '⚠️ TEST RESULT OUT OF EXPECTED RANGE'}
                    </div>
                    <div className="text-sm text-gray-700">
                      {results.overall_compatibility.score >= 85 && results.overall_compatibility.score <= 95
                        ? 'Score is in expected range (85-95%). Algorithm is working correctly!'
                        : `Score is ${results.overall_compatibility.score}%, expected ~90%. Check console for details.`}
                    </div>
                  </div>

                  <p className="text-sm text-gray-600 mt-4">
                    ℹ️ See browser console for complete calculation breakdown and debug output.
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 mb-4">Edge case test results:</p>
                  <div className="space-y-2">
                    {results.map((test, idx) => (
                      <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <span className="text-sm">{test.name}</span>
                        <div className="flex items-center gap-3">
                          <span className="font-semibold">{test.result.overall_compatibility.score}%</span>
                          <span className={test.passed ? 'text-green-600' : 'text-red-600'}>
                            {test.passed ? '✅' : '❌'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600 mt-4">
                    ℹ️ See browser console for detailed breakdown of each test.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="flex justify-center">
          <Button onClick={() => navigate('/')} variant="outline">
            <Home className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </div>

      <footer className="text-center py-8 text-sm text-gray-500">
        <p>Made with ♥️ in BK</p>
      </footer>
    </div>
  );
}

