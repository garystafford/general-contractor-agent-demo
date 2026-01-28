import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  type Node,
  type Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  MarkerType,
  Handle,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { ArrowLeft, Activity, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Task } from '../types';

interface NodeData extends Record<string, unknown> {
  label: string;
  type: 'contractor' | 'agent' | 'mcp';
  status: 'idle' | 'active' | 'used' | 'completed';
  taskCount?: number;
  currentTask?: string;
}

const AGENTS = [
  'Architect',
  'Carpenter',
  'Electrician',
  'Plumber',
  'Mason',
  'Painter',
  'HVAC',
  'Roofer',
  'Project Planning',
];

const MCP_SERVERS = [
  { id: 'materials', label: 'Materials Supplier' },
  { id: 'permitting', label: 'Permitting Service' },
];

// Custom node component with styling based on status
const CustomNode = ({ data }: { data: NodeData }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const isActive = data.status === 'active';
  
  const getNodeStyle = () => {
    const baseStyle = 'px-6 py-4 rounded-xl border-2 shadow-lg transition-all duration-300 min-w-[180px] relative';

    switch (data.status) {
      case 'active':
        return `${baseStyle} bg-blue-500 border-blue-600 text-white`;
      case 'used':
        return `${baseStyle} bg-green-50 border-green-400 text-gray-900`;
      case 'completed':
        return `${baseStyle} bg-green-500 border-green-600 text-white`;
      default: // idle
        return `${baseStyle} bg-gray-50 border-gray-300 text-gray-600`;
    }
  };

  const getIcon = () => {
    if (data.type === 'contractor') return '🏗️';
    if (data.type === 'mcp') return '⚙️';
    return '👷';
  };

  return (
    <>
      {/* Target handle (top) */}
      <Handle type="target" position={Position.Top} />

      {/* Glow effect for active nodes */}
      {isActive && (
        <div 
          className="absolute inset-0 rounded-xl animate-pulse"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, transparent 70%)',
            transform: 'scale(1.3)',
            zIndex: -1,
          }}
        />
      )}

      <div 
        className={getNodeStyle()}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div className="flex items-center justify-center gap-2 mb-1">
          <span className="text-2xl">{getIcon()}</span>
          <span className="font-semibold text-sm">{data.label}</span>
        </div>
        {data.taskCount !== undefined && data.taskCount > 0 && (
          <div className="text-xs text-center mt-2 opacity-75">
            {data.taskCount} task{data.taskCount !== 1 ? 's' : ''}
          </div>
        )}
        {data.currentTask && (
          <div className="text-xs text-center mt-1 italic truncate max-w-[160px]">
            {data.currentTask}
          </div>
        )}
        
        {/* Tooltip */}
        {showTooltip && (data.currentTask || data.taskCount) && (
          <div 
            className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 
                       bg-gray-900 text-white text-xs rounded-lg px-3 py-2 
                       shadow-xl min-w-[200px] max-w-[280px]"
          >
            <div className="font-semibold mb-1">{data.label}</div>
            {data.taskCount !== undefined && (
              <div className="text-gray-300">Tasks: {data.taskCount}</div>
            )}
            {data.currentTask && (
              <div className="text-blue-300 mt-1">
                <span className="text-gray-400">Working on: </span>
                {data.currentTask}
              </div>
            )}
            {/* Arrow */}
            <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 
                          border-l-8 border-r-8 border-t-8 
                          border-l-transparent border-r-transparent border-t-gray-900" />
          </div>
        )}
      </div>

      {/* Source handle (bottom) */}
      <Handle type="source" position={Position.Bottom} />
    </>
  );
};

