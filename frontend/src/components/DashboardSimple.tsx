import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/projectStore';
import { apiClient } from '../api/client';
import toast from 'react-hot-toast';
import {
  Play,
  SkipForward,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  ArrowLeft,
  RefreshCw,
  XCircle,
  RefreshCcw,
} from 'lucide-react';

const PHASES = [
  'planning',
  'permitting',
  'foundation',
  'framing',
  'rough_in',
  'inspection',
  'finishing',
  'final_inspection',
];

export function DashboardSimple() {
  const navigate = useNavigate();
  const {
    projectStatus,
    tasks,
    setProjectStatus,
    setTasks,
    reset,
  } = useProjectStore();

  const [isExecuting, setIsExecuting] = useState(false);
  const [executionMode, setExecutionMode] = useState<'next' | 'all' | null>(null);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(false);

  // Fetch project data
  const fetchProjectData = async () => {
    try {
      const [status, tasks] = await Promise.all([
        apiClient.getProjectStatus(),
        apiClient.getTasks(),
      ]);
      setProjectStatus(status);
      setTasks(tasks);
      return status;
    } catch (error: any) {
      console.error('Failed to load project data:', error);
      return null;
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      const status = await fetchProjectData();
      if (!status) {
        toast.error('Failed to load project data');
        navigate('/');
      }
    };
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-refresh while tasks are in progress
  useEffect(() => {
    if (!projectStatus) return;

    const hasTasksInProgress = projectStatus.task_status.in_progress > 0;
    const isNotComplete = projectStatus.task_status.completion_percentage < 100;

    if (hasTasksInProgress || isNotComplete) {
      setIsAutoRefreshing(true);
      console.log('🔄 Auto-refreshing dashboard (tasks in progress)...');
      const interval = setInterval(async () => {
        await fetchProjectData();
      }, 1000); // Refresh every 1 second for faster updates

      return () => {
        clearInterval(interval);
        setIsAutoRefreshing(false);
      };
    } else {
      setIsAutoRefreshing(false);
    }
  }, [projectStatus]);

  const handleExecuteNextPhase = async () => {
    if (isExecuting) {
      toast.error('Already executing - please wait');
      return;
    }

    setIsExecuting(true);
    setExecutionMode('next');

    try {
      toast.loading('Executing next phase...', { id: 'execute-next' });
      await apiClient.executeNextPhase();
      toast.success('Phase execution started', { id: 'execute-next' });

      // Refresh status immediately
      await fetchProjectData();
    } catch (error: any) {
      const msg = error.message || 'Failed to execute phase - is backend running?';
      toast.error(msg, { id: 'execute-next' });
      console.error('Execute next phase error:', error);
    } finally {
      setIsExecuting(false);
      setExecutionMode(null);
    }
  };

  const handleExecuteAll = async () => {
    if (isExecuting) {
      toast.error('Already executing - please wait');
      return;
    }

    setIsExecuting(true);
    setExecutionMode('all');

    try {
      const executePromise = apiClient.executeAll().then(async () => {
        await fetchProjectData();
      });

      await toast.promise(executePromise, {
        loading: 'Executing entire project... This may take several minutes.',
        success: 'Project execution completed!',
        error: (err) => `Failed: ${err.message || 'Is backend running?'}`,
      });
    } catch (error: any) {
      console.error('Execute all error:', error);
    } finally {
      setIsExecuting(false);
      setExecutionMode(null);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset the project? All progress will be lost.')) {
      return;
    }

    try {
      await apiClient.resetProject();
      reset();
      toast.success('Project reset successfully');
      navigate('/');
    } catch (error: any) {
      toast.error('Failed to reset project');
    }
  };

  const handleSkipTask = async (taskId: string, taskDescription: string) => {
    if (!confirm(`Skip this task?\n\n"${taskDescription}"\n\nThis will mark it as completed so dependent tasks can proceed.`)) {
      return;
    }

    try {
      await apiClient.skipTask(taskId);
      toast.success('Task skipped - dependent tasks can now proceed');
      await fetchProjectData();
    } catch (error: any) {
      toast.error('Failed to skip task');
    }
  };

  const handleRetryTask = async (taskId: string, taskDescription: string) => {
    if (!confirm(`Retry this task?\n\n"${taskDescription}"\n\nThis will reset and re-execute the task.`)) {
      return;
    }

    try {
      await apiClient.retryTask(taskId);
      toast.success('Task reset - retrying now...');
      await fetchProjectData();
    } catch (error: any) {
      toast.error('Failed to retry task');
    }
  };

  if (!projectStatus) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600 dark:text-gray-400">Loading project...</p>
        </div>
      </div>
    );
  }

  const { task_status, project: projectData } = projectStatus;

  // Calculate ACTUAL construction phase from tasks, not project status
  const getActualPhase = () => {
    // Find the phase of tasks currently in progress
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
    if (inProgressTasks.length > 0) {
      return inProgressTasks[0].phase;
    }

    // Find the phase of the last completed task
    const completedTasks = tasks.filter(t => t.status === 'completed');
    if (completedTasks.length > 0) {
      return completedTasks[completedTasks.length - 1].phase;
    }

    // Find the phase of ready tasks
    const readyTasks = tasks.filter(t => t.status === 'ready');
    if (readyTasks.length > 0) {
      return readyTasks[0].phase;
    }

    return 'planning';
  };

  const actualPhase = getActualPhase();
  const currentPhaseIndex = PHASES.indexOf(actualPhase);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Auto-refresh indicator */}
        {isAutoRefreshing && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin" />
            <span className="text-sm text-blue-900 dark:text-blue-100">
              🔴 LIVE - Refreshing every 1 second | Last update: {new Date().toLocaleTimeString()}
            </span>
            <button
              onClick={fetchProjectData}
              className="ml-auto text-xs px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition"
            >
              Refresh Now
            </button>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate('/')}
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white mb-4 transition"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Form</span>
            </button>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Project Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {projectData.description}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={fetchProjectData}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition"
              title="Manually refresh data from backend"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={handleExecuteNextPhase}
              disabled={isExecuting || task_status.completion_percentage >= 100}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition"
            >
              <SkipForward className="w-4 h-4" />
              <span>Next Phase</span>
            </button>
            <button
              onClick={handleExecuteAll}
              disabled={isExecuting || task_status.completion_percentage >= 100}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition"
            >
              <Play className="w-4 h-4" />
              <span>Execute All</span>
            </button>
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Completion</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {task_status.completion_percentage.toFixed(1)}%
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">In Progress</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {task_status.in_progress}
                </p>
              </div>
              <Clock className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {task_status.completed} / {task_status.total_tasks}
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {task_status.failed}
                </p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        {/* Phase Progress */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Construction Phases
          </h2>
          <div className="flex items-center space-x-2">
            {PHASES.map((phase, index) => (
              <div
                key={phase}
                className={`flex-1 h-2 rounded-full transition-all duration-300 ${
                  index < currentPhaseIndex
                    ? 'bg-green-500'
                    : index === currentPhaseIndex
                    ? 'bg-blue-500'
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
                title={phase}
              />
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-600 dark:text-gray-400">
            <span>Planning</span>
            <span className="font-semibold text-blue-600 dark:text-blue-400 capitalize">
              {actualPhase.replace('_', ' ')}
            </span>
            <span>Final Inspection</span>
          </div>
        </div>

        {/* Action Prompt */}
        {task_status.in_progress === 0 && task_status.pending > 0 && (
          <div className="bg-orange-50 dark:bg-orange-900/20 border-2 border-orange-400 dark:border-orange-600 rounded-lg p-6">
            <h3 className="text-lg font-bold text-orange-900 dark:text-orange-100 mb-2">
              ⚠️ Project Paused - Action Required!
            </h3>
            <p className="text-orange-800 dark:text-orange-200 mb-4">
              {task_status.pending} tasks are waiting to be executed. Click one of the buttons above to continue:
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleExecuteNextPhase}
                className="flex items-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-semibold"
              >
                <SkipForward className="w-4 h-4" />
                <span>Execute Next Phase</span>
              </button>
              <button
                onClick={handleExecuteAll}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold"
              >
                <Play className="w-4 h-4" />
                <span>Execute All Remaining Tasks</span>
              </button>
            </div>
          </div>
        )}

        {/* Live Activity Feed */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              🔴 Live Activity Feed
            </h2>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {tasks.filter(t => t.status === 'in_progress').length} active · {' '}
              {tasks.filter(t => t.status === 'failed').length} failed · {' '}
              {tasks.filter(t => t.status === 'completed').length} completed · {' '}
              {tasks.filter(t => t.status === 'ready').length} queued
            </div>
          </div>
          <div className="space-y-2 max-h-[600px] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-4"
               style={{ scrollbarWidth: 'thin' }}>
            {tasks
              .filter(t => t.status === 'in_progress')
              .map(task => (
                <div key={task.task_id} className="flex items-center space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 animate-pulse">
                  <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      {task.agent} is working...
                    </p>
                    <p className="text-xs text-blue-700 dark:text-blue-300">
                      {task.description}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 bg-blue-600 text-white rounded">
                    {task.phase}
                  </span>
                </div>
              ))}

            {tasks
              .filter(t => t.status === 'failed')
              .map(task => (
                <div key={task.task_id} className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border-2 border-red-300 dark:border-red-700">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-red-900 dark:text-red-100">
                      {task.agent} FAILED
                    </p>
                    <p className="text-xs text-red-700 dark:text-red-300 mb-2">
                      {task.description}
                    </p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleSkipTask(task.task_id, task.description)}
                        className="flex items-center space-x-1 px-2 py-1 text-xs bg-orange-600 hover:bg-orange-700 text-white rounded transition"
                        title="Skip this task and allow dependent tasks to proceed"
                      >
                        <XCircle className="w-3 h-3" />
                        <span>Skip</span>
                      </button>
                      <button
                        onClick={() => handleRetryTask(task.task_id, task.description)}
                        className="flex items-center space-x-1 px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition"
                        title="Retry this task"
                      >
                        <RefreshCcw className="w-3 h-3" />
                        <span>Retry</span>
                      </button>
                    </div>
                  </div>
                  <span className="text-xs px-2 py-1 bg-red-600 text-white rounded">
                    ERROR
                  </span>
                </div>
              ))}

            {tasks
              .filter(t => t.status === 'completed')
              .reverse()
              .map(task => (
                <div key={task.task_id} className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-green-900 dark:text-green-100">
                      {task.agent} completed
                    </p>
                    <p className="text-xs text-green-700 dark:text-green-300">
                      {task.description}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 bg-green-600 text-white rounded">
                    ✓
                  </span>
                </div>
              ))}

            {tasks
              .filter(t => t.status === 'ready')
              .map(task => (
                <div key={task.task_id} className="flex items-center space-x-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                  <Clock className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                      {task.agent} - Queued
                    </p>
                    <p className="text-xs text-yellow-700 dark:text-yellow-300">
                      {task.description}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 bg-yellow-600 text-white rounded">
                    Next
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Status Message */}
        {isExecuting && (
          <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>
              {executionMode === 'all'
                ? 'Executing entire project...'
                : 'Executing next phase...'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
