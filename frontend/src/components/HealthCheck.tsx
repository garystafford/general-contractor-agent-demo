import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, XCircle, AlertCircle, RefreshCw, ArrowLeft, Activity } from 'lucide-react';
import { config } from '../config';

interface ComponentHealth {
  status: string;
  details?: string;
  error?: string;
  tools?: string[];
  agents?: string[];
}

interface HealthReport {
  timestamp: string;
  overall_status: string;
  components: {
    backend_api?: ComponentHealth;
    mcp_services?: {
      materials: ComponentHealth;
      permitting: ComponentHealth;
      initialized: boolean;
      error?: string;
    };
    task_manager?: ComponentHealth;
    agents?: ComponentHealth;
  };
  error?: string;
}

export function HealthCheck() {
  const navigate = useNavigate();
  const [healthData, setHealthData] = useState<HealthReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${config.apiUrl}/api/health/detailed`);
      const result = await response.json();

      if (result.status === 'success') {
        setHealthData(result.data);
        setLastChecked(new Date());
      } else {
        setError('Failed to fetch health data');
      }
    } catch (err) {
      setError('Cannot connect to backend API');
      console.error('Health check error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
      case 'healthy':
        return <CheckCircle2 className="w-6 h-6 text-green-500" />;
      case 'down':
      case 'unhealthy':
        return <XCircle className="w-6 h-6 text-red-500" />;
      case 'degraded':
        return <AlertCircle className="w-6 h-6 text-yellow-500" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up':
      case 'healthy':
        return 'bg-green-50 border-green-200';
      case 'down':
      case 'unhealthy':
        return 'bg-red-50 border-red-200';
      case 'degraded':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'up':
        return 'Operational';
      case 'down':
        return 'Down';
      case 'healthy':
        return 'Healthy';
      case 'unhealthy':
        return 'Unhealthy';
      case 'degraded':
        return 'Degraded';
      default:
        return status;
    }
  };

  if (error && !healthData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
              Back
            </button>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-red-900 mb-2">Backend Unavailable</h2>
            <p className="text-red-700">{error}</p>
            <button
              onClick={fetchHealth}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
              Back
            </button>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              <Activity className="w-8 h-8" />
              System Health Status
            </h1>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {healthData && (
          <>
            {/* Overall Status */}
            <div className={`rounded-lg border-2 p-6 mb-6 ${getStatusColor(healthData.overall_status)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {getStatusIcon(healthData.overall_status)}
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      System Status: {getStatusText(healthData.overall_status)}
                    </h2>
                    <p className="text-sm text-gray-600">
                      Last checked: {new Date(lastChecked).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Components Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Backend API */}
              {healthData.components.backend_api && (
                <div className={`rounded-lg border p-6 ${getStatusColor(healthData.components.backend_api.status)}`}>
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Backend API</h3>
                    {getStatusIcon(healthData.components.backend_api.status)}
                  </div>
                  <p className="text-sm text-gray-700">{healthData.components.backend_api.details}</p>
                  {healthData.components.backend_api.error && (
                    <p className="text-sm text-red-700 mt-2">Error: {healthData.components.backend_api.error}</p>
                  )}
                </div>
              )}

              {/* Task Manager */}
              {healthData.components.task_manager && (
                <div className={`rounded-lg border p-6 ${getStatusColor(healthData.components.task_manager.status)}`}>
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Task Manager</h3>
                    {getStatusIcon(healthData.components.task_manager.status)}
                  </div>
                  <p className="text-sm text-gray-700">{healthData.components.task_manager.details}</p>
                  {healthData.components.task_manager.error && (
                    <p className="text-sm text-red-700 mt-2">Error: {healthData.components.task_manager.error}</p>
                  )}
                </div>
              )}

              {/* Agents */}
              {healthData.components.agents && (
                <div className={`rounded-lg border p-6 ${getStatusColor(healthData.components.agents.status)}`}>
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Agents</h3>
                    {getStatusIcon(healthData.components.agents.status)}
                  </div>
                  <p className="text-sm text-gray-700 mb-2">{healthData.components.agents.details}</p>
                  {healthData.components.agents.agents && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {healthData.components.agents.agents.map((agent) => (
                        <span
                          key={agent}
                          className="px-2 py-1 bg-white border border-gray-300 rounded text-xs font-medium text-gray-700"
                        >
                          {agent}
                        </span>
                      ))}
                    </div>
                  )}
                  {healthData.components.agents.error && (
                    <p className="text-sm text-red-700 mt-2">Error: {healthData.components.agents.error}</p>
                  )}
                </div>
              )}

              {/* MCP Services - Materials */}
              {healthData.components.mcp_services?.materials && (
                <div className={`rounded-lg border p-6 ${getStatusColor(healthData.components.mcp_services.materials.status)}`}>
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">MCP Materials Server</h3>
                    {getStatusIcon(healthData.components.mcp_services.materials.status)}
                  </div>
                  <p className="text-sm text-gray-700">{healthData.components.mcp_services.materials.details}</p>
                  {healthData.components.mcp_services.materials.tools && (
                    <div className="mt-3">
                      <p className="text-xs font-semibold text-gray-600 mb-1">Available Tools:</p>
                      <div className="flex flex-wrap gap-1">
                        {healthData.components.mcp_services.materials.tools.map((tool) => (
                          <span
                            key={tool}
                            className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-700"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {healthData.components.mcp_services.materials.error && (
                    <p className="text-sm text-red-700 mt-2">{healthData.components.mcp_services.materials.details}</p>
                  )}
                </div>
              )}

              {/* MCP Services - Permitting */}
              {healthData.components.mcp_services?.permitting && (
                <div className={`rounded-lg border p-6 ${getStatusColor(healthData.components.mcp_services.permitting.status)}`}>
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">MCP Permitting Server</h3>
                    {getStatusIcon(healthData.components.mcp_services.permitting.status)}
                  </div>
                  <p className="text-sm text-gray-700">{healthData.components.mcp_services.permitting.details}</p>
                  {healthData.components.mcp_services.permitting.tools && (
                    <div className="mt-3">
                      <p className="text-xs font-semibold text-gray-600 mb-1">Available Tools:</p>
                      <div className="flex flex-wrap gap-1">
                        {healthData.components.mcp_services.permitting.tools.map((tool) => (
                          <span
                            key={tool}
                            className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-700"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {healthData.components.mcp_services.permitting.error && (
                    <p className="text-sm text-red-700 mt-2">{healthData.components.mcp_services.permitting.details}</p>
                  )}
                </div>
              )}
            </div>

            {/* MCP Initialization Status */}
            {healthData.components.mcp_services && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>MCP Services Initialized:</strong>{' '}
                  {healthData.components.mcp_services.initialized ? 'Yes' : 'No'}
                </p>
                {healthData.components.mcp_services.error && (
                  <p className="text-sm text-red-700 mt-2">
                    <strong>Initialization Error:</strong> {healthData.components.mcp_services.error}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
