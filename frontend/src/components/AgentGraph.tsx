import { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  type Node,
  type Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useProjectStore } from '../store/projectStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { config } from '../config';
import type { AgentActivityMessage } from '../types';

const AGENT_NAMES = [
  'Architect',
  'Carpenter',
  'Electrician',
  'Plumber',
  'Mason',
  'Painter',
  'HVAC',
  'Roofer',
];

const MCP_SERVERS = [
  { id: 'materials', name: 'Materials Supplier' },
  { id: 'permitting', name: 'Permitting Service' },
];

// Create custom node component for agents
function AgentNode({ data }: { data: any }) {
  const isActive = data.isActive;
  const isMCP = data.isMCP;

  return (
    <div
      className={`px-6 py-4 rounded-xl border-2 transition-all duration-300 ${
        isActive
          ? isMCP
            ? 'bg-purple-500 border-purple-300 shadow-lg shadow-purple-500/50 scale-110'
            : 'bg-blue-500 border-blue-300 shadow-lg shadow-blue-500/50 scale-110'
          : isMCP
          ? 'bg-purple-100 border-purple-300 dark:bg-purple-900/30 dark:border-purple-700'
          : 'bg-gray-100 border-gray-300 dark:bg-gray-800 dark:border-gray-600'
      }`}
    >
      <div className="text-center">
        <div
          className={`font-semibold ${
            isActive ? 'text-white' : 'text-gray-900 dark:text-white'
          }`}
        >
          {data.label}
        </div>
        {isActive && data.taskDescription && (
          <div className="text-xs text-white/90 mt-1 max-w-[200px] truncate">
            {data.taskDescription}
          </div>
        )}
        {/* Pulsing indicator for active agents */}
        {isActive && (
          <div className="absolute -top-1 -right-1 w-3 h-3">
            <div className="absolute w-full h-full bg-green-400 rounded-full animate-ping"></div>
            <div className="relative w-full h-full bg-green-500 rounded-full"></div>
          </div>
        )}
      </div>
    </div>
  );
}

const nodeTypes = {
  agent: AgentNode,
};

export function AgentGraph() {
  const { agentActivity } = useProjectStore();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set());

  // Handle WebSocket messages for agent activity
  const handleAgentActivity = useCallback(
    (message: any) => {
      if (message.type === 'agent_activity') {
        const data = message.data as AgentActivityMessage['data'];
        const active = new Set(Object.keys(data.active_agents));
        setActiveAgents(active);
      }
    },
    []
  );

  // Connect to agent activity WebSocket
  useWebSocket({
    url: `${config.wsUrl}/ws/agent-activity`,
    onMessage: handleAgentActivity,
  });

  // Initialize graph layout
  useEffect(() => {
    const centerX = 400;
    const centerY = 300;
    const radius = 250;

    // Create General Contractor node (center)
    const gcNode: Node = {
      id: 'general-contractor',
      type: 'agent',
      position: { x: centerX - 80, y: centerY - 30 },
      data: {
        label: 'General Contractor',
        isActive: true, // Always shown as coordinator
        isMCP: false,
      },
    };

    // Create agent nodes in a circle
    const agentNodes: Node[] = AGENT_NAMES.map((name, index) => {
      const angle = (index / AGENT_NAMES.length) * 2 * Math.PI;
      const x = centerX + radius * Math.cos(angle) - 60;
      const y = centerY + radius * Math.sin(angle) - 25;

      return {
        id: name.toLowerCase(),
        type: 'agent',
        position: { x, y },
        data: {
          label: name,
          isActive: activeAgents.has(name),
          isMCP: false,
          taskDescription: agentActivity?.active_agents[name]?.description || null,
        },
      };
    });

    // Create MCP server nodes
    const mcpNodes: Node[] = MCP_SERVERS.map((server, index) => {
      const x = centerX + (index === 0 ? -350 : 350);
      const y = centerY - 25;

      return {
        id: server.id,
        type: 'agent',
        position: { x, y },
        data: {
          label: server.name,
          isActive: false, // Can enhance this to track MCP usage
          isMCP: true,
        },
      };
    });

    // Create edges from GC to active agents
    const agentEdges: Edge[] = AGENT_NAMES.filter((name) => activeAgents.has(name)).map(
      (name) => ({
        id: `gc-${name.toLowerCase()}`,
        source: 'general-contractor',
        target: name.toLowerCase(),
        animated: true,
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#3b82f6',
        },
      })
    );

    // Create edges from GC to MCP servers (show when any agent is active)
    const mcpEdges: Edge[] =
      activeAgents.size > 0
        ? MCP_SERVERS.map((server) => ({
            id: `gc-${server.id}`,
            source: 'general-contractor',
            target: server.id,
            animated: true,
            style: { stroke: '#a855f7', strokeWidth: 2, strokeDasharray: '5,5' },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#a855f7',
            },
          }))
        : [];

    setNodes([gcNode, ...agentNodes, ...mcpNodes]);
    setEdges([...agentEdges, ...mcpEdges]);
  }, [activeAgents, agentActivity, setNodes, setEdges]);

  return (
    <div className="w-full h-[600px] bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background />
        <Controls />
      </ReactFlow>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 border border-gray-200 dark:border-gray-700">
        <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Legend</div>
        <div className="space-y-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            <span className="text-gray-700 dark:text-gray-300">Active Agent</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-300 dark:bg-gray-600 rounded"></div>
            <span className="text-gray-700 dark:text-gray-300">Idle Agent</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-purple-500 rounded"></div>
            <span className="text-gray-700 dark:text-gray-300">MCP Server</span>
          </div>
        </div>
      </div>
    </div>
  );
}
