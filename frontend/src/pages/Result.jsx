import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Edit, Home, Heart, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getSubmission, getBaseline } from '../lib/storage/apiStore';
import { computeOverallMatch } from '../lib/matching/overlapHelper';

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
              const match = computeOverallMatch({
                answersA: sub.answers,
                answersB: baseline.answers,
                traitsA: sub.derived.traits,
                traitsB: baseline.derived.traits,
                boundariesA: sub.derived.boundaryFlags,
                boundariesB: baseline.derived.boundaryFlags
              });
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

        {/* Archetype */}
        <Card className="mb-6" data-testid="result-archetype">
          <CardHeader>
            <CardTitle className="text-2xl">Your Archetype{derived.archetypes.length > 1 ? 's' : ''}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {derived.archetypes.map((archetype, idx) => (
                <div key={idx} className="p-4 bg-rose-50 rounded-lg">
                  <h3 className="text-xl font-semibold text-rose-900 mb-2">{archetype.name}</h3>
                  <Progress value={archetype.score * 100} className="mb-2" />
                  <p className="text-sm text-gray-700">{archetype.score > 0.7 ? 'Strong match' : 'Moderate match'}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Dials */}
        <Card className="mb-6" data-testid="result-dials">
          <CardHeader>
            <CardTitle className="text-2xl">Your Four Dimensions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {Object.entries(derived.dials).map(([dimension, score]) => (
                <div key={dimension}>
                  <div className="flex justify-between mb-2">
                    <span className="font-medium capitalize">{dimension}</span>
                    <span className="text-gray-600">{Math.round(score)}/100</span>
                  </div>
                  <Progress value={score} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

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
                    <span className="text-gray-600">{Math.round(baselineMatch.match.overallScore)}%</span>
                  </div>
                  <Progress value={baselineMatch.match.overallScore} />
                </div>
                {baselineMatch.match.categoryScores && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">Category Breakdown</h4>
                    <div className="space-y-2">
                      {Object.entries(baselineMatch.match.categoryScores).map(([category, score]) => (
                        <div key={category} className="flex justify-between text-sm">
                          <span className="capitalize">{category}</span>
                          <span>{Math.round(score)}%</span>
                        </div>
                      ))}
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

