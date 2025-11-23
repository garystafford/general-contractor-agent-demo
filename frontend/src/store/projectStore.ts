import { create } from 'zustand';
import type { Project, ProjectStatus, Task, Agent, AgentActivity } from '../types';

export interface ErrorDetail {
  type: 'missing_info' | 'configuration' | 'stuck_state';
  title: string;
  message: string;
  missingFields?: string[];
  blockedTasks?: string[];
  suggestions?: string[];
}

interface ProjectState {
  // Project state
  project: Project | null;
  projectStatus: ProjectStatus | null;
  tasks: Task[];
  agents: Agent[];
  agentActivity: AgentActivity | null;

  // UI state
  isLoading: boolean;
  error: string | null;
  selectedTask: Task | null;
  selectedAgent: string | null;
  errorModal: ErrorDetail | null;
  isErrorModalOpen: boolean;

  // Actions
  setProject: (project: Project) => void;
  setProjectStatus: (status: ProjectStatus) => void;
  setTasks: (tasks: Task[]) => void;
  updateTask: (task: Task) => void;
  setAgents: (agents: Agent[]) => void;
  setAgentActivity: (activity: AgentActivity) => void;
  setSelectedTask: (task: Task | null) => void;
  setSelectedAgent: (agentName: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  showErrorModal: (error: ErrorDetail) => void;
  closeErrorModal: () => void;
  reset: () => void;

  // Computed getters
  getTasksByPhase: () => Record<string, Task[]>;
  getTasksByAgent: () => Record<string, Task[]>;
  getCompletionPercentage: () => number;
  getActiveAgents: () => string[];
}

const initialState = {
  project: null,
  projectStatus: null,
  tasks: [],
  agents: [],
  agentActivity: null,
  isLoading: false,
  error: null,
  selectedTask: null,
  selectedAgent: null,
  errorModal: null,
  isErrorModalOpen: false,
};

export const useProjectStore = create<ProjectState>((set, get) => ({
  ...initialState,

  setProject: (project) => set({ project }),

  setProjectStatus: (status) => set({ projectStatus: status, project: status.project }),

  setTasks: (tasks) => set({ tasks }),

  updateTask: (updatedTask) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.task_id === updatedTask.task_id ? updatedTask : task
      ),
    })),

  setAgents: (agents) => set({ agents }),

  setAgentActivity: (activity) => set({ agentActivity: activity }),

  setSelectedTask: (task) => set({ selectedTask: task }),

  setSelectedAgent: (agentName) => set({ selectedAgent: agentName }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  showErrorModal: (error) => set({ errorModal: error, isErrorModalOpen: true }),

  closeErrorModal: () => set({ errorModal: null, isErrorModalOpen: false }),

  reset: () => set(initialState),

  // Computed getters
  getTasksByPhase: () => {
    const { tasks } = get();
    return tasks.reduce((acc, task) => {
      if (!acc[task.phase]) {
        acc[task.phase] = [];
      }
      acc[task.phase].push(task);
      return acc;
    }, {} as Record<string, Task[]>);
  },

  getTasksByAgent: () => {
    const { tasks } = get();
    return tasks.reduce((acc, task) => {
      if (!acc[task.agent]) {
        acc[task.agent] = [];
      }
      acc[task.agent].push(task);
      return acc;
    }, {} as Record<string, Task[]>);
  },

  getCompletionPercentage: () => {
    const { tasks } = get();
    if (tasks.length === 0) return 0;
    const completed = tasks.filter((t) => t.status === 'completed').length;
    return Math.round((completed / tasks.length) * 100);
  },

  getActiveAgents: () => {
    const { tasks } = get();
    const activeAgents = new Set<string>();
    tasks.forEach((task) => {
      if (task.status === 'in_progress') {
        activeAgents.add(task.agent);
      }
    });
    return Array.from(activeAgents);
  },
}));
