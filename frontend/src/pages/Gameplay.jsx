import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ChevronRight, ChevronLeft, Home, X, Sparkles } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getSessionActivities } from '../lib/storage/apiStore';

export default function Gameplay() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [session, setSession] = useState(null);
  const [activities, setActivities] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const playerA = location.state?.playerA;
  const playerB = location.state?.playerB;

  useEffect(() => {
    loadSession();
  }, []);

  const loadSession = async () => {
    try {
      const sessionId = location.state?.sessionId;
      
      if (!sessionId) {
        setError('No session ID provided');
        setLoading(false);
        return;
      }

      console.log('Loading session:', sessionId);
      const sessionData = await getSessionActivities(sessionId);
      
      if (!sessionData) {
        setError('Session not found');
        setLoading(false);
        return;
      }

      setSession(sessionData.session);
      setActivities(sessionData.activities || []);
      setLoading(false);
      
      console.log('✅ Session loaded:', {
        id: sessionId,
        activities: sessionData.activities?.length
      });
    } catch (err) {
      console.error('Error loading session:', err);
      setError(err.message || 'Failed to load game session');
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (currentStep < activities.length - 1) {
      setCurrentStep(currentStep + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleEndGame = () => {
    if (confirm('Are you sure you want to end the game? Progress will not be saved.')) {
      navigate('/result', { state: { submissionId: playerA?.id } });
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-rose-50 via-white to-pink-50">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-rose-100 rounded-full mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-rose-600" />
          </div>
          <p className="text-gray-600">Loading game session...</p>
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
            <CardTitle className="text-red-600">Unable to Load Game</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <Button onClick={() => navigate('/')} className="w-full">
              <Home className="w-4 h-4 mr-2" />
              Return Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No activities
  if (!activities || activities.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-rose-50 via-white to-pink-50 p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle>No Activities Found</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600">This session has no activities.</p>
            <Button onClick={() => navigate('/')} className="w-full">
              <Home className="w-4 h-4 mr-2" />
              Return Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentActivity = activities[currentStep];
  const progress = ((currentStep + 1) / activities.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-pink-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Attuned Gameplay
          </h1>
          <p className="text-gray-600">
            {playerA?.name && playerB?.name 
              ? `${playerA.name} & ${playerB.name}` 
              : 'Game Session'}
          </p>
        </div>

        {/* Session Configuration Card */}
        {session && (
          <Card className="mb-6 bg-gradient-to-r from-rose-50 to-pink-50">
            <CardContent className="pt-4 pb-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-sm text-gray-600">Player A</div>
                  <div className="font-semibold text-gray-900">{playerA?.name || 'Player A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Player B</div>
                  <div className="font-semibold text-gray-900">{playerB?.name || 'Player B'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Rating</div>
                  <div className="font-semibold text-gray-900">{session.rating}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Mode</div>
                  <div className="font-semibold text-gray-900 capitalize">{session.activity_type}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Progress Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Step {currentStep + 1} of {activities.length}</span>
                <span>{Math.round(progress)}% Complete</span>
              </div>
              <Progress value={progress} className="h-3" />
            </div>
          </CardContent>
        </Card>

        {/* Activity Card */}
        {currentActivity && (
          <Card className="mb-6 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-rose-500 to-pink-500 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    currentActivity.type === 'truth' 
                      ? 'bg-green-500/30 border border-green-300' 
                      : 'bg-purple-500/30 border border-purple-300'
                  }`}>
                    {currentActivity.type === 'truth' ? 'Truth' : 'Dare'}
                  </span>
                  <div className="flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full ${
                          i < currentActivity.intensity 
                            ? 'bg-white' 
                            : 'bg-white/30'
                        }`}
                      />
                    ))}
                  </div>
                </div>
                <span className="text-sm opacity-90">
                  Rating: {currentActivity.rating}
                </span>
              </div>
            </CardHeader>
            <CardContent className="pt-8 pb-8">
              <div className="space-y-6">
                {/* Activity Steps */}
                {currentActivity.script?.steps?.map((step, idx) => {
                  // Map actor letter to player name
                  const actorName = step.actor === 'A' 
                    ? (playerA?.name || 'Player A')
                    : (playerB?.name || 'Player B');
                  
                  return (
                    <div key={idx} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-semibold text-sm ${
                          step.actor === 'A' 
                            ? 'bg-blue-100 text-blue-700' 
                            : 'bg-purple-100 text-purple-700'
                        }`}>
                          {step.actor}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {actorName}
                        </span>
                      </div>
                      <p className="text-lg text-gray-900 pl-10">
                        {step.do}
                      </p>
                    </div>
                  );
                })}

                {/* Tags */}
                {currentActivity.tags && currentActivity.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap mt-4 pt-4 border-t">
                    {currentActivity.tags.map((tag, idx) => (
                      <span 
                        key={idx}
                        className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center gap-4 mb-8">
          <Button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            variant="outline"
            className="flex-1"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          
          {currentStep < activities.length - 1 ? (
            <Button
              onClick={handleNext}
              className="flex-1 bg-rose-600 hover:bg-rose-700"
            >
              Next
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleEndGame}
              variant="outline"
              className="flex-1 border-green-600 text-green-700 hover:bg-green-50"
            >
              Complete Session
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>

        {/* End Game */}
        <div className="flex justify-center">
          <Button onClick={handleEndGame} variant="ghost" size="sm" className="text-gray-500">
            <X className="w-4 h-4 mr-2" />
            End Game Early
          </Button>
        </div>

        {/* Session Info */}
        {session && (
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>Session: {session.session_id}</p>
            <p>Rating: {session.rating} | Type: {session.activity_type}</p>
          </div>
        )}
      </div>

      <footer className="text-center py-8 text-sm text-gray-500">
        <p>Made with ♥️ in BK</p>
      </footer>
    </div>
  );
}

