# Current Limitations

This document outlines known limitations in the current implementation and their mitigations.

## 1. Agent Loop Protection ⚠️ CRITICAL

### The Problem

Agents can get stuck in infinite loops, repeatedly calling the same tools without recognizing task completion.

**Example:**
```
Tool #1: install_underlayment
Tool #2: install_shingles
Tool #3: install_underlayment  ← Loop starts
Tool #4: install_shingles
... (continues 60+ times)
```

### Why This Happens

1. **LLM Limitation:** The AI doesn't always recognize when a task is complete
2. **Parameter Confusion:** Agent thinks it needs to "fix" parameters and retries
3. **No Feedback Loop:** Tools return success, but agent doesn't process the result correctly
4. **Black Box Execution:** Tool calls happen inside Strands framework with no external visibility

### Current Protection: Timeout Only

✅ **ACTIVE PROTECTION:**
- **Timeout wrapper** around `agent.invoke_async()`
- Default: **120 seconds** (2 minutes)
- Configuration: `TASK_TIMEOUT_SECONDS` in `.env`

⚠️ **ADVISORY ONLY** (not guaranteed to work):
- Enhanced system prompts telling agents to stop
- Improved tool docstrings with completion messages
- Better task instructions

### The Hard Truth

**We cannot prevent the loop from starting.** We can only **terminate it after timeout**.

This is because:
- Tool calls execute inside `agent.invoke_async()`
- No callbacks or hooks are exposed by Strands
- We cannot count or intercept individual tool calls
- The entire execution is a black box

### What This Means for Users

**Expected Behavior:**
1. Agent starts task execution
2. Agent gets stuck in loop (undetectable from outside)
3. After 2 minutes, timeout fires
4. Task marked as failed with error message
5. Execution continues to next task

**To Adjust Timeout:**

```bash
# In .env file
TASK_TIMEOUT_SECONDS=60   # Faster failure (testing)
TASK_TIMEOUT_SECONDS=300  # More patience (production)
```

### Future Solutions

**Short-term:**
- Continue refining prompts (may reduce frequency, but won't eliminate)
- Monitor and report specific agents/tasks that loop frequently

**Long-term (requires Strands framework changes):**
1. Add `max_iterations` parameter to `Agent()`
2. Add callbacks for tool execution
3. Expose tool call tracking
4. Add built-in loop detection

**Workaround:**
- Break complex tasks into smaller subtasks
- Use more specific task descriptions
- Test agents individually before orchestration

See [LOOP_PROTECTION.md](LOOP_PROTECTION.md) for detailed implementation details.

---

## 2. MCP Server Stability

### The Problem

MCP servers run as separate processes via stdio. Connection issues can occur.

### Current Mitigation

- Health checks before use
- Automatic restart on failure
- Timeout protection on MCP calls

### Known Issues

- Initial connection can be slow
- Stdio buffer can overflow with large payloads
- Process cleanup on abrupt termination

---

## 3. Task Sequencing

### The Problem

Complex task dependencies can create bottlenecks or deadlocks.

### Current Mitigation

- Phase-based sequencing
- Dependency checking before execution
- Maximum iteration limit (50 phases)

### Limitations

- No automatic dependency resolution
- Cannot parallelize tasks with implicit dependencies
- Limited to pre-defined project types

---

## 4. Error Handling

### The Problem

Agent errors can cascade through dependent tasks.

### Current Mitigation

- Try-catch around all agent invocations
- Task status tracking (pending, in_progress, completed, failed)
- Graceful degradation

### Limitations

- No automatic retry logic
- Failed tasks cannot be re-executed without project reset
- No partial rollback capability

---

## 5. Resource Management

### The Problem

Running multiple agents and MCP servers consumes significant resources.

### Current Mitigation

- Process pooling for MCP servers
- Async execution to avoid blocking
- Configurable parallelism limit

### Limitations

- No memory monitoring
- No automatic scaling
- Token usage not tracked or limited

---

## Reporting Issues

If you encounter these limitations in unexpected ways:

1. Check your `TASK_TIMEOUT_SECONDS` configuration
2. Review agent logs for specific error messages
3. Note which agent/task combination triggered the issue
4. Consider if task description could be more specific

For agent loops specifically:
- Note which tools are being called repeatedly
- Check if the task description is ambiguous
- Try breaking the task into smaller pieces

## Summary

| Limitation | Severity | Mitigation | Effectiveness |
|------------|----------|------------|---------------|
| Agent Loops | 🔴 HIGH | Timeout wrapper | 🟢 100% (catches all) |
| MCP Stability | 🟡 MEDIUM | Auto-restart | 🟢 90% |
| Task Sequencing | 🟡 MEDIUM | Dependency checks | 🟢 85% |
| Error Cascade | 🟡 MEDIUM | Status tracking | 🟡 70% |
| Resource Usage | 🟢 LOW | Async execution | 🟢 80% |

**Key Takeaway:** The timeout-based loop protection is **crude but effective**. It will catch all infinite loops, but only after the timeout period. This is currently the best we can do with the Strands framework architecture.
