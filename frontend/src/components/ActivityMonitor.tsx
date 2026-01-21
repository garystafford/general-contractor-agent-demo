import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { config } from '../config';
import {
  ArrowLeft,
  Terminal,
  Trash2,
  Pause,
  Play,
  Download,
} from 'lucide-react';
import toast from 'react-hot-toast';

// Activity event types matching backend
interface ActivityEvent {
  timestamp: string;
  type: string;
  agent: string | null;
  task_id: string | null;
  message: string;
  details?: Record<string, any>;
}

// Color mapping for different event types
const EVENT_COLORS: Record<string, { text: string; prefix: string; bg: string }> = {
  task_start: { text: 'text-blue-400', prefix: '[START]', bg: 'bg-blue-900/20' },
  task_complete: { text: 'text-green-400', prefix: '[DONE]', bg: 'bg-green-900/20' },
  task_failed: { text: 'text-red-400', prefix: '[FAIL]', bg: 'bg-red-900/20' },
  agent_thinking: { text: 'text-purple-400', prefix: '[THINK]', bg: 'bg-purple-900/20' },
  tool_call: { text: 'text-yellow-400', prefix: '[TOOL]', bg: 'bg-yellow-900/20' },
  tool_result: { text: 'text-cyan-400', prefix: '[RESULT]', bg: 'bg-cyan-900/20' },
  planning_start: { text: 'text-indigo-400', prefix: '[PLAN]', bg: 'bg-indigo-900/20' },
  planning_complete: { text: 'text-indigo-400', prefix: '[PLAN]', bg: 'bg-indigo-900/20' },
  mcp_call: { text: 'text-orange-400', prefix: '[MCP]', bg: 'bg-orange-900/20' },
  mcp_result: { text: 'text-orange-300', prefix: '[MCP]', bg: 'bg-orange-900/10' },
  info: { text: 'text-gray-400', prefix: '[INFO]', bg: '' },
  warning: { text: 'text-yellow-500', prefix: '[WARN]', bg: 'bg-yellow-900/10' },
  error: { text: 'text-red-500', prefix: '[ERROR]', bg: 'bg-red-900/20' },
};

