# Shed Construction Execution Guide

## Overview

The **detailed shed construction test** (`test_shed_detailed.py`) demonstrates multi-agent orchestration with real-time output of agent reasoning and tool calling.

---

## Quick Start

### Planning Mode (No AWS Required)
```bash
uv run test_shed_detailed.py
```

Shows complete task breakdown, dependencies, and project statistics.

### Execution Mode (Requires AWS Bedrock)
```bash
uv run test_shed_detailed.py execute
```

Executes all 10 tasks with AI agents, showing real-time:
- 💭 Agent reasoning and thinking
- 🔧 Tool calls with parameters
- ✓ Tool execution results
- 📊 Task completion status

---

## What You'll See in Execution Mode

### 1. Task Header
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TASK #1: Design shed plans (10x12 ft)
│ Agent: Architect
│ Phase: PLANNING
└──────────────────────────────────────────────────────────────────────────────┘

📊 Requirements: {
  "width": 10,
  "length": 12,
  "height": 8
}
🔧 Materials: blueprints, specifications
```

### 2. Real-Time Agent Reasoning
```
🤖 Agent is thinking and using tools...
--------------------------------------------------------------------------------

💭 I'll create comprehensive shed plans for this 10x12 ft storage structure.
💭 First, I need to design the floor plan layout.
```

### 3. Tool Calls
```
🔧 Calling tool: create_floor_plan
   Input: {
      "room_type": "shed",
      "dimensions": "10x12",
      "square_footage": 120
   }
✓ Tool completed successfully
   Result: {
      "status": "success",
      "details": "Created floor plan for shed (120 sq ft)"
   }
```

### 4. Task Completion
```
✅ TASK COMPLETED
--------------------------------------------------------------------------------
📝 Agent Reasoning: I'll create comprehensive shed plans...
🔧 Tools Used: create_floor_plan, create_structural_plan
✓ Results: 2 tool(s) executed successfully
```

### 5. Progress Through All Tasks

The system will execute all 10 tasks in sequence:

```
Task 1  → Architect designs plans
Task 2  → Mason pours foundation
Task 3  → Carpenter frames walls
Task 4  → Carpenter builds roof trusses
Task 5  → Roofer installs roofing
Task 6  → Electrician wires electrical
Task 7  → Carpenter installs siding
Task 8  → Carpenter installs door/window
Task 9  → Painter paints exterior
Task 10 → Carpenter final walkthrough
```

### 6. Final Summary
```
================================================================================
📊 PROJECT COMPLETION SUMMARY
================================================================================
✅ Completed: 10/10
❌ Failed: 0
⏳ Pending: 0
```

---

## Key Features

### Real-Time Streaming
- Uses Strands `stream_async()` for live output
- Shows agent reasoning as it happens
- Displays tool calls before execution
- Shows results immediately after completion

### Task Dependencies
- Automatically waits for prerequisite tasks
- Executes tasks in correct sequence
- Handles parallel execution when possible

### Error Handling
- Catches and displays errors gracefully
- Marks failed tasks in task manager
- Continues with remaining tasks when possible

### Detailed Logging
Each task shows:
- **Requirements**: Technical specifications
- **Materials**: Needed supplies
- **Agent Reasoning**: Claude's thinking process
- **Tool Calls**: Which tools were invoked
- **Tool Results**: What each tool returned

---

## Example Full Output

Here's what a complete task execution looks like:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TASK #3: Frame walls and install door/window openings
│ Agent: Carpenter
│ Phase: FRAMING
└──────────────────────────────────────────────────────────────────────────────┘

📊 Requirements: {
  "wall_count": 4,
  "door_count": 1,
  "window_count": 1
}
🔧 Materials: 2x4 lumber, plywood, nails, door frame, window frame

🤖 Agent is thinking and using tools...
--------------------------------------------------------------------------------

💭 I'll frame the four walls of the shed with proper openings for the door and window.
💭 Let me start by framing the walls with 2x4 lumber at 16-inch centers.

🔧 Calling tool: frame_walls
   Input: {
      "wall_count": 4,
      "wall_length": 10.0,
      "stud_spacing": 16
   }
✓ Tool completed successfully
   Result: {
      "status": "success",
      "details": "Framed 4 walls with 10.0ft length and 16\" stud spacing"
   }

💭 Now I'll install the door frame opening.

🔧 Calling tool: install_doors
   Input: {
      "door_count": 1,
      "door_type": "exterior"
   }
✓ Tool completed successfully
   Result: {
      "status": "success",
      "details": "Installed 1 exterior door frames"
   }

💭 The walls are framed and door/window openings are ready.

✅ TASK COMPLETED
--------------------------------------------------------------------------------
📝 Agent Reasoning: I'll frame the four walls of the shed with proper openings...
🔧 Tools Used: frame_walls, install_doors
✓ Results: 2 tool(s) executed successfully
```

