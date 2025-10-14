import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Edit, Home, Heart, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getSubmission, getBaseline } from '../lib/storage/apiStore';
import { computeOverallMatch } from '../lib/matching/overlapHelper';
import { EXCLUDED_FROM_MEAN } from '@/lib/matching/overlapHelper';
import { CATEGORY_MAP } from '@/lib/matching/categoryMap';
import { computeDomainsFromTraits } from '@/lib/scoring/domainCalculator';
import { extractBoundaries } from '../lib/scoring/traitCalculator';

const DEBUG_RESULTS = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('debug') === '1';
function dbg(...args) {
  if (DEBUG_RESULTS) console.log('[RESULT DEBUG]', ...args);
}

export default function Result() {
  const location = useLocation();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [baselineMatch, setBaselineMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        const submissionId = location.state?.submissionId;
        
        if (!submissionId) {
          console.error('No submission ID in location state');
          setError('No submission ID provided');
          setTimeout(() => navigate('/'), 2000);
          return;
        }

        console.log(`Loading submission: ${submissionId} (attempt ${retryCount + 1})`);
        
        // Retry logic: try up to 3 times with delays
        let sub = null;
        const maxRetries = 3;
        
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
          if (attempt > 0) {
            console.log(`Retry attempt ${attempt}/${maxRetries}...`);
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); // Exponential backoff
          }
          
          sub = await getSubmission(submissionId);
          
          if (sub) {
            console.log('✅ Submission loaded successfully');
            break;
          } else {
            console.warn(`Attempt ${attempt + 1}: Submission not found`);
          }
        }
        
        if (!sub) {
          console.error(`Failed to load submission after ${maxRetries + 1} attempts`);
          setError(`Could not load your results. The submission may not have been saved properly.`);
          setLoading(false);
          return;
        }

        setSubmission(sub);

        // Calculate baseline match if baseline is set
        const baselineId = await getBaseline();
        if (baselineId && baselineId !== submissionId) {
          console.log(`Loading baseline: ${baselineId}`);
          const baseline = await getSubmission(baselineId);
          if (baseline) {
            console.log('✅ Baseline loaded, calculating match...');
            try {
              const boundariesA = extractBoundaries(sub.answers || {});
              const boundariesB = extractBoundaries(baseline.answers || {});
              const domainsA = computeDomainsFromTraits(sub?.derived?.traits || {});
              const domainsB = computeDomainsFromTraits(baseline?.derived?.traits || {});
              const match = computeOverallMatch({
                answersA: sub.answers,
                answersB: baseline.answers,
                traitsA: sub.derived?.traits,
                traitsB: baseline.derived?.traits,
                boundariesA,
                boundariesB,
                domainsA,
                domainsB
              });
              // Debug dump
              dbg('submission.id', sub?.id);
              dbg('baseline.id', baseline?.id);
              dbg('EXCLUDED_FROM_MEAN', Array.from(EXCLUDED_FROM_MEAN || []));
              dbg('CATEGORY_MAP', CATEGORY_MAP);
              dbg('ANSWERS_A', sub?.answers);
              dbg('ANSWERS_B', baseline?.answers);
              dbg('BOUNDARIES_A', boundariesA);
              dbg('BOUNDARIES_B', boundariesB);
              dbg('TRAITS_A', sub?.derived?.traits);
              dbg('TRAITS_B', baseline?.derived?.traits);
              dbg('DOMAINS_A', domainsA);
              dbg('DOMAINS_B', domainsB);
              // Second run for introspection (re-using same inputs)
              const match2 = computeOverallMatch({
                answersA: sub.answers,
                answersB: baseline.answers,
                traitsA: sub.derived?.traits,
                traitsB: baseline.derived?.traits,
                boundariesA,
                boundariesB,
                domainsA,
                domainsB
              });
              dbg('MATCH_OUT', match2);
              if (match2?.catScores) {
                const rows = Object.entries(match2.catScores).map(([k, v]) => ({ category: k, percent: Math.round((v ?? 0) * 100) }));
                console.table(rows);
              }
              // Directional EXHIBITION inputs quick view
              try {
                const A_B9a = sub?.answers?.['B9a'];
                const B_B9a = baseline?.answers?.['B9a'];
                const A_B10b = sub?.answers?.['B10b'];
                const B_B10b = baseline?.answers?.['B10b'];
                console.table([
                  { key: 'A.B9a', value: A_B9a },
                  { key: 'B.B9a', value: B_B9a },
                  { key: 'A.B10b', value: A_B10b },
                  { key: 'B.B10b', value: B_B10b },
                  { key: 'catScores.EXHIBITION', value: Math.round((match2?.catScores?.EXHIBITION ?? 0) * 100) + '%' },
                ]);
              } catch {}
              setBaselineMatch({ baseline, match });
              console.log('✅ Match calculated:', match);
            } catch (matchError) {
              console.error('Error calculating match:', matchError);
              // Don't fail the whole page if match calculation fails
            }
          }
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error loading result data:', err);
        setError(`An error occurred: ${err.message}`);
        setLoading(false);
      }
    };

    loadData();
  }, [location, navigate, retryCount]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-rose-50 via-white to-pink-50">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-rose-100 rounded-full mb-4 animate-pulse">
            <Heart className="w-8 h-8 text-rose-600" />
          </div>
          <p className="text-gray-600">Loading your results...</p>
          {retryCount > 0 && (
            <p className="text-sm text-gray-500 mt-2">Retry attempt {retryCount}</p>
          )}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-rose-50 via-white to-pink-50 p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-6 h-6" />
              Unable to Load Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                Your submission may have been saved. You can check the admin panel to verify.
              </p>
              <div className="flex gap-2">
                <Button onClick={() => navigate('/')} variant="outline" className="flex-1">
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
                {retryCount < 3 && (
                  <Button onClick={() => setRetryCount(retryCount + 1)} className="flex-1">
                    Retry
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No submission (shouldn't happen after loading/error checks)
  if (!submission) {
    return null;
  }

  const { derived } = submission;
  const HIDE_TRAITS = new Set(['RECORDING','GROUP_ENM']);
  const visibleTraits = Object.entries(derived?.traits || {}).filter(([k]) => !HIDE_TRAITS.has(k));
  const gates = extractBoundaries(submission?.answers || {});

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-pink-50">
      <div className="container mx-auto px-4 py-12 max-w-5xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-rose-100 rounded-full mb-4">
            <Heart className="w-8 h-8 text-rose-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            {submission.name}'s Intimacy Profile
          </h1>
          <p className="text-gray-600">Here's what we discovered about you</p>
        </div>

        <Card className="mb-6" data-testid="result-demographics">
          <CardHeader>
            <CardTitle className="text-2xl">About You</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-700">
              <div>
                <p className="text-sm uppercase tracking-wide text-gray-500">Sex</p>
                <p className="text-lg font-semibold capitalize">{submission.sex || 'Not specified'}</p>
              </div>
              <div>
                <p className="text-sm uppercase tracking-wide text-gray-500">Sexual Orientation</p>
                <p className="text-lg font-semibold capitalize">{submission.sexualOrientation || 'Not specified'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Domains */}
        <Card className="mb-6" data-testid="result-domains">
          <CardHeader>
            <CardTitle className="text-2xl">Your Domains</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const domains = computeDomainsFromTraits(derived?.traits || {});
              return (
                <div className="space-y-4">
                  {/* Power Top & Bottom */}
                  <div>
                    <div className="flex justify-between mb-1"><span className="font-medium">Power (Top)</span><span>{Math.round(domains.powerTop)}</span></div>
                    <Progress value={domains.powerTop} />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="font-medium">Power (Bottom)</span><span>{Math.round(domains.powerBottom)}</span></div>
                    <Progress value={domains.powerBottom} />
                  </div>

                  {/* Connection, Sensory, Exploration, Structure */}
                  <div>
                    <div className="flex justify-between mb-1"><span className="font-medium">Connection</span><span>{Math.round(domains.connection)}</span></div>
                    <Progress value={domains.connection} />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="font-medium">Sensory</span><span>{Math.round(domains.sensory)}</span></div>
                    <Progress value={domains.sensory} />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="font-medium">Exploration</span><span>{Math.round(domains.exploration)}</span></div>
                    <Progress value={domains.exploration} />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="font-medium">Structure</span><span>{Math.round(domains.structure)}</span></div>
                    <Progress value={domains.structure} />
                  </div>

                  {/* Baseline comparison small badges (if baseline present) */}
                  {baselineMatch && baselineMatch.baseline?.derived?.traits && (
                    (() => {
                      const bd = computeDomainsFromTraits(baselineMatch.baseline.derived.traits || {});
                      const Row = ({ label, a, b }) => (
                        <div className="flex justify-between text-sm text-gray-700">
                          <span>{label}</span>
                          <span>{Math.round(a)} vs {Math.round(b)}</span>
                        </div>
                      );
                      return (
                        <div className="mt-4 space-y-1">
                          <Row label="Power (Top)" a={domains.powerTop} b={bd.powerTop} />
                          <Row label="Power (Bottom)" a={domains.powerBottom} b={bd.powerBottom} />
                          <Row label="Connection" a={domains.connection} b={bd.connection} />
                          <Row label="Sensory" a={domains.sensory} b={bd.sensory} />
                          <Row label="Exploration" a={domains.exploration} b={bd.exploration} />
                          <Row label="Structure" a={domains.structure} b={bd.structure} />
                        </div>
                      );
                    })()
                  )}
                </div>
              );
            })()}
          </CardContent>
        </Card>

        {/* Gates */}
        <Card className="mt-4" data-testid="result-gates">
          <CardHeader>
            <CardTitle>Gates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-gray-700">
            <div><strong>Recording OK:</strong> {gates.noRecording ? 'No' : 'Yes'}</div>
            <div><strong>Impact Cap:</strong> {Number.isFinite(gates.impactCap) ? `${gates.impactCap}/100` : '—'}</div>
            <div>
              <strong>Hard NOs:</strong>{' '}
              {gates.hardNos?.length ? gates.hardNos.join(', ') : 'None'}
            </div>
          </CardContent>
        </Card>

        {/* Traits - if available (hide gate traits) */}
        {visibleTraits.length > 0 && (
          <Card className="mb-6" data-testid="result-traits">
            <CardHeader>
              <CardTitle className="text-2xl">Your Traits</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {visibleTraits.map(([trait, score]) => (
                  <div key={trait}>
                    <div className="flex justify-between mb-2">
                      <span className="font-medium capitalize">{trait}</span>
                      <span className="text-gray-600">{Math.round(score * 100)}/100</span>
                    </div>
                    <Progress value={score * 100} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Baseline Match */}
        {baselineMatch && (
          <Card className="mb-6" data-testid="result-match">
            <CardHeader>
              <CardTitle className="text-2xl">Compatibility with {baselineMatch.baseline.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="font-medium">Overall Match</span>
                    <span className="text-gray-600">{Math.round(baselineMatch.match.overall * 1)}%</span>
                  </div>
                  <Progress value={baselineMatch.match.overall * 1} />
                </div>
                {baselineMatch.match.catScores && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">Category Breakdown</h4>
                    <div className="space-y-2">
                      {Object.entries(baselineMatch.match.catScores)
                        .filter(([category]) => !EXCLUDED_FROM_MEAN.has(category))
                        .map(([category, score]) => (
                        <div key={category} className="flex justify-between text-sm">
                          <span className="capitalize">{category}</span>
                          <span>{Math.round(score * 100)}%</span>
                        </div>
                      ))}
                      <p className="text-xs text-gray-500 mt-2">
                        Compatibility excludes gate categories: {Array.from(EXCLUDED_FROM_MEAN).join(', ')}. See “Gates” for details.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex justify-center gap-4">
          <Button onClick={() => navigate('/')} variant="outline">
            <Home className="w-4 h-4 mr-2" />
            Home
          </Button>
          <Button onClick={() => navigate('/survey')} variant="outline">
            <Edit className="w-4 h-4 mr-2" />
            Take Again
          </Button>
        </div>
      </div>
    </div>
  );
}

