// Project Types
export interface Project {
  description: string;
  type: string;
  parameters: Record<string, any>;
  start_time: string | null;
  status: string;
  planning_method: 'template' | 'dynamic';
}

export interface ProjectRequest {
  description: string;
  project_type: string;
  parameters?: Record<string, any>;
  use_dynamic_planning?: boolean;
}

export interface TaskBreakdown {
  by_phase: Record<string, Task[]>;
  by_agent: Record<string, number>;
}

export interface ProjectStartResponse {
  status: string;
  message: string;
  project: Project;
  total_tasks: number;
  task_breakdown: TaskBreakdown;
}

// Task Types
export type TaskStatus = 'pending' | 'ready' | 'in_progress' | 'completed' | 'failed' | 'blocked';
export type Phase = 'planning' | 'permitting' | 'foundation' | 'framing' | 'rough_in' | 'inspection' | 'finishing' | 'final_inspection';

export interface Task {
  task_id: string;
  agent: string;
  description: string;
  status: TaskStatus;
  phase: Phase;
  dependencies: string[];
  result?: any;
}

// Agent Types
export interface Agent {
  name: string;
  status: 'available' | 'busy';
  tools: string[];
}

export interface AgentActivity {
  active_agents: Record<string, {
    task_id: string;
    description: string;
    phase: string;
  }>;
  total_agents: number;
  busy_count: number;
}

// Token Usage Types
export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface TokenUsageSummary {
  project_totals: TokenUsage;
  by_agent: Record<string, TokenUsage>;
  by_task: Record<string, TokenUsage>;
}

// Project Status Types
export interface TaskStatusSummary {
  total_tasks: number;
  completed: number;
  failed: number;
  in_progress: number;
  pending: number;
  completion_percentage: number;
}

export interface ProjectStatus {
  project: Project;
  phase: string;
  task_status: TaskStatusSummary;
  agents: string[];
  token_usage?: TokenUsageSummary;
}

// Materials Types
export interface Material {
  material_id: string;
  name: string;
  category: string;
  unit: string;
  price_per_unit: number;
  stock_quantity: number;
}

export interface MaterialOrder {
  material_id: string;
  quantity: number;
}

export interface Order {
  order_id: string;
  items: Array<{
    material_id: string;
    material_name: string;
    quantity: number;
    unit_price: number;
    subtotal: number;
  }>;
  total_cost: number;
  status: string;
  order_date: string;
}

// Permit Types
export type PermitType = 'building' | 'electrical' | 'plumbing' | 'mechanical' | 'demolition' | 'roofing';
export type PermitStatus = 'pending' | 'under_review' | 'approved' | 'rejected';
export type InspectionStatus = 'scheduled' | 'passed' | 'failed' | 'cancelled';

export interface Permit {
  permit_id: string;
  permit_type: PermitType;
  project_address: string;
  project_description: string;
  applicant: string;
  status: PermitStatus;
  application_date: string;
  review_date?: string;
  approval_date?: string;
  rejection_reason?: string;
}

export interface Inspection {
  inspection_id: string;
  permit_id: string;
  inspection_type: string;
  scheduled_date: string;
  status: InspectionStatus;
  inspector?: string;
  notes?: string;
  failed_items?: string[];
}

// WebSocket Message Types
export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
}

export interface ProjectStatusMessage extends WebSocketMessage<ProjectStatus> {
  type: 'project_status';
}

export interface TaskUpdateMessage extends WebSocketMessage<Task> {
  type: 'task_update';
}

export interface TasksListMessage extends WebSocketMessage<Task[]> {
  type: 'tasks_list';
}

export interface AgentActivityMessage extends WebSocketMessage<AgentActivity> {
  type: 'agent_activity';
}

// API Response Types
export interface APIResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  detail?: string;
}
