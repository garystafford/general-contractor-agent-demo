import { useEffect } from 'react';
import { useProjectStore } from '../store/projectStore';
import { apiClient } from '../api/client';
import type { Task, TaskStatus } from '../types';
import { CheckCircle2, Circle, Clock, XCircle, AlertTriangle } from 'lucide-react';

const STATUS_COLUMNS: { status: TaskStatus; label: string; color: string }[] = [
  { status: 'pending', label: 'Pending', color: 'gray' },
  { status: 'ready', label: 'Ready', color: 'yellow' },
  { status: 'in_progress', label: 'In Progress', color: 'blue' },
  { status: 'completed', label: 'Completed', color: 'green' },
  { status: 'failed', label: 'Failed', color: 'red' },
];

const STATUS_ICONS = {
  pending: Circle,
  ready: Clock,
  in_progress: Clock,
  completed: CheckCircle2,
  failed: XCircle,
  blocked: AlertTriangle,
};

const STATUS_COLORS = {
  pending: 'text-gray-500 bg-gray-100 dark:bg-gray-700',
  ready: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30',
  in_progress: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
  completed: 'text-green-600 bg-green-100 dark:bg-green-900/30',
  failed: 'text-red-600 bg-red-100 dark:bg-red-900/30',
  blocked: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30',
};

function TaskCard({ task }: { task: Task }) {
  const Icon = STATUS_ICONS[task.status];
  const colorClass = STATUS_COLORS[task.status];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 hover:shadow-md transition cursor-pointer">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
          {task.agent}
        </div>
        <Icon className={`w-4 h-4 ${colorClass.split(' ')[0]}`} />
      </div>

      {/* Description */}
      <p className="text-sm text-gray-900 dark:text-white font-medium mb-2">
        {task.description}
      </p>

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span className="capitalize">{task.phase}</span>
        <span>#{task.task_id}</span>
      </div>

      {/* Dependencies */}
      {task.dependencies.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Depends on: {task.dependencies.join(', ')}
          </p>
        </div>
      )}
    </div>
  );
}

export function TaskBoard() {
  const { tasks, setTasks } = useProjectStore();

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const fetchedTasks = await apiClient.getTasks();
        setTasks(fetchedTasks);
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      }
    };

    fetchTasks();
  }, [setTasks]);

  const getTasksByStatus = (status: TaskStatus): Task[] => {
    return tasks.filter((task) => task.status === status);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          Task Board
        </h1>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {STATUS_COLUMNS.map(({ status, label, color }) => {
            const columnTasks = getTasksByStatus(status);

            return (
              <div key={status} className="flex flex-col">
                {/* Column Header */}
                <div className={`bg-${color}-100 dark:bg-${color}-900/30 rounded-t-lg p-4 border-b-4 border-${color}-500`}>
                  <div className="flex items-center justify-between">
                    <h2 className={`font-semibold text-${color}-900 dark:text-${color}-100`}>
                      {label}
                    </h2>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium bg-${color}-200 dark:bg-${color}-800 text-${color}-900 dark:text-${color}-100`}>
                      {columnTasks.length}
                    </span>
                  </div>
                </div>

                {/* Column Content */}
                <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-b-lg p-4 space-y-3 min-h-[400px] max-h-[600px] overflow-y-auto">
                  {columnTasks.length === 0 ? (
                    <div className="text-center text-gray-400 dark:text-gray-600 py-8">
                      No tasks
                    </div>
                  ) : (
                    columnTasks.map((task) => <TaskCard key={task.task_id} task={task} />)
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary */}
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Task Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {STATUS_COLUMNS.map(({ status, label }) => {
              const count = getTasksByStatus(status).length;
              return (
                <div key={status} className="text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
