import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Download, Database, History, AlertCircle, Home, Sparkles } from 'lucide-react';
import { computeDomainsFromTraits } from '@/lib/scoring/domainCalculator';
import {
  getAllSubmissions,
  getBaseline,
  setBaseline,
  clearBaseline,
  exportData,
  generateRecommendations,
  getSessionActivities
} from '../lib/storage/apiStore';

const ADMIN_PASSWORD = '1111';

export default function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = () => {
    if (password === ADMIN_PASSWORD) {
      setIsAuthenticated(true);
      setError('');
    } else {
      setError('Incorrect password');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Admin Login</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Input
                  type="password"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                  data-testid="admin-login"
                />
              </div>
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <Button onClick={handleLogin} className="w-full">
                Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <Link to="/">
            <Button variant="outline" className="gap-2">
              <Home className="w-4 h-4" />
              Home
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Link to="/admin">
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <Database className="w-8 h-8 text-rose-600 mb-2" />
                <h3 className="font-semibold text-gray-900">Responses</h3>
                <p className="text-sm text-gray-600">View and manage submissions</p>
              </CardContent>
            </Card>
          </Link>
          <Link to="/admin/export">
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <Download className="w-8 h-8 text-blue-600 mb-2" />
                <h3 className="font-semibold text-gray-900">Export</h3>
                <p className="text-sm text-gray-600">Download data as CSV/JSON</p>
              </CardContent>
            </Card>
          </Link>
          <Link to="/admin/recommendations">
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <Sparkles className="w-8 h-8 text-amber-600 mb-2" />
                <h3 className="font-semibold text-gray-900">Recommendations</h3>
                <p className="text-sm text-gray-600">Test AI activity generation</p>
              </CardContent>
            </Card>
          </Link>
          <Link to="/admin/history">
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <History className="w-8 h-8 text-purple-600 mb-2" />
                <h3 className="font-semibold text-gray-900">History</h3>
                <p className="text-sm text-gray-600">Version history & rollback</p>
              </CardContent>
            </Card>
          </Link>
        </div>

        <Routes>
          <Route index element={<ResponsesList />} />
          <Route path="export" element={<ExportTools />} />
          <Route path="recommendations" element={<RecommendationsPanel />} />
          <Route path="history" element={<VersionHistory />} />
        </Routes>
      </div>

      <footer className="text-center py-8 text-sm text-gray-500">
        <p>Made with ♥️ in BK</p>
      </footer>
    </div>
  );
}