// MCP Server node with hexagon shape
const McpNode = ({ data }: { data: NodeData }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const getColors = () => {
    switch (data.status) {
      case 'active':
        return { bg: '#8b5cf6', border: '#7c3aed', text: 'white', shadow: 'rgba(139, 92, 246, 0.5)', glow: 'rgba(139, 92, 246, 0.4)' };
      case 'used':
        return { bg: '#ede9fe', border: '#a78bfa', text: '#1f2937', shadow: 'rgba(167, 139, 250, 0.3)', glow: 'transparent' };
      case 'completed':
        return { bg: '#8b5cf6', border: '#7c3aed', text: 'white', shadow: 'rgba(139, 92, 246, 0.5)', glow: 'transparent' };
      default: // idle
        return { bg: '#f3f4f6', border: '#9ca3af', text: '#6b7280', shadow: 'rgba(156, 163, 175, 0.3)', glow: 'transparent' };
    }
  };

  const colors = getColors();
  const isActive = data.status === 'active';
  const hexagonPath = 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)';

  return (
    <>
      <Handle type="target" position={Position.Top} />
      
      <div 
        className="relative"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        style={{ filter: `drop-shadow(0 4px 8px ${colors.shadow})` }}
      >
        {/* Glow effect for active nodes */}
        {isActive && (
          <div 
            className="absolute inset-0 animate-pulse"
            style={{
              background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
              transform: 'scale(1.4)',
              zIndex: -1,
            }}
          />
        )}
        
        {/* Hexagon shape */}
        <div
          style={{
            width: '160px',
            height: '140px',
            backgroundColor: colors.border,
            clipPath: hexagonPath,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {/* Inner hexagon */}
          <div
            style={{
              position: 'absolute',
              inset: '4px',
              backgroundColor: colors.bg,
              clipPath: hexagonPath,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '12px',
            }}
          >
            <span className="text-2xl mb-1">⚙️</span>
            <span 
              className="font-semibold text-sm text-center leading-tight"
              style={{ color: colors.text }}
            >
              {data.label}
            </span>
            {data.taskCount !== undefined && data.taskCount > 0 && (
              <div 
                className="text-xs mt-1 opacity-75"
                style={{ color: colors.text }}
              >
                {data.taskCount} call{data.taskCount !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
        
        {/* Tooltip */}
        {showTooltip && (
          <div 
            className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 
                       bg-gray-900 text-white text-xs rounded-lg px-3 py-2 
                       shadow-xl min-w-[180px] max-w-[250px]"
          >
            <div className="font-semibold mb-1">{data.label}</div>
            <div className="text-gray-300">Type: MCP Server</div>
            {data.taskCount !== undefined && data.taskCount > 0 && (
              <div className="text-purple-300 mt-1">
                API Calls: {data.taskCount}
              </div>
            )}
            {data.status !== 'idle' && (
              <div className="text-gray-400 mt-1 capitalize">
                Status: {data.status}
              </div>
            )}
            {/* Arrow */}
            <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 
                          border-l-8 border-r-8 border-t-8 
                          border-l-transparent border-r-transparent border-t-gray-900" />
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </>
  );
};

// General Contractor node with circle shape (central orchestrator)
const ContractorNode = ({ data }: { data: NodeData }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const getColors = () => {
    switch (data.status) {
      case 'active':
        return { bg: '#f59e0b', border: '#d97706', text: 'white', shadow: 'rgba(245, 158, 11, 0.5)', glow: 'rgba(245, 158, 11, 0.4)' };
      case 'used':
        return { bg: '#fef3c7', border: '#fbbf24', text: '#1f2937', shadow: 'rgba(251, 191, 36, 0.3)', glow: 'transparent' };
      case 'completed':
        return { bg: '#f59e0b', border: '#d97706', text: 'white', shadow: 'rgba(245, 158, 11, 0.5)', glow: 'transparent' };
      default: // idle
        return { bg: '#fffbeb', border: '#fbbf24', text: '#92400e', shadow: 'rgba(251, 191, 36, 0.3)', glow: 'transparent' };
    }
  };

  const colors = getColors();
  const isActive = data.status === 'active';

  return (
    <>
      <Handle type="target" position={Position.Top} />
      
      <div className="relative">
        {/* Glow effect for active nodes */}
        {isActive && (
          <div 
            className="absolute inset-0 rounded-full animate-pulse"
            style={{
              background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
              transform: 'scale(1.5)',
              zIndex: -1,
            }}
          />
        )}
        
        <div 
          className="relative"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          style={{ 
            width: '160px',
            height: '160px',
            borderRadius: '50%',
            backgroundColor: colors.bg,
            border: `5px solid ${colors.border}`,
            boxShadow: `0 6px 16px ${colors.shadow}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '16px',
          }}
        >
          <span className="text-3xl mb-1">🏗️</span>
          <span 
            className="font-semibold text-sm text-center leading-tight"
            style={{ color: colors.text }}
          >
            General
          </span>
          <span 
            className="font-semibold text-sm text-center leading-tight"
            style={{ color: colors.text }}
          >
            Contractor
          </span>
          
          {/* Tooltip */}
          {showTooltip && (
            <div 
              className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 
                         bg-gray-900 text-white text-xs rounded-lg px-3 py-2 
                         shadow-xl min-w-[200px] max-w-[280px]"
            >
              <div className="font-semibold mb-1">General Contractor</div>
              <div className="text-gray-300">Central Orchestrator</div>
              <div className="text-amber-300 mt-1">
                Coordinates all agents and MCP services
              </div>
              {data.status !== 'idle' && (
                <div className="text-gray-400 mt-1 capitalize">
                  Status: {data.status}
                </div>
              )}
              {/* Arrow */}
              <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 
                            border-l-8 border-r-8 border-t-8 
                            border-l-transparent border-r-transparent border-t-gray-900" />
            </div>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </>
  );
};

const nodeTypes = {
  custom: CustomNode,
  mcp: McpNode,
  contractor: ContractorNode,
};

export function AgentNetworkGraph() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const createInitialGraph = useCallback(() => {
    const newNodes: Node<NodeData>[] = [];

    console.log('[Graph] Creating initial nodes in ellipse layout...');

    const centerX = 700;
    const centerY = 400;

    // General Contractor (center) - octagon shape
    newNodes.push({
      id: 'general-contractor',
      type: 'contractor',
      position: { x: centerX - 80, y: centerY - 80 },
      data: {
        label: 'General Contractor',
        type: 'contractor',
        status: 'idle',
      },
    });

    // Calculate positions for agents in an ellipse (wider than tall)
    const radiusX = 550;  // Horizontal radius (wider)
    const radiusY = 320;  // Vertical radius (shorter)
    const totalNodes = AGENTS.length + MCP_SERVERS.length;
    const angleStep = (2 * Math.PI) / totalNodes;

    // Agents (arranged in ellipse)
    AGENTS.forEach((agent, index) => {
      const angle = angleStep * index - Math.PI / 2; // Start from top
      const x = centerX + radiusX * Math.cos(angle);
      const y = centerY + radiusY * Math.sin(angle);

      newNodes.push({
        id: agent.toLowerCase(),
        type: 'custom',
        position: { x: x - 90, y: y - 30 },
        data: {
          label: agent,
          type: 'agent',
          status: 'idle',
          taskCount: 0,
        },
      });
    });

    // MCP Servers (continue the ellipse after agents)
    MCP_SERVERS.forEach((server, index) => {
      const angle = angleStep * (AGENTS.length + index) - Math.PI / 2;
      const x = centerX + radiusX * Math.cos(angle);
      const y = centerY + radiusY * Math.sin(angle);

      newNodes.push({
        id: server.id,
        type: 'mcp',  // Use circle MCP node type
        position: { x: x - 65, y: y - 65 },
        data: {
          label: server.label,
          type: 'mcp',
          status: 'idle',
          taskCount: 0,
        },
      });
    });

    console.log('[Graph] Created nodes with IDs:', newNodes.map(n => n.id));

    setNodes(newNodes);
    setEdges([]); // Edges will be created dynamically based on task dependencies
  }, [setNodes, setEdges]);

  const updateGraphWithTasks = useCallback(async () => {
    try {
      const tasks = await apiClient.getTasks();
      console.log(`[Graph] Fetched ${tasks.length} tasks`);

      // Count tasks by agent and determine status
      const agentStats = new Map<string, { total: number; active: number; completed: number; currentTask?: string }>();

      tasks.forEach((task: Task) => {
        const agentKey = task.agent.toLowerCase();
        const stats = agentStats.get(agentKey) || { total: 0, active: 0, completed: 0 };

        stats.total++;
        if (task.status === 'in_progress') {
          stats.active++;
          stats.currentTask = task.description;
        } else if (task.status === 'completed') {
          stats.completed++;
        }

        agentStats.set(agentKey, stats);
      });

      console.log('[Graph] Agent stats:', Object.fromEntries(agentStats));

      // Track dependencies between agents (which agent depends on which)
      const agentDependencies = new Map<string, Set<string>>(); // target agent -> source agents it depends on
      const activeHandoffs = new Set<string>(); // edges that are currently active

      tasks.forEach((task: Task) => {
        const targetAgent = task.agent.toLowerCase();

        // For each dependency, find which agent owns that task
        task.dependencies.forEach((depTaskId: string) => {
          const depTask = tasks.find((t: Task) => t.task_id === depTaskId);
          if (depTask && depTask.agent !== task.agent) {
            const sourceAgent = depTask.agent.toLowerCase();

            if (!agentDependencies.has(targetAgent)) {
              agentDependencies.set(targetAgent, new Set());
            }
            agentDependencies.get(targetAgent)!.add(sourceAgent);

            // Mark edge as active if dependency task just completed and current task is ready/in_progress
            if (
              (depTask.status === 'completed' && (task.status === 'ready' || task.status === 'in_progress')) ||
              (depTask.status === 'in_progress' && task.status === 'pending')
            ) {
              activeHandoffs.add(`${sourceAgent}->${targetAgent}`);
            }
          }
        });
      });

      // Fetch actual MCP activity from the activity logger
      const mcpStats = new Map<string, { total: number; active: number; completed: number }>();
      const mcpDependencies = new Map<string, Set<string>>(); // MCP -> agents that use it
      
      try {
        // Fetch recent activity events to track MCP calls
        const activityResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/activity/recent?count=100`);
        if (activityResponse.ok) {
          const activityData = await activityResponse.json();
          const events = activityData.data?.events || [];
          
          // Track MCP calls from activity events
          const recentMcpCalls = new Map<string, { lastCallTime: number; agent?: string }>();
          const now = Date.now();
          const activeWindow = 10000; // Consider MCP active if called within last 10 seconds
          
          events.forEach((event: { type: string; details?: { service?: string }; timestamp?: string; agent?: string }) => {
            if (event.type === 'mcp_call' || event.type === 'mcp_result') {
              const service = event.details?.service;
              if (service) {
                const eventTime = event.timestamp ? new Date(event.timestamp).getTime() : now;
                const existing = recentMcpCalls.get(service);
                
                if (!existing || eventTime > existing.lastCallTime) {
                  recentMcpCalls.set(service, { lastCallTime: eventTime, agent: event.agent || undefined });
                }
                
                // Update MCP stats
                const stats = mcpStats.get(service) || { total: 0, active: 0, completed: 0 };
                stats.total++;
                
                // Check if this is a recent/active call
                if (now - eventTime < activeWindow) {
                  stats.active++;
                } else if (event.type === 'mcp_result') {
                  stats.completed++;
                }
                mcpStats.set(service, stats);
                
                // Track which agents use this MCP service
                if (!mcpDependencies.has(service)) {
                  mcpDependencies.set(service, new Set());
                }
                // MCP calls are made by the general contractor on behalf of agents
                // Add connection to general-contractor
                mcpDependencies.get(service)!.add('general-contractor');
              }
            }
          });
          
          // Mark active MCP connections
          recentMcpCalls.forEach((info, service) => {
            if (now - info.lastCallTime < activeWindow) {
              activeHandoffs.add(`${service}->general-contractor`);
            }
          });
          
          console.log('[Graph] MCP stats from activity:', Object.fromEntries(mcpStats));
        }
      } catch (error) {
        console.warn('[Graph] Could not fetch MCP activity, falling back to task-based detection:', error);
        
        // Fallback: detect MCP usage from task descriptions (original behavior)
        tasks.forEach((task: Task) => {
          const agentKey = task.agent.toLowerCase();
          const desc = task.description.toLowerCase();

          if (desc.includes('material') || desc.includes('order')) {
            const stats = mcpStats.get('materials') || { total: 0, active: 0, completed: 0 };
            stats.total++;
            if (task.status === 'in_progress') stats.active++;
            if (task.status === 'completed') stats.completed++;
            mcpStats.set('materials', stats);

            if (!mcpDependencies.has('materials')) {
              mcpDependencies.set('materials', new Set());
            }
            mcpDependencies.get('materials')!.add(agentKey);

            if (task.status === 'in_progress') {
              activeHandoffs.add(`materials->${agentKey}`);
            }
          }
          if (desc.includes('permit') || desc.includes('inspection')) {
            const stats = mcpStats.get('permitting') || { total: 0, active: 0, completed: 0 };
            stats.total++;
            if (task.status === 'in_progress') stats.active++;
            if (task.status === 'completed') stats.completed++;
            mcpStats.set('permitting', stats);

            if (!mcpDependencies.has('permitting')) {
              mcpDependencies.set('permitting', new Set());
            }
            mcpDependencies.get('permitting')!.add(agentKey);

            if (task.status === 'in_progress') {
              activeHandoffs.add(`permitting->${agentKey}`);
            }
          }
        });
      }

      // Update nodes with task information
      setNodes((nodes) =>
        nodes.map((node) => {
          const nodeId = node.id;

          // Check if it's an agent node
          if (node.data.type === 'agent') {
            const stats = agentStats.get(nodeId);
            if (stats) {
              let status: 'idle' | 'active' | 'used' | 'completed' = 'idle';
              if (stats.active > 0) {
                status = 'active';
              } else if (stats.total === stats.completed && stats.completed > 0) {
                status = 'completed';
              } else if (stats.total > 0) {
                status = 'used';
              }

              return {
                ...node,
                data: {
                  ...node.data,
                  status,
                  taskCount: stats.total,
                  currentTask: stats.currentTask,
                },
              };
            }
          }

          // Check if it's an MCP server node
          if (node.data.type === 'mcp') {
            const stats = mcpStats.get(nodeId);
            if (stats) {
              let status: 'idle' | 'active' | 'used' | 'completed' = 'idle';
              if (stats.active > 0) {
                status = 'active';
              } else if (stats.total === stats.completed && stats.completed > 0) {
                status = 'completed';
              } else if (stats.total > 0) {
                status = 'used';
              }

              return {
                ...node,
                data: {
                  ...node.data,
                  status,
                  taskCount: stats.total,
                },
              };
            }
          }

          return node;
        })
      );

      // Create new edges based on agent dependencies and MCP usage
      const newEdges: Edge[] = [];

      // Add edges from General Contractor to all agents with tasks
      console.log('[Graph] Creating GC → Agent edges...');
      agentStats.forEach((stats, agentId) => {
        if (stats.total > 0) {
          const edge = {
            id: `gc-${agentId}`,
            source: 'general-contractor',
            target: agentId,
            animated: stats.active > 0,
            style: {
              stroke: stats.active > 0 ? '#3b82f6' : '#94a3b8',
              strokeWidth: stats.active > 0 ? 3 : 2,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: stats.active > 0 ? '#3b82f6' : '#94a3b8',
              width: 20,
              height: 20,
            },
          };
          console.log(`[Graph] Edge: general-contractor → ${agentId}`, edge);
          newEdges.push(edge);
        }
      });

      // Add edges between agents based on task dependencies
      agentDependencies.forEach((sourceAgents, targetAgent) => {
        sourceAgents.forEach((sourceAgent) => {
          const edgeKey = `${sourceAgent}->${targetAgent}`;
          const isActive = activeHandoffs.has(edgeKey);

          newEdges.push({
            id: `dep-${sourceAgent}-${targetAgent}`,
            source: sourceAgent,
            target: targetAgent,
            animated: isActive,
            style: {
              stroke: isActive ? '#10b981' : '#94a3b8',
              strokeWidth: isActive ? 3 : 2,
              strokeDasharray: '5,5',
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: isActive ? '#10b981' : '#94a3b8',
              width: 20,
              height: 20,
            },
            label: isActive ? '🔄 handoff' : '',
            labelStyle: { fill: '#10b981', fontWeight: 'bold', fontSize: 12 },
            labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
          });
        });
      });

      // Add edges from MCP servers to agents
      mcpDependencies.forEach((agents, mcpId) => {
        agents.forEach((agentId) => {
          const edgeKey = `${mcpId}->${agentId}`;
          const isActive = activeHandoffs.has(edgeKey);

          newEdges.push({
            id: `mcp-${mcpId}-${agentId}`,
            source: mcpId,
            target: agentId,
            animated: isActive,
            style: {
              stroke: isActive ? '#a855f7' : '#94a3b8',
              strokeWidth: isActive ? 3 : 2,
              strokeDasharray: '3,3',
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: isActive ? '#a855f7' : '#94a3b8',
              width: 20,
              height: 20,
            },
            label: isActive ? '⚙️ service' : '',
            labelStyle: { fill: '#a855f7', fontWeight: 'bold', fontSize: 12 },
            labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
          });
        });
      });

      console.log(`[Graph] Total edges created: ${newEdges.length}`, newEdges);
      console.log('[Graph] Setting edges...', {
        gcToAgents: Array.from(agentStats.keys()).filter(id => agentStats.get(id)!.total > 0).length,
        agentDependencies: agentDependencies.size,
        mcpDependencies: mcpDependencies.size,
        edges: newEdges.map(e => `${e.source} → ${e.target}`),
      });

      setEdges(newEdges);

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error updating graph with tasks:', error);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    createInitialGraph();
  }, [createInitialGraph]);

  useEffect(() => {
    updateGraphWithTasks();

    // Poll for updates every 2 seconds
    const interval = setInterval(updateGraphWithTasks, 2000);

    return () => clearInterval(interval);
  }, [updateGraphWithTasks]);

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Dashboard
            </button>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              <Activity className="w-6 h-6" />
              Agent Network Graph
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
            <button
              onClick={updateGraphWithTasks}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-3">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-start gap-8 text-sm">
            {/* Node Types */}
            <div className="flex items-start gap-2">
              <span className="font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">Nodes:</span>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-amber-50 border-2 border-amber-400 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Orchestrator</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-50 border-2 border-gray-300 rounded"></div>
                  <span className="text-gray-600 dark:text-gray-400">Agent</span>
                </div>
                <div className="flex items-center gap-2">
                  <div 
                    className="w-5 h-4 bg-purple-100 border-2 border-purple-400"
                    style={{ clipPath: 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)' }}
                  ></div>
                  <span className="text-gray-600 dark:text-gray-400">MCP Server</span>
                </div>
              </div>
            </div>

            {/* Node Status */}
            <div className="flex items-start gap-2">
              <span className="font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">Status:</span>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-gray-50 border-2 border-gray-300 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Idle</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 border-2 border-blue-600 rounded-full animate-pulse"></div>
                  <span className="text-gray-600 dark:text-gray-400">Active</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 border-2 border-green-600 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Done</span>
                </div>
              </div>
            </div>

            {/* Edge Types */}
            <div className="flex items-start gap-2">
              <span className="font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">Connections:</span>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-blue-500"></div>
                  <span className="text-gray-600 dark:text-gray-400">Task</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-green-500 border-t-2 border-dashed border-green-500"></div>
                  <span className="text-gray-600 dark:text-gray-400">Handoff</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-purple-500 border-t-2 border-dotted border-purple-500"></div>
                  <span className="text-gray-600 dark:text-gray-400">MCP Call</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.5}
          maxZoom={1.5}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}
