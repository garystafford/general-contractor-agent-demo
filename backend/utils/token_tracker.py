"""
Token usage tracker for capturing LLM token consumption across a project.

Tracks input/output/total tokens at three levels:
- Project totals
- Per-agent breakdown
- Per-task breakdown
"""

import logging
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

    def get_project_totals(self) -> Dict[str, int]:
        """Get project-level token totals."""
        return self._project_totals.to_dict()

    def get_by_agent(self) -> Dict[str, Dict[str, int]]:
        """Get token usage broken down by agent."""
        return {name: usage.to_dict() for name, usage in self._by_agent.items()}

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
        logger.info("TokenTracker cleared")


def get_token_tracker() -> TokenTracker:
    """Get the token tracker instance."""
    return TokenTracker.get_instance()