function ResponsesList() {
  const [submissions, setSubmissions] = useState([]);
  const [baselineId, setBaselineIdState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllSubmissions();
      setSubmissions(data.submissions || []);
      setBaselineIdState(data.baseline);
    } catch (err) {
      console.error('Error loading submissions:', err);
      setError(err.message || 'Failed to load submissions');
    } finally {
      setLoading(false);
    }
  };

  const handleSetBaseline = async (id) => {
    try {
      await setBaseline(id);
      setBaselineIdState(id);
    } catch (error) {
      console.error('Error setting baseline:', error);
    }
  };

  if (loading) {
    return <Card><CardContent className="pt-6">Loading...</CardContent></Card>;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Unable to Load Submissions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error.includes('500') || error.includes('timeout')
                ? 'Backend database is responding slowly or unavailable. Please try again in a moment.'
                : error.includes('404')
                ? 'Backend endpoint not found. Please check your configuration.'
                : 'Could not connect to backend. Check your internet connection.'}
            </AlertDescription>
          </Alert>
          <div className="flex gap-2">
            <Button onClick={loadData} className="flex-1">
              Retry Loading
            </Button>
            <Button onClick={() => window.location.reload()} variant="outline" className="flex-1">
              Refresh Page
            </Button>
          </div>
          <p className="text-sm text-gray-600">
            If the problem persists, the backend service may be experiencing issues.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>All Submissions</CardTitle>
      </CardHeader>
      <CardContent>
        {submissions.length === 0 ? (
          <p className="text-gray-600">No submissions yet.</p>
        ) : (
          <div className="overflow-x-auto" data-testid="responses-table">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Sex</TableHead>
                  <TableHead>Orientation</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>PowerTop</TableHead>
                  <TableHead>PowerBottom</TableHead>
                  <TableHead>Connection</TableHead>
                  <TableHead>Sensory</TableHead>
                  <TableHead>Exploration</TableHead>
                  <TableHead>Structure</TableHead>
                  <TableHead>Baseline</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {submissions.map((sub) => {
                  // Handle both v0.3.1 and v0.4 profiles
                  const isV04 = sub.version === '0.4' || sub.derived?.profile_version === '0.4';
                  let d;
                  
                  if (isV04 && sub.derived?.domain_scores) {
                    // v0.4 has domains directly
                    d = {
                      powerTop: sub.derived.power_dynamic?.top_score || 0,
                      powerBottom: sub.derived.power_dynamic?.bottom_score || 0,
                      connection: sub.derived.domain_scores.connection || 0,
                      sensory: sub.derived.domain_scores.sensation || 0, // Note: v0.4 calls it "sensation"
                      exploration: sub.derived.domain_scores.exploration || 0,
                      structure: sub.derived.domain_scores.power || 0 // Note: v0.4 "power" domain is similar to "structure"
                    };
                  } else {
                    // v0.3.1 - compute from traits
                    d = computeDomainsFromTraits(sub.derived?.traits || {});
                  }
                  
                  return (
                    <TableRow key={sub.id}>
                      <TableCell className="font-medium">{sub.name}</TableCell>
                      <TableCell className="capitalize">{sub.sex || '-'}</TableCell>
                      <TableCell className="capitalize">{sub.sexualOrientation || '-'}</TableCell>
                      <TableCell>{new Date(sub.createdAt).toLocaleDateString()}</TableCell>
                      <TableCell>{sub.version || '—'}</TableCell>
                      <TableCell>{Math.round(d.powerTop)}</TableCell>
                      <TableCell>{Math.round(d.powerBottom)}</TableCell>
                      <TableCell>{Math.round(d.connection)}</TableCell>
                      <TableCell>{Math.round(d.sensory)}</TableCell>
                      <TableCell>{Math.round(d.exploration)}</TableCell>
                      <TableCell>{Math.round(d.structure)}</TableCell>
                      <TableCell>
                        <Button
                          variant={baselineId === sub.id ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => handleSetBaseline(sub.id)}
                          data-testid="set-baseline"
                        >
                          {baselineId === sub.id ? 'Baseline' : 'Set'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ExportTools() {
  const handleExportJSON = async () => {
    try {
      const data = await exportData();
      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attuned-submissions-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting JSON:', error);
      alert('Failed to export data');
    }
  };

  const handleExportCSV = async () => {
    try {
      const data = await exportData();
      const submissions = data.submissions || [];
      
      // Create CSV header
      const headers = ['Name', 'Sex', 'Sexual Orientation', 'Created', 'Version', 'PowerTop', 'PowerBottom', 'Connection', 'Sensory', 'Exploration', 'Structure'];
      const rows = submissions.map(sub => {
        const d = computeDomainsFromTraits(sub.derived?.traits || {});
        return [
          sub.name,
          sub.sex || '',
          sub.sexualOrientation || '',
          new Date(sub.createdAt).toISOString(),
          sub.version || '',
          Math.round(d.powerTop),
          Math.round(d.powerBottom),
          Math.round(d.connection),
          Math.round(d.sensory),
          Math.round(d.exploration),
          Math.round(d.structure)
        ];
      });
      
      const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attuned-submissions-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export data');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Export Data</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">CSV Export</h3>
            <p className="text-sm text-gray-600 mb-3">
              Download all submissions as a CSV file with key metrics.
            </p>
            <Button onClick={handleExportCSV} className="gap-2" data-testid="export-csv">
              <Download className="w-4 h-4" />
              Export CSV
            </Button>
          </div>
          <div className="border-t pt-4">
            <h3 className="font-semibold text-gray-900 mb-2">JSON Export</h3>
            <p className="text-sm text-gray-600 mb-3">
              Download complete submission data including all answers and derived scores.
            </p>
            <Button onClick={handleExportJSON} className="gap-2" data-testid="export-json">
              <Download className="w-4 h-4" />
              Export JSON
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RecommendationsPanel() {
  const [submissions, setSubmissions] = useState([]);
  const [playerA, setPlayerA] = useState('');
  const [playerB, setPlayerB] = useState('');
  const [rating, setRating] = useState('R');
  const [targetActivities, setTargetActivities] = useState(5);
  const [activityType, setActivityType] = useState('random');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSubmissions();
  }, []);

  const loadSubmissions = async () => {
    try {
      const data = await getAllSubmissions();
      setSubmissions(data.submissions || []);
      
      // Auto-select first two submissions if available
      if (data.submissions && data.submissions.length >= 2) {
        setPlayerA(data.submissions[0].id);
        setPlayerB(data.submissions[1].id);
      }
    } catch (error) {
      console.error('Error loading submissions:', error);
    }
  };

  const handleGenerate = async () => {
    if (!playerA || !playerB) {
      setError('Please select both Player A and Player B');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        player_a: { submission_id: playerA },
        player_b: { submission_id: playerB },
        session: {
          rating,
          target_activities: parseInt(targetActivities),
          activity_type: activityType,
          bank_ratio: 0.5,
          rules: { avoid_maybe_until: 6 }
        }
      };

      const data = await generateRecommendations(payload);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;

    const json = JSON.stringify(result, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recommendations-${result.session_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Recommendations (Groq AI)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Player A
              </label>
              <select
                className="w-full border border-gray-300 rounded-md p-2"
                value={playerA}
                onChange={(e) => setPlayerA(e.target.value)}
              >
                <option value="">Select Player A</option>
                {submissions.map(sub => (
                  <option key={sub.id} value={sub.id}>
                    {sub.name} ({sub.sex || 'unknown'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Player B
              </label>
              <select
                className="w-full border border-gray-300 rounded-md p-2"
                value={playerB}
                onChange={(e) => setPlayerB(e.target.value)}
              >
                <option value="">Select Player B</option>
                {submissions.map(sub => (
                  <option key={sub.id} value={sub.id}>
                    {sub.name} ({sub.sex || 'unknown'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rating
              </label>
              <select
                className="w-full border border-gray-300 rounded-md p-2"
                value={rating}
                onChange={(e) => setRating(e.target.value)}
              >
                <option value="G">G - General (family-friendly)</option>
                <option value="R">R - Restricted (sensual/intimate)</option>
                <option value="X">X - Explicit (sexual content)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Activities
              </label>
              <Input
                type="number"
                min="1"
                max="50"
                value={targetActivities}
                onChange={(e) => setTargetActivities(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Activity Type
              </label>
              <select
                className="w-full border border-gray-300 rounded-md p-2"
                value={activityType}
                onChange={(e) => setActivityType(e.target.value)}
              >
                <option value="random">Random Mix (~50/50)</option>
                <option value="truth">Truth Only</option>
                <option value="dare">Dare Only</option>
              </select>
            </div>
          </div>

          {/* Generate Button */}
          <div>
            <Button
              onClick={handleGenerate}
              disabled={loading || !playerA || !playerB}
              className="w-full gap-2"
            >
              <Sparkles className="w-4 h-4" />
              {loading ? 'Generating...' : 'Generate Plan'}
            </Button>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">
                  Generated Plan
                </h3>
                <Button onClick={handleDownload} variant="outline" className="gap-2">
                  <Download className="w-4 h-4" />
                  Download JSON
                </Button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-blue-50 p-3 rounded">
                  <div className="text-2xl font-bold text-blue-900">{result.stats?.total || 0}</div>
                  <div className="text-xs text-blue-700">Total Activities</div>
                </div>
                <div className="bg-green-50 p-3 rounded">
                  <div className="text-2xl font-bold text-green-900">{result.stats?.truths || 0}</div>
                  <div className="text-xs text-green-700">Truths</div>
                </div>
                <div className="bg-purple-50 p-3 rounded">
                  <div className="text-2xl font-bold text-purple-900">{result.stats?.dares || 0}</div>
                  <div className="text-xs text-purple-700">Dares</div>
                </div>
                <div className="bg-amber-50 p-3 rounded">
                  <div className="text-2xl font-bold text-amber-900">{result.stats?.bank_count || 0}</div>
                  <div className="text-xs text-amber-700">From Bank</div>
                </div>
                <div className="bg-rose-50 p-3 rounded">
                  <div className="text-2xl font-bold text-rose-900">{Math.round(result.stats?.elapsed_ms || 0)}ms</div>
                  <div className="text-xs text-rose-700">Generation Time</div>
                </div>
              </div>

              {/* Activities Preview */}
              <div className="border rounded p-4 bg-gray-50 max-h-96 overflow-y-auto">
                <h4 className="font-semibold mb-3">Activities Preview:</h4>
                <div className="space-y-2">
                  {result.activities?.slice(0, 10).map((activity, idx) => (
                    <div key={idx} className="bg-white p-3 rounded border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-gray-500">#{activity.seq}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          activity.type === 'truth' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800'
                        }`}>
                          {activity.type}
                        </span>
                        <span className="text-xs text-gray-500">
                          Intensity: {activity.intensity}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">
                        {activity.script?.steps?.[0]?.do || 'No description'}
                      </p>
                    </div>
                  ))}
                  {result.activities?.length > 10 && (
                    <p className="text-sm text-gray-500 text-center pt-2">
                      ... and {result.activities.length - 10} more activities
                    </p>
                  )}
                </div>
              </div>

              {/* Full JSON */}
              <details className="border rounded">
                <summary className="p-3 cursor-pointer font-semibold text-gray-900 hover:bg-gray-50">
                  View Full JSON
                </summary>
                <div className="p-3 bg-gray-50 border-t">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function VersionHistory() {
  // Placeholder for version history functionality
  // In a full implementation, this would track schema versions and allow rollback
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Version History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="border-l-4 border-blue-400 pl-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-semibold text-gray-900">v0.2.3 (Current)</h3>
                <p className="text-sm text-gray-600">October 2025</p>
              </div>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Active</span>
            </div>
            <p className="text-sm text-gray-700">
              B28 reweighted; B27 RISK reduced; Power complement and strict boundary gates added to matching.
            </p>
          </div>

          <div className="border-l-4 border-gray-300 pl-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-semibold text-gray-900">v0.2.2</h3>
                <p className="text-sm text-gray-600">September 2025</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled
                data-testid="rollback-button"
              >
                Rollback
              </Button>
            </div>
            <p className="text-sm text-gray-700">
              Category map finalized; B24/B30 split into A/B variants.
            </p>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Rollback functionality is currently disabled in this prototype. 
              In production, this would restore a previous schema version and recalculate all submissions.
            </AlertDescription>
          </Alert>
        </div>
      </CardContent>
    </Card>
  );
}

