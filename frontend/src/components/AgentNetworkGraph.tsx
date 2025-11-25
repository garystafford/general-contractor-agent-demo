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
  const getNodeStyle = () => {
    const baseStyle = 'px-6 py-4 rounded-xl border-2 shadow-lg transition-all duration-300 min-w-[180px] relative';

    switch (data.status) {
      case 'active':
        return `${baseStyle} bg-blue-500 border-blue-600 text-white animate-pulse shadow-blue-500/50`;
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

      <div className={getNodeStyle()}>
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
      </div>

      {/* Source handle (bottom) */}
      <Handle type="source" position={Position.Bottom} />
    </>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export function AgentNetworkGraph() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const createInitialGraph = useCallback(() => {
    const newNodes: Node<NodeData>[] = [];

    console.log('[Graph] Creating initial nodes in circular layout...');

    const centerX = 700;
    const centerY = 450;

    // General Contractor (center)
    newNodes.push({
      id: 'general-contractor',
      type: 'custom',
      position: { x: centerX - 90, y: centerY - 30 },
      data: {
        label: 'General Contractor',
        type: 'contractor',
        status: 'idle',
      },
    });

    // Calculate positions for agents in a circle
    const agentRadius = 380;
    const totalNodes = AGENTS.length + MCP_SERVERS.length;
    const angleStep = (2 * Math.PI) / totalNodes;

    // Agents (arranged in circle)
    AGENTS.forEach((agent, index) => {
      const angle = angleStep * index - Math.PI / 2; // Start from top
      const x = centerX + agentRadius * Math.cos(angle);
      const y = centerY + agentRadius * Math.sin(angle);

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

    // MCP Servers (continue the circle after agents)
    MCP_SERVERS.forEach((server, index) => {
      const angle = angleStep * (AGENTS.length + index) - Math.PI / 2;
      const x = centerX + agentRadius * Math.cos(angle);
      const y = centerY + agentRadius * Math.sin(angle);

      newNodes.push({
        id: server.id,
        type: 'custom',
        position: { x: x - 90, y: y - 30 },
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

      // Check if any tasks use MCP services
      const mcpStats = new Map<string, { total: number; active: number; completed: number }>();
      const mcpDependencies = new Map<string, Set<string>>(); // MCP -> agents that use it

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
            {/* Node Status */}
            <div className="flex items-start gap-2">
              <span className="font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">Nodes:</span>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-50 border-2 border-gray-300 rounded"></div>
                  <span className="text-gray-600 dark:text-gray-400">Idle</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-50 border-2 border-green-400 rounded"></div>
                  <span className="text-gray-600 dark:text-gray-400">Used</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-500 border-2 border-blue-600 rounded animate-pulse"></div>
                  <span className="text-gray-600 dark:text-gray-400">Working</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 border-2 border-green-600 rounded"></div>
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
                  <span className="text-gray-600 dark:text-gray-400">Task Assignment</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-green-500 border-t-2 border-dashed border-green-500"></div>
                  <span className="text-gray-600 dark:text-gray-400">🔄 Task Handoff</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-purple-500 border-t-2 border-dotted border-purple-500"></div>
                  <span className="text-gray-600 dark:text-gray-400">⚙️ MCP Service</span>
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
