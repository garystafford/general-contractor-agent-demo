import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/projectStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiClient } from '../api/client';
import { AgentGraph } from './AgentGraph';
import { config } from '../config';
import toast from 'react-hot-toast';
import {
  Play,
  SkipForward,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
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

export function Dashboard() {
  const navigate = useNavigate();
  const {
    project,
    projectStatus,
    setProjectStatus,
    setTasks,
    updateTask,
    reset,
  } = useProjectStore();

  const [isExecuting, setIsExecuting] = useState(false);
  const [executionMode, setExecutionMode] = useState<'next' | 'all' | null>(null);

  // Handle WebSocket messages
  const handleProjectUpdate = (message: any) => {
    if (message.type === 'project_status') {
      setProjectStatus(message.data);
    }
  };

  const handleTaskUpdate = (message: any) => {
    if (message.type === 'task_update') {
      updateTask(message.data);
    } else if (message.type === 'tasks_list') {
      setTasks(message.data);
    }
  };

  // Connect to WebSockets
  useWebSocket({
    url: `${config.wsUrl}/ws/project-updates`,
    onMessage: handleProjectUpdate,
  });

  useWebSocket({
    url: `${config.wsUrl}/ws/task-updates`,
    onMessage: handleTaskUpdate,
  });

  // Fetch initial data
  useEffect(() => {
    if (!project) {
      navigate('/');
      return;
    }

    const fetchInitialData = async () => {
      try {
        const [status, tasks] = await Promise.all([
          apiClient.getProjectStatus(),
          apiClient.getTasks(),
        ]);
        setProjectStatus(status);
        setTasks(tasks);
      } catch {
        toast.error('Failed to load project data');
      }
    };

    fetchInitialData();
  }, [project, navigate, setProjectStatus, setTasks]);

  const handleExecuteNextPhase = async () => {
    setIsExecuting(true);
    setExecutionMode('next');

    try {
      await apiClient.executeNextPhase();
      toast.success('Phase execution started');
    } catch (error: any) {
      toast.error(error.message || 'Failed to execute phase');
    } finally {
      setTimeout(() => {
        setIsExecuting(false);
        setExecutionMode(null);
      }, 2000);
    }
  };

  const handleExecuteAll = async () => {
    setIsExecuting(true);
    setExecutionMode('all');

    try {
      toast.promise(
        apiClient.executeAll(),
        {
          loading: 'Executing entire project...',
          success: 'Project execution completed!',
          error: 'Failed to execute project',
        }
      );
    } catch {
      // Error handled by toast.promise
    } finally {
      setTimeout(() => {
        setIsExecuting(false);
        setExecutionMode(null);
      }, 1000);
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
    } catch {
      toast.error('Failed to reset project');
    }
  };

  if (!projectStatus) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const { task_status } = projectStatus;
  const currentPhaseIndex = PHASES.indexOf(projectStatus.phase);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Project Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {project?.description}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleExecuteNextPhase}
              disabled={isExecuting || task_status.completion_percentage === 100}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition"
            >
              <SkipForward className="w-4 h-4" />
              <span>Next Phase</span>
            </button>
            <button
              onClick={handleExecuteAll}
              disabled={isExecuting || task_status.completion_percentage === 100}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition"
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
                  {task_status.completion_percentage}%
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
            <span className="font-semibold text-blue-600 dark:text-blue-400">
              {projectStatus.phase}
            </span>
            <span>Final Inspection</span>
          </div>
        </div>

        {/* Agent Collaboration Graph */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Agent Collaboration Network
          </h2>
          <AgentGraph />
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