export function ActivityMonitor() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const terminalRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Connect to SSE stream
  useEffect(() => {
    const connectToStream = () => {
      const url = `${config.apiUrl}/api/activity/stream`;
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        console.log('Connected to activity stream');
      };

      eventSource.onmessage = (event) => {
        if (isPaused) return;

        try {
          const data = JSON.parse(event.data) as ActivityEvent;
          setEvents((prev) => [...prev.slice(-499), data]); // Keep last 500 events
        } catch (e) {
          console.error('Failed to parse event:', e);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        console.error('Activity stream error, reconnecting...');
        eventSource.close();
        // Reconnect after delay
        setTimeout(connectToStream, 3000);
      };
    };

    connectToStream();

    return () => {
      eventSourceRef.current?.close();
    };
  }, [isPaused]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current && !isPaused) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [events, isPaused]);

  // Format timestamp
  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return '--:--:--';
    }
  };

  // Get event styling
  const getEventStyle = (type: string) => {
    return EVENT_COLORS[type] || EVENT_COLORS.info;
  };

  // Filter events
  const filteredEvents = events.filter((event) => {
    if (filter === 'all') return true;
    if (filter === 'tools') return event.type === 'tool_call' || event.type === 'tool_result';
    if (filter === 'tasks') return event.type.startsWith('task_');
    if (filter === 'thinking') return event.type === 'agent_thinking';
    if (filter === 'mcp') return event.type.startsWith('mcp_');
    if (filter === 'errors') return event.type === 'error' || event.type === 'task_failed';
    return true;
  });

  // Clear events
  const handleClear = async () => {
    try {
      await fetch(`${config.apiUrl}/api/activity/clear`, { method: 'POST' });
      setEvents([]);
      toast.success('Activity log cleared');
    } catch {
      toast.error('Failed to clear activity log');
    }
  };

  // Export events
  const handleExport = () => {
    const content = events.map(e =>
      `${formatTime(e.timestamp)} ${getEventStyle(e.type).prefix} [${e.agent || 'System'}] ${e.message}`
    ).join('\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity-log-${new Date().toISOString().slice(0, 19)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Activity log exported');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-4 font-mono">
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Dashboard</span>
            </button>
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-green-400" />
              <h1 className="text-xl font-bold text-white">Activity Monitor</h1>
            </div>
          </div>

          {/* Connection status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between flex-wrap gap-4 bg-gray-800 rounded-lg p-3">
          <div className="flex items-center gap-2">
            {/* Filter dropdown */}
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-gray-700 text-white px-3 py-1.5 rounded border border-gray-600 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Events</option>
              <option value="tasks">Tasks Only</option>
              <option value="tools">Tool Calls</option>
              <option value="thinking">Reasoning</option>
              <option value="mcp">MCP Calls</option>
              <option value="errors">Errors Only</option>
            </select>

            {/* Event count */}
            <span className="text-sm text-gray-400">
              {filteredEvents.length} events
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Pause/Resume */}
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition ${
                isPaused
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-yellow-600 hover:bg-yellow-700 text-white'
              }`}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              {isPaused ? 'Resume' : 'Pause'}
            </button>

            {/* Export */}
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-600 hover:bg-gray-500 text-white rounded text-sm transition"
            >
              <Download className="w-4 h-4" />
              Export
            </button>

            {/* Clear */}
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition"
            >
              <Trash2 className="w-4 h-4" />
              Clear
            </button>
          </div>
        </div>

        {/* Terminal */}
        <div
          ref={terminalRef}
          className="bg-black rounded-lg border border-gray-700 p-4 h-[calc(100vh-220px)] overflow-y-auto"
          style={{ scrollbarWidth: 'thin', scrollbarColor: '#4B5563 #1F2937' }}
        >
          {filteredEvents.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <Terminal className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Waiting for activity...</p>
                <p className="text-sm mt-1">Events will appear here when agents start working</p>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredEvents.map((event, index) => {
                const style = getEventStyle(event.type);
                return (
                  <div
                    key={`${event.timestamp}-${index}`}
                    className={`flex items-start gap-2 py-1 px-2 rounded ${style.bg} hover:bg-gray-800/50 transition`}
                  >
                    {/* Timestamp */}
                    <span className="text-gray-500 text-xs whitespace-nowrap">
                      {formatTime(event.timestamp)}
                    </span>

                    {/* Event type prefix */}
                    <span className={`${style.text} font-bold text-xs whitespace-nowrap`}>
                      {style.prefix}
                    </span>

                    {/* Agent name */}
                    {event.agent && (
                      <span className="text-blue-300 text-xs whitespace-nowrap">
                        [{event.agent}]
                      </span>
                    )}

                    {/* Message */}
                    <span className={`${style.text} text-sm break-all`}>
                      {event.message}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Paused indicator */}
          {isPaused && (
            <div className="sticky bottom-0 bg-yellow-900/80 text-yellow-200 text-center py-2 rounded mt-4">
              Stream paused - click Resume to continue
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-xs text-gray-400 bg-gray-800 rounded-lg p-3">
          <span className="font-semibold">Legend:</span>
          <span className="text-blue-400">[START] Task Started</span>
          <span className="text-green-400">[DONE] Task Complete</span>
          <span className="text-red-400">[FAIL] Task Failed</span>
          <span className="text-purple-400">[THINK] Agent Reasoning</span>
          <span className="text-yellow-400">[TOOL] Tool Call</span>
          <span className="text-cyan-400">[RESULT] Tool Result</span>
          <span className="text-orange-400">[MCP] MCP Service Call</span>
        </div>
      </div>
    </div>
  );
}
