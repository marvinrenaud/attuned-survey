import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Edit, Home, Heart, AlertCircle, Play } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getSubmission, getBaseline, generateRecommendations, getCompatibility } from '../lib/storage/apiStore';
import { getCategoryName, getActivityName } from '../lib/matching/categoryMap';

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
  const [startingGame, setStartingGame] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const submissionId = location.state?.submissionId;

        if (!submissionId) {
          console.error('No submission ID in location state');
          setError('No submission ID provided');
          setLoading(false);
          return;
        }

        console.log(`Loading submission: ${submissionId} (attempt ${retryCount + 1})`);
        console.log('Fetching from backend...');

        // Retry logic: try up to 3 times with delays
        let sub = null;
        const maxRetries = 3;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
          if (attempt > 0) {
            console.log(`Retry attempt ${attempt}/${maxRetries}...`);
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
          }

          console.log(`  Calling getSubmission(${submissionId})...`);
          sub = await getSubmission(submissionId);
          console.log(`  Response received:`, sub ? 'Success' : 'Null response');

          if (sub) {
            console.log('✅ Submission loaded successfully', { id: sub.id, version: sub.version });
            break;
          } else {
            console.warn(`Attempt ${attempt + 1}: Submission not found or fetch failed`);
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
            // Check if both profiles are v0.4
            const currentIsV04 = sub.version === '0.4' || sub.derived?.profile_version === '0.4';
            const baselineIsV04 = baseline.version === '0.4' || baseline.derived?.profile_version === '0.4';

            console.log('Version check:', {
              current: currentIsV04 ? 'v0.4' : 'v0.3.1',
              baseline: baselineIsV04 ? 'v0.4' : 'v0.3.1'
            });

            if (currentIsV04 && baselineIsV04) {
              console.log('✅ Both profiles are v0.4, fetching compatibility...');
              try {
                const compatibility = await getCompatibility(sub.id, baseline.id);
                dbg('Compatibility result:', compatibility);
                setBaselineMatch({ baseline, compatibility });
                console.log('✅ Compatibility fetched:', compatibility.overall_compatibility);
              } catch (matchError) {
                console.error('Error fetching compatibility:', matchError);
                // Set baseline without compatibility for display
                setBaselineMatch({ baseline, compatibility: null, error: matchError.message });
              }
            } else {
              // Version mismatch or missing data
              console.warn('⚠️ Version mismatch or missing data - cannot calculate compatibility');
              setBaselineMatch({
                baseline,
                compatibility: null,
                versionMismatch: !currentIsV04 || !baselineIsV04
              });
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

  const handleStartGame = async () => {
    if (!submission || !baselineMatch?.baseline) {
      console.error('Cannot start game: missing submission or baseline');
      return;
    }

    setStartingGame(true);

    try {
      console.log('Starting game session...');

      // Generate recommendations for 25 activities
      const payload = {
        player_a: { submission_id: submission.id },
        player_b: { submission_id: baselineMatch.baseline.id },
        session: {
          rating: 'R',  // Default to R-rated
          target_activities: 25,
          activity_type: 'random',
          bank_ratio: 0.5,
          rules: { avoid_maybe_until: 6 }
        }
      };

      const recommendationsData = await generateRecommendations(payload);

      console.log('✅ Game session created:', recommendationsData.session_id);

      // Navigate to gameplay page with session ID
      navigate('/gameplay', {
        state: {
          sessionId: recommendationsData.session_id,
          playerA: submission,
          playerB: baselineMatch.baseline
        }
      });
    } catch (err) {
      console.error('Error starting game:', err);
      alert('Failed to start game: ' + err.message);
      setStartingGame(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-primary">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-tertiary rounded-full mb-4 animate-pulse">
            <Heart className="w-8 h-8 text-primary" />
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
      <div className="min-h-screen flex items-center justify-center bg-background-primary p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-6 h-6" />
              Unable to Load Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertDescription>
                {error.includes('timeout')
                  ? 'Backend is taking longer than expected. The database may be slow. Please try again.'
                  : error.includes('500')
                    ? 'Backend database encountered an error. Please try again in a moment.'
                    : error.includes('No submission ID')
                      ? 'No submission ID provided. Please complete the survey first.'
                      : error}
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                {error.includes('No submission ID')
                  ? 'You need to complete a survey to see results.'
                  : 'Your submission may have been saved. Try reloading or check the admin panel.'}
              </p>
              <div className="flex gap-2">
                <Button onClick={() => navigate('/')} variant="outline" className="flex-1">
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
                {!error.includes('No submission ID') && (
                  <Button onClick={() => window.location.reload()} className="flex-1">
                    Retry Loading
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No submission
  if (!submission) {
    return null;
  }

  const { derived } = submission;

  // Check if this is a v0.4 profile
  if (!derived || !derived.profile_version || derived.profile_version !== '0.4') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-primary p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-600">
              <AlertCircle className="w-6 h-6" />
              Incompatible Profile Version
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              This profile was created with an older version of the survey and cannot be displayed with the current system.
            </p>
            <Button onClick={() => navigate('/')} className="w-full">
              <Home className="w-4 h-4 mr-2" />
              Take New Survey
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const {
    arousal_propensity,
    power_dynamic,
    domain_scores,
    boundaries,
    activities,
    truth_topics
  } = derived;

  return (
    <div className="min-h-screen bg-background-primary">
      <div className="container mx-auto px-4 py-12 max-w-5xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-tertiary rounded-full mb-4">
            <Heart className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2 font-heading">
            {submission.name}'s Intimacy Profile
          </h1>
          <p className="text-gray-600">Your personalized intimacy profile (v0.4)</p>
          <p className="text-sm text-gray-500 mt-1">Completed on {new Date(submission.createdAt).toLocaleDateString()}</p>
        </div>

        {/* Demographics */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">About You</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-700">
              <div>
                <p className="text-sm uppercase tracking-wide text-gray-500">Your Anatomy</p>
                <p className="text-lg font-semibold capitalize">
                  {derived.anatomy?.anatomy_self?.join(', ') || 'Not specified'}
                </p>
              </div>
              <div>
                <p className="text-sm uppercase tracking-wide text-gray-500">Partner Anatomy Preferences</p>
                <p className="text-lg font-semibold capitalize">
                  {derived.anatomy?.anatomy_preference?.join(', ') || 'Not specified'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Arousal Propensity */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">Arousal Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Your arousal style based on the Sexual Excitation/Sexual Inhibition model.
            </p>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <div>
                    <span className="font-medium">Sexual Excitation (SE)</span>
                    <span className="ml-2 text-sm text-gray-500">({arousal_propensity.interpretation.se})</span>
                  </div>
                  <span className="text-gray-600">{Math.round(arousal_propensity.sexual_excitation * 100)}%</span>
                </div>
                <Progress value={arousal_propensity.sexual_excitation * 100} />
                <p className="text-sm text-gray-600 mt-1">How easily you become aroused</p>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <div>
                    <span className="font-medium">Inhibition - Performance (SIS-P)</span>
                    <span className="ml-2 text-sm text-gray-500">({arousal_propensity.interpretation.sis_p})</span>
                  </div>
                  <span className="text-gray-600">{Math.round(arousal_propensity.inhibition_performance * 100)}%</span>
                </div>
                <Progress value={arousal_propensity.inhibition_performance * 100} />
                <p className="text-sm text-gray-600 mt-1">Performance concerns that affect arousal</p>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <div>
                    <span className="font-medium">Inhibition - Consequence (SIS-C)</span>
                    <span className="ml-2 text-sm text-gray-500">({arousal_propensity.interpretation.sis_c})</span>
                  </div>
                  <span className="text-gray-600">{Math.round(arousal_propensity.inhibition_consequence * 100)}%</span>
                </div>
                <Progress value={arousal_propensity.inhibition_consequence * 100} />
                <p className="text-sm text-gray-600 mt-1">Concerns about consequences that affect arousal</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Power Dynamic */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">Power Dynamic</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-semibold">{power_dynamic.orientation}</h3>
                <span className="text-sm text-gray-600">{power_dynamic.interpretation}</span>
              </div>

              {/* Visual slider for power dynamic */}
              <div className="relative h-12 bg-gradient-to-r from-blue-200 via-purple-200 to-pink-200 rounded-lg mb-4">
                <div
                  className="absolute top-1/2 transform -translate-y-1/2 w-4 h-4 bg-gray-800 rounded-full border-2 border-white shadow-lg"
                  style={{
                    left: power_dynamic.orientation === 'Switch'
                      ? '50%'
                      : power_dynamic.orientation === 'Top'
                        ? `${50 - power_dynamic.confidence * 50}%`
                        : power_dynamic.orientation === 'Bottom'
                          ? `${50 + power_dynamic.confidence * 50}%`
                          : '50%',
                    transform: 'translate(-50%, -50%)'
                  }}
                />
                <div className="absolute inset-0 flex items-center justify-between px-3 text-xs font-medium">
                  <span>Top</span>
                  <span>Switch</span>
                  <span>Bottom</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Top Score</span>
                    <span className="text-sm font-medium">{power_dynamic.top_score}/100</span>
                  </div>
                  <Progress value={power_dynamic.top_score} />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Bottom Score</span>
                    <span className="text-sm font-medium">{power_dynamic.bottom_score}/100</span>
                  </div>
                  <Progress value={power_dynamic.bottom_score} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Domain Scores */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">Domain Preferences</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Your preferences across five key domains of intimacy.
            </p>
            <div className="space-y-4">
              {Object.entries(domain_scores).map(([domain, score]) => (
                <div key={domain}>
                  <div className="flex justify-between mb-2">
                    <span className="font-medium capitalize">{domain}</span>
                    <span className="text-gray-600">{score}/100</span>
                  </div>
                  <Progress value={score} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">Activity Interests</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Activities you're open to exploring with a partner.
            </p>
            <div className="space-y-4">
              {Object.entries(activities).map(([category, categoryActivities]) => {
                const interested = Object.entries(categoryActivities).filter(([_, val]) => val >= 0.5);
                if (interested.length === 0) return null;

                return (
                  <div key={category} className="border-t pt-3 first:border-t-0 first:pt-0">
                    <h4 className="font-medium mb-2 capitalize">{getCategoryName(category)}</h4>
                    <div className="flex flex-wrap gap-2">
                      {interested.map(([activity, value]) => (
                        <span
                          key={activity}
                          className={`px-3 py-1 rounded-full text-sm ${value === 1.0
                              ? 'bg-accent-sage/20 text-accent-sage'
                              : 'bg-tertiary/50 text-text-secondary'
                            }`}
                        >
                          {getActivityName(activity)} {value === 0.5 ? '(Maybe)' : ''}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Boundaries */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">Boundaries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Hard Limits</h4>
                {boundaries.hard_limits && boundaries.hard_limits.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {boundaries.hard_limits.map((limit, idx) => (
                      <span key={idx} className="px-3 py-1 bg-error/20 text-error rounded-full text-sm capitalize">
                        {limit.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">No hard limits specified</p>
                )}
              </div>

              {boundaries.additional_notes && (
                <div>
                  <h4 className="font-medium mb-2">Additional Notes</h4>
                  <p className="text-gray-700 italic">"{boundaries.additional_notes}"</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Truth Topics */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">Truth Topic Openness</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="font-medium">Overall Openness</span>
                <span className="text-gray-600">{truth_topics.openness_score}/100</span>
              </div>
              <Progress value={truth_topics.openness_score} />
            </div>
            <p className="text-sm text-gray-600">
              Your comfort level discussing intimate topics with a partner.
            </p>
          </CardContent>
        </Card>

        {/* Compatibility (if baseline set) */}
        {baselineMatch && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-2xl">
                Compatibility with {baselineMatch.baseline.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Version mismatch warning */}
              {baselineMatch.versionMismatch && (
                <Alert variant="destructive" className="mb-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Version Mismatch:</strong> The baseline profile was created with a different survey version.
                    Both profiles must be v0.4 to calculate compatibility. Please have your partner retake the survey,
                    then set their new submission as the baseline.
                  </AlertDescription>
                </Alert>
              )}

              {/* Error during calculation */}
              {baselineMatch.error && !baselineMatch.versionMismatch && (
                <Alert variant="destructive" className="mb-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Error:</strong> Failed to calculate compatibility: {baselineMatch.error}
                  </AlertDescription>
                </Alert>
              )}

              {/* Successful compatibility calculation */}
              {baselineMatch.compatibility && (
                <div className="space-y-6">
                  {/* Overall Score */}
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="font-medium text-lg">Overall Compatibility</span>
                      <span className="text-lg font-semibold text-primary">
                        {baselineMatch.compatibility.overall_compatibility.score}%
                      </span>
                    </div>
                    <Progress value={baselineMatch.compatibility.overall_compatibility.score} />
                    <p className="text-sm text-gray-600 mt-1">
                      {baselineMatch.compatibility.overall_compatibility.interpretation}
                    </p>
                  </div>

                  {/* Breakdown */}
                  <div>
                    <h4 className="font-medium mb-3">Compatibility Breakdown</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="flex justify-between mb-1 text-sm">
                          <span>Power Complement</span>
                          <span>{baselineMatch.compatibility.breakdown.power_complement}%</span>
                        </div>
                        <Progress value={baselineMatch.compatibility.breakdown.power_complement} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1 text-sm">
                          <span>Domain Similarity</span>
                          <span>{baselineMatch.compatibility.breakdown.domain_similarity}%</span>
                        </div>
                        <Progress value={baselineMatch.compatibility.breakdown.domain_similarity} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1 text-sm">
                          <span>Activity Overlap</span>
                          <span>{baselineMatch.compatibility.breakdown.activity_overlap}%</span>
                        </div>
                        <Progress value={baselineMatch.compatibility.breakdown.activity_overlap} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1 text-sm">
                          <span>Truth Topics</span>
                          <span>{baselineMatch.compatibility.breakdown.truth_overlap}%</span>
                        </div>
                        <Progress value={baselineMatch.compatibility.breakdown.truth_overlap} className="h-2" />
                      </div>
                    </div>
                  </div>

                  {/* Boundary Conflicts */}
                  {baselineMatch.compatibility.breakdown.boundary_conflicts.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2 text-red-600">⚠️ Boundary Conflicts</h4>
                      <div className="bg-red-50 p-3 rounded-lg">
                        <p className="text-sm text-red-800 mb-2">
                          {baselineMatch.compatibility.breakdown.boundary_conflicts.length} potential conflict(s) detected
                        </p>
                        <ul className="text-sm text-red-700 list-disc list-inside">
                          {baselineMatch.compatibility.breakdown.boundary_conflicts.slice(0, 3).map((conflict, idx) => (
                            <li key={idx}>
                              {conflict.player}'s boundary: {conflict.boundary.replace(/_/g, ' ')}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* Mutual Activities */}
                  {baselineMatch.compatibility.mutual_activities && (
                    <div>
                      <h4 className="font-medium mb-2">Shared Interests</h4>
                      <div className="space-y-2">
                        {Object.entries(baselineMatch.compatibility.mutual_activities).map(([category, acts]) => {
                          if (!acts || acts.length === 0) return null;
                          return (
                            <div key={category}>
                              <span className="text-sm font-medium capitalize">{getCategoryName(category)}: </span>
                              <span className="text-sm text-gray-600">{acts.length} shared activities</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex justify-center gap-4 flex-wrap">
          <Button onClick={() => navigate('/')} variant="outline">
            <Home className="w-4 h-4 mr-2" />
            Home
          </Button>

          {/* Start Game button - only show if baseline match exists */}
          {baselineMatch?.baseline && baselineMatch?.compatibility && (
            <Button
              onClick={handleStartGame}
              disabled={startingGame}
              className="bg-gradient-to-r from-primary to-secondary hover:from-primary-dark hover:to-secondary-dark"
            >
              <Play className="w-4 h-4 mr-2" />
              {startingGame ? 'Starting Game...' : 'Start Game'}
            </Button>
          )}

          <Button onClick={() => navigate('/admin')} variant="outline">
            <Edit className="w-4 h-4 mr-2" />
            Admin Panel
          </Button>
        </div>
      </div>

      <footer className="text-center py-8 text-sm text-gray-500">
        <p>Made with ♥️ in BK</p>
      </footer>
    </div>
  );
}
