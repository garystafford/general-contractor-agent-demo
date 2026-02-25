import axios, { type AxiosInstance } from 'axios';
import type {
  ProjectRequest,
  ProjectStartResponse,
  ProjectStatus,
  Task,
  Agent,
  Material,
  MaterialOrder,
  Order,
  Permit,
  Inspection,
  APIResponse,
  TokenUsageSummary,
} from '../types';
import { config } from '../config';

class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = config.apiUrl) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 300000, // 5 minutes for long-running operations
    });
  }

  // Health Check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health', { timeout: 5000 });
      return response.data.status === 'healthy';
    } catch {
      return false;
    }
  }

  // Project Management
  async startProject(request: ProjectRequest): Promise<ProjectStartResponse> {
    const response = await this.client.post<APIResponse<ProjectStartResponse>>(
      '/api/projects/start',
      request
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to start project');
    }
    return response.data.data!;
  }

  async executeNextPhase(): Promise<any> {
    const response = await this.client.post<APIResponse<any>>('/api/projects/execute-next-phase');
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to execute next phase');
    }
    return response.data.data!;
  }

  async executeAll(): Promise<any> {
    const response = await this.client.post<APIResponse<any>>('/api/projects/execute-all');
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to execute project');
    }
    return response.data.data!;
  }

  async getProjectStatus(): Promise<ProjectStatus> {
    const response = await this.client.get<APIResponse<ProjectStatus>>('/api/projects/status');
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get project status');
    }
    return response.data.data!;
  }

  async resetProject(): Promise<void> {
    const response = await this.client.post<APIResponse<void>>('/api/projects/reset');
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to reset project');
    }
  }

  // Agent Management
  async getAgents(): Promise<string[]> {
    const response = await this.client.get<APIResponse<{ agents: string[]; total: number }>>(
      '/api/agents'
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get agents');
    }
    return response.data.data!.agents;
  }

  async getAgentStatus(agentName: string): Promise<Agent> {
    const response = await this.client.get<APIResponse<Agent>>(`/api/agents/${agentName}`);
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get agent status');
    }
    return response.data.data!;
  }

  async getAllAgentsStatus(): Promise<Agent[]> {
    const response = await this.client.get<APIResponse<Agent[]>>('/api/agents/status');
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get agents status');
    }
    return response.data.data!;
  }

  // Task Management
  async getTasks(): Promise<Task[]> {
    const response = await this.client.get<APIResponse<{ tasks: Task[]; total: number }>>(
      '/api/tasks'
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get tasks');
    }
    return response.data.data!.tasks;
  }

  async getTask(taskId: string): Promise<Task> {
    const response = await this.client.get<APIResponse<Task>>(`/api/tasks/${taskId}`);
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get task');
    }
    return response.data.data!;
  }

  async skipTask(taskId: string): Promise<void> {
    const response = await this.client.post<APIResponse<void>>(`/api/tasks/${taskId}/skip`);
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to skip task');
    }
  }

  async retryTask(taskId: string): Promise<void> {
    const response = await this.client.post<APIResponse<void>>(`/api/tasks/${taskId}/retry`);
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to retry task');
    }
  }

  // Materials Supplier
  async getMaterialsCatalog(category?: string): Promise<Material[]> {
    const params = category ? { category } : {};
    const response = await this.client.get<APIResponse<Material[]>>('/api/materials/catalog', {
      params,
    });
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get materials catalog');
    }
    return response.data.data!;
  }

  async checkMaterialsAvailability(materialIds: string[]): Promise<any> {
    const response = await this.client.post<APIResponse<any>>(
      '/api/materials/check-availability',
      materialIds
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to check availability');
    }
    return response.data.data!;
  }

  async orderMaterials(orders: MaterialOrder[]): Promise<Order> {
    const response = await this.client.post<APIResponse<Order>>('/api/materials/order', {
      orders,
    });
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to order materials');
    }
    return response.data.data!;
  }

  async getOrder(orderId: string): Promise<Order> {
    const response = await this.client.get<APIResponse<Order>>(`/api/materials/orders/${orderId}`);
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get order');
    }
    return response.data.data!;
  }

  // Permitting
  async applyForPermit(
    permitType: string,
    projectAddress: string,
    projectDescription: string,
    applicant: string
  ): Promise<Permit> {
    const response = await this.client.post<APIResponse<Permit>>('/api/permits/apply', {
      permit_type: permitType,
      project_address: projectAddress,
      project_description: projectDescription,
      applicant,
    });
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to apply for permit');
    }
    return response.data.data!;
  }

  async getPermitStatus(permitId: string): Promise<Permit> {
    const response = await this.client.get<APIResponse<Permit>>(`/api/permits/${permitId}`);
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get permit status');
    }
    return response.data.data!;
  }

  async scheduleInspection(
    permitId: string,
    inspectionType: string,
    requestedDate?: string
  ): Promise<Inspection> {
    const response = await this.client.post<APIResponse<Inspection>>('/api/permits/inspections', {
      permit_id: permitId,
      inspection_type: inspectionType,
      requested_date: requestedDate,
    });
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to schedule inspection');
    }
    return response.data.data!;
  }

  async getInspection(inspectionId: string): Promise<Inspection> {
    const response = await this.client.get<APIResponse<Inspection>>(
      `/api/permits/inspections/${inspectionId}`
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get inspection');
    }
    return response.data.data!;
  }

  async getRequiredPermits(projectType: string, workItems: string[]): Promise<any> {
    const response = await this.client.post<APIResponse<any>>('/api/permits/required', {
      project_type: projectType,
      work_items: workItems,
    });
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get required permits');
    }
    return response.data.data!;
  }

  // Token Usage
  async getTokenUsage(): Promise<TokenUsageSummary> {
    const response = await this.client.get<APIResponse<TokenUsageSummary>>('/api/token-usage');
    if (response.data.status === 'error') {
      throw new Error(response.data.detail || 'Failed to get token usage');
    }
    return response.data.data!;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
