"""
Token usage tracker for capturing LLM token consumption across a project.

Tracks input/output/total tokens at three levels:
- Project totals
- Per-agent breakdown
- Per-task breakdown
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Accumulated token usage counts."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, input_tokens: int, output_tokens: int, total_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens

    def to_dict(self) -> Dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


class TokenTracker:
    """
    Singleton token usage tracker that accumulates LLM token consumption.

    Usage:
        tracker = TokenTracker.get_instance()
        tracker.record_usage("task_1", "Architect", {"inputTokens": 100, "outputTokens": 50, "totalTokens": 150})
    """

    _instance: Optional["TokenTracker"] = None

    def __init__(self):
        self._project_totals = TokenUsage()
        self._by_task: Dict[str, TokenUsage] = {}
        self._by_agent: Dict[str, TokenUsage] = {}
        self._api_call_count: int = 0
        self._api_calls_by_agent: Dict[str, int] = {}
        self._project_start_time: Optional[float] = None
        self._project_end_time: Optional[float] = None

    @classmethod
    def get_instance(cls) -> "TokenTracker":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_usage(self, task_id: str, agent_name: str, usage: Dict[str, Any]) -> None:
        """
        Record token usage from a Strands AgentResult.metrics.accumulated_usage dict.

        Args:
            task_id: The task that consumed the tokens
            agent_name: The agent that consumed the tokens
            usage: Dict with keys inputTokens, outputTokens, totalTokens (Strands format)
        """
        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)
        total_tokens = usage.get("totalTokens", 0)

        if total_tokens == 0 and input_tokens == 0 and output_tokens == 0:
            return

        # Count this as a Bedrock API call
        self._api_call_count += 1
        self._api_calls_by_agent[agent_name] = (
            self._api_calls_by_agent.get(agent_name, 0) + 1
        )

        # Accumulate into project totals
        self._project_totals.add(input_tokens, output_tokens, total_tokens)

        # Accumulate by task
        if task_id not in self._by_task:
            self._by_task[task_id] = TokenUsage()
        self._by_task[task_id].add(input_tokens, output_tokens, total_tokens)

        # Accumulate by agent
        if agent_name not in self._by_agent:
            self._by_agent[agent_name] = TokenUsage()
        self._by_agent[agent_name].add(input_tokens, output_tokens, total_tokens)

        logger.info(
            f"Token usage recorded - task={task_id}, agent={agent_name}: "
            f"in={input_tokens:,}, out={output_tokens:,}, total={total_tokens:,}"
        )

    def start_timer(self) -> None:
        """Record project start time."""
        self._project_start_time = time.time()
        self._project_end_time = None

    def stop_timer(self) -> None:
        """Record project end time."""
        self._project_end_time = time.time()

    def get_runtime_seconds(self) -> Optional[float]:
        """Get project runtime in seconds, or None if not started."""
        if self._project_start_time is None:
            return None
        end = self._project_end_time or time.time()
        return round(end - self._project_start_time, 1)

    def get_project_totals(self) -> Dict[str, Any]:
        """Get project-level token totals."""
        totals = self._project_totals.to_dict()
        totals["bedrock_api_calls"] = self._api_call_count
        runtime = self.get_runtime_seconds()
        if runtime is not None:
            totals["runtime_seconds"] = runtime
            minutes, secs = divmod(int(runtime), 60)
            totals["runtime_display"] = f"{minutes}m {secs}s"
        return totals

    def get_by_agent(self) -> Dict[str, Dict[str, Any]]:
        """Get token usage broken down by agent."""
        result = {}
        for name, usage in self._by_agent.items():
            agent_data = usage.to_dict()
            agent_data["bedrock_api_calls"] = self._api_calls_by_agent.get(name, 0)
            result[name] = agent_data
        return result

    def get_by_task(self) -> Dict[str, Dict[str, int]]:
        """Get token usage broken down by task."""
        return {task_id: usage.to_dict() for task_id, usage in self._by_task.items()}

    def get_summary(self) -> Dict[str, Any]:
        """Get full token usage summary."""
        return {
            "project_totals": self.get_project_totals(),
            "by_agent": self.get_by_agent(),
            "by_task": self.get_by_task(),
        }

    def clear(self) -> None:
        """Clear all tracked token usage."""
        self._project_totals = TokenUsage()
        self._by_task.clear()
        self._by_agent.clear()
        self._api_call_count = 0
        self._api_calls_by_agent.clear()
        self._project_start_time = None
        self._project_end_time = None
        logger.info("TokenTracker cleared")


def get_token_tracker() -> TokenTracker:
    """Get the token tracker instance."""
    return TokenTracker.get_instance()
