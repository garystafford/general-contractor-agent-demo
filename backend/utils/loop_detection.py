"""
Loop detection and prevention utilities for agent execution.
"""

import logging
from typing import Dict, List, Tuple, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ToolCallTracker:
    """
    Tracks tool calls to detect and prevent infinite loops.

    Detects loops by:
    1. Counting total tool calls
    2. Detecting repeated identical calls
    3. Tracking sequences of calls
    """

    def __init__(
        self, max_total_calls: int = 20, max_identical_calls: int = 2, max_recent_repeats: int = 3
    ):
        """
        Initialize the tracker.

        Args:
            max_total_calls: Maximum total tool calls allowed
            max_identical_calls: Maximum times the same tool+params can be called
            max_recent_repeats: Maximum repeating pattern length to detect
        """
        self.max_total_calls = max_total_calls
        self.max_identical_calls = max_identical_calls
        self.max_recent_repeats = max_recent_repeats

        # Track all calls
        self.call_history: List[Tuple[str, str]] = []

        # Track counts per unique call
        self.call_counts: Dict[Tuple[str, str], int] = defaultdict(int)

        # Track if loop was detected
        self.loop_detected = False
        self.loop_reason = ""

    def track_call(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Track a tool call and check for loops.

        Args:
            tool_name: Name of the tool being called
            parameters: Parameters passed to the tool

        Returns:
            True if execution should continue, False if loop detected
        """
        # Normalize parameters to string for comparison
        param_str = str(sorted(parameters.items()))
        call_signature = (tool_name, param_str)

        # Add to history
        self.call_history.append(call_signature)
        self.call_counts[call_signature] += 1

        total_calls = len(self.call_history)

        # Check 1: Too many total calls
        if total_calls > self.max_total_calls:
            self.loop_detected = True
            self.loop_reason = f"Exceeded maximum tool calls ({self.max_total_calls})"
            logger.warning(f"Loop detected: {self.loop_reason}")
            return False

        # Check 2: Same call repeated too many times
        if self.call_counts[call_signature] > self.max_identical_calls:
            self.loop_detected = True
            self.loop_reason = (
                f"Tool '{tool_name}' called {self.call_counts[call_signature]} times "
                f"with same parameters (max: {self.max_identical_calls})"
            )
            logger.warning(f"Loop detected: {self.loop_reason}")
            return False

        # Check 3: Repeating pattern in recent calls
        if total_calls >= self.max_recent_repeats * 2:
            recent = self.call_history[-self.max_recent_repeats * 2 :]
            first_half = recent[: self.max_recent_repeats]
            second_half = recent[self.max_recent_repeats :]

            if first_half == second_half:
                self.loop_detected = True
                self.loop_reason = f"Detected repeating pattern: {[t[0] for t in first_half]}"
                logger.warning(f"Loop detected: {self.loop_reason}")
                return False

        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of tracked calls."""
        return {
            "total_calls": len(self.call_history),
            "unique_calls": len(self.call_counts),
            "loop_detected": self.loop_detected,
            "loop_reason": self.loop_reason,
            "call_history": [
                {"tool": tool, "count": count} for (tool, params), count in self.call_counts.items()
            ],
        }

    def reset(self):
        """Reset the tracker for a new execution."""
        self.call_history.clear()
        self.call_counts.clear()
        self.loop_detected = False
        self.loop_reason = ""


class LoopDetectionError(Exception):
    """Raised when an infinite loop is detected."""

    def __init__(self, message: str, tracker_summary: Dict[str, Any]):
        super().__init__(message)
        self.tracker_summary = tracker_summary