---

## Technical Details

### Streaming Implementation

The script uses Strands Agent SDK's streaming API:

```python
async for event in agent.stream_async(task_prompt):
    event_type = event.get("type", "")

    if event_type == "text":
        # Agent reasoning
        print(f"💭 {event.get('text', '')}")

    elif event_type == "tool_use":
        # Tool being called
        print(f"🔧 Calling tool: {event.get('name')}")

    elif event_type == "tool_result":
        # Tool completed
        print(f"✓ Tool completed successfully")
```

### Event Types

- **text**: Agent's reasoning and thinking
- **tool_use**: Tool about to be executed
- **tool_result**: Results from tool execution
- **message**: Complete message structure

---

## Customization

### Modify Project Parameters

Edit the `start_project()` call in the script:

```python
result = await gc.start_project(
    project_description="Your custom description",
    project_type="shed_construction",
    dimensions={"width": 8, "length": 10, "height": 7},  # Customize size
    has_foundation=True,  # Toggle foundation
    has_electrical=False,  # Toggle electrical
    has_plumbing=False,   # Toggle plumbing
)
```

### Add Custom Output

Add custom event handlers:

```python
elif event_type == "custom_event":
    # Handle your custom events
    pass
```

---

## Performance

### Expected Execution Time
- **Planning Mode**: < 1 second
- **Execution Mode**: 5-10 minutes total
  - Each task: 30-60 seconds
  - Depends on AWS Bedrock response time
  - Network latency affects streaming speed

### Cost Considerations
- Uses Claude Sonnet 4.5 on AWS Bedrock
- Cost depends on your AWS pricing
- Typical cost per full execution: ~$0.10-0.50
- Input tokens: ~2,000 per task
- Output tokens: ~500-1,000 per task

---

## Troubleshooting

### Streaming Stops or Hangs
- Check AWS network connectivity
- Verify model ID is correct
- Ensure AWS credentials haven't expired

### No Output After "Agent is thinking..."
- Model may be taking time to respond
- Wait 30-60 seconds
- Check AWS Bedrock console for errors

### Tool Calls Fail
- Agent tools are simulated (return mock data)
- Tools always succeed in this demo
- Real implementation would call actual services

---

## Next Steps

1. **Run Planning Mode** first to understand the flow
2. **Configure AWS credentials** in `.env`
3. **Run Execution Mode** to see AI agents in action
4. **Experiment with parameters** (shed size, features)
5. **Create custom project types** for other construction scenarios

---

## Related Files

- **Test Script**: `test_shed_detailed.py`
- **Configuration**: `backend/config.py`
- **Task Manager**: `backend/orchestration/task_manager.py`
- **General Contractor**: `backend/agents/general_contractor.py`
- **All Agents**: `backend/agents/*.py`

---

## Support

If you encounter issues:
1. Check [TESTING.md](TESTING.md) for configuration help
2. Verify AWS Bedrock model access
3. Review error messages carefully
4. Ensure all agent files have been updated with correct API
