"""
Activity logger for capturing and streaming agent events.

Captures:
- Agent reasoning/thinking
- Tool calls with arguments
- Tool results
- Task state changes
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of activity events."""
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    AGENT_THINKING = "agent_thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    PLANNING_START = "planning_start"
    PLANNING_COMPLETE = "planning_complete"
    MCP_CALL = "mcp_call"
    MCP_RESULT = "mcp_result"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ActivityEvent:
    """Represents a single activity event."""
    timestamp: str
    type: ActivityType
    agent: Optional[str]
    task_id: Optional[str]
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "type": self.type.value,
            "agent": self.agent,
            "task_id": self.task_id,
            "message": self.message,
            "details": self.details,
        }


class ActivityLogger:
    """
    Singleton activity logger that captures and streams agent events.

    Usage:
        logger = ActivityLogger.get_instance()
        logger.log_tool_call("Architect", "task_1", "create_floor_plan", {"square_feet": 1200})
    """

    _instance: Optional["ActivityLogger"] = None

    def __init__(self, max_events: int = 500):
        self._events: deque = deque(maxlen=max_events)
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "ActivityLogger":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _now(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()

    async def _emit(self, event: ActivityEvent):
        """Emit event to all subscribers."""
        self._events.append(event)

        # Send to all subscribers
        async with self._lock:
            dead_queues = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Skip if queue is full
                    pass
                except Exception:
                    dead_queues.append(queue)

            # Clean up dead queues
            for q in dead_queues:
                self._subscribers.remove(q)

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to activity events. Returns a queue for receiving events."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from activity events."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_recent_events(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent events."""
        events = list(self._events)[-count:]
        return [e.to_dict() for e in events]

    def clear(self):
        """Clear all events."""
        self._events.clear()

    # Logging methods
    async def log_task_start(self, agent: str, task_id: str, description: str):
        """Log task starting."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.TASK_START,
            agent=agent,
            task_id=task_id,
            message=f"Starting: {description}",
            details={"description": description},
        )
        await self._emit(event)
        logger.info(f"[{agent}] Task {task_id} started: {description}")

    async def log_task_complete(self, agent: str, task_id: str, result: Any = None):
        """Log task completion."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.TASK_COMPLETE,
            agent=agent,
            task_id=task_id,
            message="Task completed successfully",
            details={"result_summary": str(result)[:200] if result else None},
        )
        await self._emit(event)
        logger.info(f"[{agent}] Task {task_id} completed")

    async def log_task_failed(self, agent: str, task_id: str, error: str):
        """Log task failure."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.TASK_FAILED,
            agent=agent,
            task_id=task_id,
            message=f"Task failed: {error}",
            details={"error": error},
        )
        await self._emit(event)
        logger.error(f"[{agent}] Task {task_id} failed: {error}")

    async def log_thinking(self, agent: str, task_id: Optional[str], thinking: str):
        """Log agent reasoning/thinking."""
        # Truncate long thinking messages
        display_thinking = thinking[:500] + "..." if len(thinking) > 500 else thinking
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.AGENT_THINKING,
            agent=agent,
            task_id=task_id,
            message=display_thinking,
            details={"full_thinking": thinking},
        )
        await self._emit(event)
        logger.debug(f"[{agent}] Thinking: {display_thinking[:100]}...")

    async def log_tool_call(
        self,
        agent: str,
        task_id: Optional[str],
        tool_name: str,
        arguments: Dict[str, Any]
    ):
        """Log a tool call."""
        # Format arguments for display
        args_str = ", ".join(f"{k}={repr(v)[:50]}" for k, v in arguments.items())
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.TOOL_CALL,
            agent=agent,
            task_id=task_id,
            message=f"Calling {tool_name}({args_str})",
            details={"tool": tool_name, "arguments": arguments},
        )
        await self._emit(event)
        logger.info(f"[{agent}] Tool call: {tool_name}")

    async def log_tool_result(
        self,
        agent: str,
        task_id: Optional[str],
        tool_name: str,
        result: Any
    ):
        """Log a tool result."""
        result_str = str(result)[:200] if result else "None"
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.TOOL_RESULT,
            agent=agent,
            task_id=task_id,
            message=f"{tool_name} returned: {result_str}",
            details={"tool": tool_name, "result": result},
        )
        await self._emit(event)
        logger.debug(f"[{agent}] Tool result: {tool_name}")

    async def log_planning_start(self, project_type: str):
        """Log planning phase starting."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.PLANNING_START,
            agent="Planner",
            task_id=None,
            message=f"Starting dynamic planning for: {project_type}",
            details={"project_type": project_type},
        )
        await self._emit(event)
        logger.info(f"Planning started for {project_type}")

    async def log_planning_complete(self, task_count: int):
        """Log planning phase completion."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.PLANNING_COMPLETE,
            agent="Planner",
            task_id=None,
            message=f"Planning complete: {task_count} tasks created",
            details={"task_count": task_count},
        )
        await self._emit(event)
        logger.info(f"Planning complete: {task_count} tasks")

    async def log_mcp_call(self, service: str, tool: str, arguments: Dict[str, Any]):
        """Log MCP service call."""
        args_str = ", ".join(f"{k}={repr(v)[:30]}" for k, v in arguments.items())
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.MCP_CALL,
            agent=None,
            task_id=None,
            message=f"MCP {service}.{tool}({args_str})",
            details={"service": service, "tool": tool, "arguments": arguments},
        )
        await self._emit(event)
        logger.info(f"MCP call: {service}.{tool}")

    async def log_mcp_result(self, service: str, tool: str, result: Any):
        """Log MCP service result."""
        result_str = str(result)[:150] if result else "None"
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.MCP_RESULT,
            agent=None,
            task_id=None,
            message=f"MCP {service}.{tool} returned: {result_str}",
            details={"service": service, "tool": tool, "result": result},
        )
        await self._emit(event)

    async def log_info(self, message: str, agent: Optional[str] = None):
        """Log general info message."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.INFO,
            agent=agent,
            task_id=None,
            message=message,
        )
        await self._emit(event)
        logger.info(message)

    async def log_warning(self, message: str, agent: Optional[str] = None):
        """Log warning message."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.WARNING,
            agent=agent,
            task_id=None,
            message=message,
        )
        await self._emit(event)
        logger.warning(message)

    async def log_error(self, message: str, agent: Optional[str] = None):
        """Log error message."""
        event = ActivityEvent(
            timestamp=self._now(),
            type=ActivityType.ERROR,
            agent=agent,
            task_id=None,
            message=message,
        )
        await self._emit(event)
        logger.error(message)


# Convenience function to get the logger
def get_activity_logger() -> ActivityLogger:
    """Get the activity logger instance."""
    return ActivityLogger.get_instance()
