# Agent Loop Protection

## Problem

AI agents can sometimes get stuck in infinite loops, repeatedly calling the same tools without recognizing task completion. This was observed with the Roofer agent repeatedly calling `install_underlayment` and `install_shingles` 60+ times.

## Root Cause

The infinite loop occurs because:

1. **LLM doesn't recognize completion:** The agent doesn't understand that calling a tool once successfully completes the task
2. **Parameter confusion:** The agent thinks it needs to "correct" parameters and tries again
3. **No built-in limits:** Strands Agents framework doesn't have native max_iterations parameter
4. **Black box execution:** Tool calls happen inside `agent.invoke_async()` without external visibility - **we cannot intercept individual tool calls**

## Critical Limitation

⚠️ **IMPORTANT:** All tool calls occur **inside** the `agent.invoke_async()` method. We cannot intercept or count individual tool calls from outside. The only effective protection is the **timeout wrapper** that terminates the entire task execution.

The `ToolCallTracker` utility class exists for future use if Strands adds callbacks, but currently **cannot be used** with the existing architecture.

## Solutions Implemented

### 1. Timeout Protection ✅ ACTIVE

**Location:** [backend/agents/general_contractor.py](../backend/agents/general_contractor.py)

Added `asyncio.wait_for()` wrapper around agent task execution with configurable timeout:

```python
timeout_seconds = settings.task_timeout_seconds  # Default: 300 seconds (5 minutes)
result = await asyncio.wait_for(
    agent.invoke_async(task_prompt),
    timeout=timeout_seconds
)
```

**Benefits:**
- ✅ **GUARANTEED** to prevent infinite loops
- Fails gracefully with informative error message
- Configurable via `TASK_TIMEOUT_SECONDS` environment variable

**Effectiveness:** 🟢 **HIGH** - This is the ONLY guaranteed protection currently working

**Default:** 120 seconds (2 minutes) for faster testing, increase to 300-600 for production

### 2. Enhanced System Prompts ⚠️ ADVISORY

**Effectiveness:** 🟡 **MEDIUM** - Helps but not guaranteed

**Location:** [backend/agents/roofer.py](../backend/agents/roofer.py) (and should be applied to all agents)

Added explicit guidelines to agent system prompts:

```
IMPORTANT GUIDELINES:
1. Complete each task ONCE and only once - do not repeat tool calls
2. After calling a tool successfully, the work is done - stop immediately
3. Do NOT call the same tool multiple times with the same parameters
4. When you receive a successful result from a tool, acknowledge it and finish
```

**Benefits:**
- Provides clear instructions to LLM about when to stop
- Reduces likelihood of repeated tool calls
- Makes completion criteria explicit

### 3. Improved Task Prompts

**Location:** [backend/agents/general_contractor.py](../backend/agents/general_contractor.py)

Enhanced task prompt sent to agents:

```
IMPORTANT: Execute each tool call only ONCE. After successfully completing the work
with your tools, provide a summary and finish. Do not repeat tool calls unnecessarily.
```

**Benefits:**
- Reinforces completion behavior at task level
- Works in conjunction with system prompt
- Applies to all tasks uniformly

## Configuration

### Environment Variables

Add to your `.env` file to customize:

```bash
# Task timeout in seconds (default: 300 = 5 minutes)
TASK_TIMEOUT_SECONDS=300
```

### Recommended Settings

- **Development/Testing:** 60-120 seconds (faster failure detection)
- **Production:** 300-600 seconds (allows complex tasks to complete)
- **Debug Mode:** Increase for manual debugging

## Monitoring Loop Behavior

### Signs of Infinite Loops

1. **Repeated Tool Calls:** Same tool called multiple times with identical parameters
2. **Timeout Errors:** Tasks consistently hitting the timeout limit
3. **High Token Usage:** Excessive API calls to AWS Bedrock
4. **No Task Completion:** Tasks showing "in_progress" for extended periods

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Watch for patterns like:
```
Tool #1: install_underlayment
Tool #2: install_shingles
Tool #3: install_underlayment  # ⚠️ Repetition detected!
Tool #4: install_shingles      # ⚠️ Repetition detected!
```

## Future Enhancements

### Recommended Improvements

1. **Tool Call Tracking:**
   - Track tool calls per task
   - Detect repeated calls with same parameters
   - Warn or fail after 3 identical calls

2. **Max Iterations Parameter:**
   - Add native max_iterations to agent configuration
   - Limit total tool calls per task (e.g., 10 max)
   - More graceful than timeout-based approach

3. **Result Validation:**
   - Verify tool results indicate actual progress
   - Detect when agent is "stuck" even without repeating exact calls
   - Implement state change detection

4. **Agent-Specific Limits:**
   - Different timeout values for different agent types
   - Roofer: 5 minutes, Electrician: 3 minutes, etc.
   - Based on expected task complexity

### Example: Tool Call Tracking

```python
class TaskExecutionTracker:
    def __init__(self, max_calls=10, max_repeats=3):
        self.tool_calls = []
        self.max_calls = max_calls
        self.max_repeats = max_repeats

    def track_call(self, tool_name, params):
        call = (tool_name, str(params))
        self.tool_calls.append(call)

        # Check total calls
        if len(self.tool_calls) > self.max_calls:
            raise Exception(f"Max tool calls exceeded: {self.max_calls}")

        # Check for repeats
        recent_calls = self.tool_calls[-self.max_repeats:]
        if len(recent_calls) == self.max_repeats and len(set(recent_calls)) == 1:
            raise Exception(f"Tool loop detected: {tool_name} called {self.max_repeats} times")
```

## Testing Loop Protection

### Test Scenario 1: Timeout Test

```bash
# Set very short timeout
export TASK_TIMEOUT_SECONDS=10

# Run a complex task that should take longer
uv run tests/test_shed_project.py
```

Expected: Task fails with timeout error

### Test Scenario 2: System Prompt Test

Modify a task to explicitly request repeated actions and verify agent stops appropriately.

## Troubleshooting

### Issue: Legitimate Long-Running Tasks Timing Out

**Solution:** Increase `TASK_TIMEOUT_SECONDS` or break task into smaller subtasks

### Issue: Agent Still Repeating After Prompt Updates

**Possible Causes:**
1. Tool results not being properly returned
2. Agent receiving ambiguous task description
3. Task requirements unclear (e.g., "install roof" vs "install underlayment and shingles")

**Solution:** Review task descriptions and tool result formats

### Issue: Timeout Too Aggressive

**Symptom:** Many tasks timing out that should succeed

**Solution:** Increase timeout or optimize agent prompts for faster completion

## Related Files

- [backend/agents/general_contractor.py](../backend/agents/general_contractor.py) - Timeout implementation
- [backend/agents/roofer.py](../backend/agents/roofer.py) - Enhanced system prompt example
- [backend/config.py](../backend/config.py) - Timeout configuration
- [.env.example](../.env.example) - Configuration template

## Best Practices

1. **Always test new agents** for loop behavior before production
2. **Monitor token usage** as indicator of potential loops
3. **Start with conservative timeouts** and increase as needed
4. **Update system prompts** when introducing new tools
5. **Log all tool calls** for debugging loop issues
6. **Review agent responses** during development for completion patterns
