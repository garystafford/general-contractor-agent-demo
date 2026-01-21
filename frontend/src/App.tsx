import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { ProjectForm } from './components/ProjectForm';
import { DashboardSimple } from './components/DashboardSimple';
import { HealthCheck } from './components/HealthCheck';
import { AgentNetworkGraph } from './components/AgentNetworkGraph';
import { ActivityMonitor } from './components/ActivityMonitor';
import { apiClient } from './api/client';
import { AlertCircle, Loader2 } from 'lucide-react';

function App() {
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    // Check backend health on app load
    const checkBackend = async () => {
      const healthy = await apiClient.healthCheck();
      setBackendHealthy(healthy);

      if (!healthy) {
        toast.error('Backend is not responding. Please start the backend server.', {
          duration: 10000,
          id: 'backend-health',
        });
      }
    };

    checkBackend();
  }, []);

  // Show loading state while checking backend
  if (backendHealthy === null) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600 dark:text-gray-400">Connecting to backend...</p>
        </div>
      </div>
    );
  }

  // Show error state if backend is down
  if (!backendHealthy) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-md text-center">
          <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Backend Unavailable
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            The backend server is not responding. Please ensure it's running at{' '}
            <code className="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded text-sm">
              http://localhost:8000
            </code>
          </p>
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 text-left text-sm">
            <p className="font-semibold text-gray-900 dark:text-white mb-2">To start the backend:</p>
            <code className="block bg-gray-800 text-green-400 p-3 rounded font-mono">
              python start.py
            </code>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectForm />} />
        <Route path="/dashboard" element={<DashboardSimple />} />
        <Route path="/activity" element={<ActivityMonitor />} />
        <Route path="/graph" element={<AgentNetworkGraph />} />
        <Route path="/health" element={<HealthCheck />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#333',
            color: '#fff',
          },
        }}
      />
    </BrowserRouter>
  );
}

export default App;
