import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Download, Database, History, AlertCircle, Home } from 'lucide-react';
import {
  getAllSubmissions,
  getBaseline,
  setBaseline,
  clearBaseline,
  exportData
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getAllSubmissions();
      setSubmissions(data.submissions || []);
      setBaselineIdState(data.baseline);
    } catch (error) {
      console.error('Error loading submissions:', error);
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
                  <TableHead>Created</TableHead>
                  <TableHead>Adventure</TableHead>
                  <TableHead>Connection</TableHead>
                  <TableHead>Intensity</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Archetype</TableHead>
                  <TableHead>Baseline</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {submissions.map((sub) => (
                  <TableRow key={sub.id}>
                    <TableCell className="font-medium">{sub.name}</TableCell>
                    <TableCell>{new Date(sub.createdAt).toLocaleDateString()}</TableCell>
                    <TableCell>{sub.derived?.dials?.Adventure?.toFixed(0) || '-'}</TableCell>
                    <TableCell>{sub.derived?.dials?.Connection?.toFixed(0) || '-'}</TableCell>
                    <TableCell>{sub.derived?.dials?.Intensity?.toFixed(0) || '-'}</TableCell>
                    <TableCell>{sub.derived?.dials?.Confidence?.toFixed(0) || '-'}</TableCell>
                    <TableCell>{sub.derived?.archetypes?.[0]?.name || '-'}</TableCell>
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
                ))}
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
      const headers = ['Name', 'Created', 'Adventure', 'Connection', 'Intensity', 'Confidence', 'Top Archetype'];
      const rows = submissions.map(sub => [
        sub.name,
        new Date(sub.createdAt).toISOString(),
        sub.derived?.dials?.Adventure?.toFixed(0) || '',
        sub.derived?.dials?.Connection?.toFixed(0) || '',
        sub.derived?.dials?.Intensity?.toFixed(0) || '',
        sub.derived?.dials?.Confidence?.toFixed(0) || '',
        sub.derived?.archetypes?.[0]?.name || ''
      ]);
      
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

