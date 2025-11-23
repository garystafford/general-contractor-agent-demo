import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/projectStore';
import { apiClient } from '../api/client';
import { config } from '../config';
import toast from 'react-hot-toast';
import {
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
import ErrorModal from './ErrorModal';

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
    showErrorModal,
    closeErrorModal,
    errorModal,
    isErrorModalOpen,
  } = useProjectStore();

  const [isAutoRefreshing, setIsAutoRefreshing] = useState(false);
  const [stuckStateChecked, setStuckStateChecked] = useState<string>('');
  const [dashboardLoadTime] = useState<number>(Date.now());

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
    } catch (error) {
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
      console.log(`🔄 Auto-refreshing dashboard every ${config.uiRefreshIntervalMs}ms (tasks in progress)...`);
      const interval = setInterval(async () => {
        await fetchProjectData();
      }, config.uiRefreshIntervalMs);

      return () => {
        clearInterval(interval);
        setIsAutoRefreshing(false);
      };
    } else {
      setIsAutoRefreshing(false);
    }
  }, [projectStatus]);

  // Detect stuck state (dependency deadlock or failed tasks blocking progress)
  useEffect(() => {
    if (!projectStatus) return;

    const { in_progress, pending, failed, completion_percentage, completed } = projectStatus.task_status;

    // Create a unique key for the current status to detect when it changes
    const statusKey = `${in_progress}-${pending}-${failed}-${completion_percentage}`;

    // Don't check again if we already showed the modal for this exact state
    if (stuckStateChecked === statusKey) return;

    // GRACE PERIOD: Don't check for stuck state immediately after dashboard loads
    // Give tasks at least 15 seconds to start executing
    const timeElapsedMs = Date.now() - dashboardLoadTime;
    const GRACE_PERIOD_MS = 15000; // 15 seconds

    if (timeElapsedMs < GRACE_PERIOD_MS) {
      // Still in grace period - don't check yet
      return;
    }

    // ADDITIONAL CHECK: If no tasks have ever completed or failed, and we're in the grace period,
    // the project is likely still starting up - don't flag as stuck
    const hasAnyProgress = completed > 0 || failed > 0;
    if (!hasAnyProgress && timeElapsedMs < GRACE_PERIOD_MS * 2) {
      // Extended grace period if no progress yet (30 seconds total)
      return;
    }

    // Check if backend reported an error_details field (from execute_entire_project)
    if ((projectStatus as any).error_details) {
      const errorDetails = (projectStatus as any).error_details;
      setStuckStateChecked(statusKey);
      showErrorModal({
        type: errorDetails.type || 'stuck_state',
        title: errorDetails.title || 'Project Error',
        message: errorDetails.message || 'An error occurred during project execution',
        blockedTasks: errorDetails.blocked_tasks || errorDetails.blockedTasks,
        suggestions: errorDetails.suggestions || []
      });
      return;
    }

    // Detect stuck state scenarios:
    // 1. No tasks running + tasks pending + failed tasks exist = likely blocked by failed task
    // 2. No tasks running + tasks pending + project not complete = dependency deadlock
    const isStuck = in_progress === 0 && pending > 0 && completion_percentage < 100;
    const hasFailedTasks = failed > 0;

    if (isStuck) {
      setStuckStateChecked(statusKey);

      // Get blocked tasks from the tasks list
      const blockedTasks = tasks
        .filter(task => task.status === 'pending')
        .map(task => `${task.description} (assigned to ${task.agent})`);

      // Get failed tasks
      const failedTasksList = tasks
        .filter(task => task.status === 'failed')
        .map(task => task.description);

      let message = 'The project cannot proceed because tasks are waiting for dependencies that will never complete.';
      const suggestions = [
        'Check if all assigned agents are properly configured',
        'Consider resetting the project with more complete details'
      ];

      if (hasFailedTasks) {
        message = `${failed} task(s) failed, blocking ${pending} pending task(s) from executing.`;
        suggestions.unshift(`Retry or skip the failed task(s): ${failedTasksList.join(', ')}`);
      } else {
        suggestions.unshift('Some tasks may be missing required information');
      }

      showErrorModal({
        type: 'stuck_state',
        title: 'Project Execution Stuck',
        message,
        blockedTasks,
        suggestions
      });
    }
  }, [projectStatus, tasks, stuckStateChecked, showErrorModal]);

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset the project? All progress will be lost.')) {
      return;
    }

    try {
      await apiClient.resetProject();
      reset();
      closeErrorModal();
      setStuckStateChecked('');
      toast.success('Project reset successfully');
      navigate('/');
    } catch {
      toast.error('Failed to reset project');
    }
  };

  const handleResetFromModal = async () => {
    try {
      await apiClient.resetProject();
      reset();
      closeErrorModal();
      setStuckStateChecked('');
      toast.success('Project reset successfully');
      navigate('/');
    } catch {
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
    } catch {
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
    } catch {
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
    // Helper to normalize phase for comparison and return normalized phase name
    const normalizeAndGetPhase = (phase: string): { index: number; normalized: string } => {
      // Check if phase is already in PHASES
      if (PHASES.includes(phase)) {
        return { index: PHASES.indexOf(phase), normalized: phase };
      }

      // Map common variations to standard phases
      const phaseMap: Record<string, string> = {
        'construction': 'framing',
        'demolition': 'framing',
        'build': 'framing',
        'install': 'finishing',
        'interior': 'finishing',
        'exterior': 'finishing',
      };

      const normalized = phaseMap[phase] || 'planning';
      return { index: PHASES.indexOf(normalized), normalized };
    };

    // If project is 100% complete, show final_inspection as completed
    if (task_status.completion_percentage >= 100) {
      return 'final_inspection';
    }

    // Find the furthest phase among in-progress tasks
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
    if (inProgressTasks.length > 0) {
      let maxPhaseIndex = -1;
      let maxPhaseNormalized = 'planning';

      inProgressTasks.forEach(task => {
        const { index, normalized } = normalizeAndGetPhase(task.phase);
        if (index > maxPhaseIndex) {
          maxPhaseIndex = index;
          maxPhaseNormalized = normalized;
        }
      });

      return maxPhaseNormalized;
    }

    // Find the furthest phase among completed tasks
    const completedTasks = tasks.filter(t => t.status === 'completed');
    if (completedTasks.length > 0) {
      let maxPhaseIndex = -1;
      let maxPhaseNormalized = 'planning';

      completedTasks.forEach(task => {
        const { index, normalized } = normalizeAndGetPhase(task.phase);
        if (index > maxPhaseIndex) {
          maxPhaseIndex = index;
          maxPhaseNormalized = normalized;
        }
      });

      return maxPhaseNormalized;
    }

    // Find the furthest phase among ready tasks
    const readyTasks = tasks.filter(t => t.status === 'ready');
    if (readyTasks.length > 0) {
      let maxPhaseIndex = -1;
      let maxPhaseNormalized = 'planning';

      readyTasks.forEach(task => {
        const { index, normalized } = normalizeAndGetPhase(task.phase);
        if (index > maxPhaseIndex) {
          maxPhaseIndex = index;
          maxPhaseNormalized = normalized;
        }
      });

      return maxPhaseNormalized;
    }

    return 'planning';
  };

  const actualPhase = getActualPhase();

  // Map phase to closest standard phase if not found
  const normalizePhase = (phase: string): string => {
    // Handle exact matches
    if (PHASES.includes(phase)) return phase;

    // Map common variations
    const phaseMap: Record<string, string> = {
      'construction': 'framing',
      'demolition': 'framing',
      'build': 'framing',
      'install': 'finishing',
      'interior': 'finishing',
      'exterior': 'finishing',
    };

    return phaseMap[phase] || 'planning';
  };

  const normalizedPhase = normalizePhase(actualPhase);
  // When project is 100% complete, set phase index beyond array so all phases show as completed (green)
  const currentPhaseIndex = task_status.completion_percentage >= 100
    ? PHASES.length
    : PHASES.indexOf(normalizedPhase);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Auto-refresh indicator */}
        {isAutoRefreshing && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin" />
            <span className="text-sm text-blue-900 dark:text-blue-100">
              🔴 LIVE - Refreshing every {config.uiRefreshIntervalMs / 1000} second{config.uiRefreshIntervalMs !== 1000 ? 's' : ''} | Last update: {new Date().toLocaleTimeString()}
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
              {actualPhase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
            <span>Final Inspection</span>
          </div>
        </div>

        {/* Autonomous Execution Status */}
        {task_status.in_progress === 0 && task_status.pending > 0 && task_status.completion_percentage < 100 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-400 dark:border-blue-600 rounded-lg p-6">
            <h3 className="text-lg font-bold text-blue-900 dark:text-blue-100 mb-2">
              🤖 Autonomous Execution in Progress
            </h3>
            <p className="text-blue-800 dark:text-blue-200">
              {task_status.pending} tasks waiting for dependencies. The system is running autonomously and will execute tasks as they become ready.
            </p>
          </div>
        )}

        {/* Project Complete */}
        {task_status.completion_percentage >= 100 && (
          <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-400 dark:border-green-600 rounded-lg p-6">
            <h3 className="text-lg font-bold text-green-900 dark:text-green-100 mb-2">
              ✅ Project Complete!
            </h3>
            <p className="text-green-800 dark:text-green-200">
              All tasks have been completed successfully. You can reset to start a new project.
            </p>
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
              {tasks.filter(t => t.status === 'ready').length} queued · {' '}
              {tasks.filter(t => t.status === 'pending').length} pending · {' '}
              {tasks.filter(t => t.status === 'blocked').length} blocked
            </div>
          </div>
          <div className="space-y-2 max-h-[600px] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-4"
               style={{ scrollbarWidth: 'thin' }}>
            {/* In Progress - Show first with animation */}
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

            {/* Ready - Dependencies met, ready to execute */}
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

            {/* Pending - Waiting for dependencies */}
            {tasks
              .filter(t => t.status === 'pending')
              .map(task => (
                <div key={task.task_id} className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-900/20 rounded-lg border border-gray-200 dark:border-gray-700">
                  <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {task.agent} - Pending
                    </p>
                    <p className="text-xs text-gray-700 dark:text-gray-300">
                      {task.description}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 bg-gray-600 text-white rounded">
                    Waiting
                  </span>
                </div>
              ))}

            {/* Blocked - Dependencies cannot be met */}
            {tasks
              .filter(t => t.status === 'blocked')
              .map(task => (
                <div key={task.task_id} className="flex items-center space-x-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                  <AlertCircle className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
                      {task.agent} - Blocked
                    </p>
                    <p className="text-xs text-purple-700 dark:text-purple-300">
                      {task.description}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 bg-purple-600 text-white rounded">
                    Blocked
                  </span>
                </div>
              ))}

            {/* Completed - Show in reverse order (most recent first) */}
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

            {/* Failed - Show last with error handling options */}
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
          </div>
        </div>
      </div>

      {/* Error Modal for Stuck States */}
      <ErrorModal
        isOpen={isErrorModalOpen}
        onClose={closeErrorModal}
        error={errorModal}
        onReset={handleResetFromModal}
      />
    </div>
  );
}
