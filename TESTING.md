# Testing Guide

This document explains how to test the General Contractor Agent Demo system.

## Test Scripts

### 1. Simple Agent Test (`test_agent.py`)

Tests a single agent (Carpenter) with a simple task.

```bash
# Run the test
uv run test_agent.py
```

**Status**: ⚠️ Requires valid AWS Bedrock model ID in `.env`

---

### 2. Shed Project Planning (`test_shed_project.py`)

Two modes:
- **Simple Planning** (default): Shows task breakdown without execution
- **Full Execution**: Executes all tasks with AI agents

```bash
# Planning mode (no AI execution)
uv run test_shed_project.py

# Full execution mode (requires AWS)
uv run test_shed_project.py full
```

---

### 3. Detailed Shed Construction (`test_shed_detailed.py`) ⭐ RECOMMENDED

The most comprehensive test showing:
- Complete task breakdown
- Real-time agent reasoning
- Tool calls and results
- Task dependencies

```bash
# Planning mode (no AWS required)
uv run test_shed_detailed.py

# Execution mode with real-time output
uv run test_shed_detailed.py execute
```

**Execution Mode Features**:
- 🤖 Real-time streaming of agent reasoning
- 🔧 Live tool call visualization
- ✓ Tool execution results
- 📊 Task-by-task progress tracking

---

## Project Types Supported

The TaskManager supports these project types:

1. `kitchen_remodel` - Kitchen renovation tasks
2. `bathroom_remodel` - Bathroom renovation tasks
3. `new_construction` - New building construction
4. `addition` - Home addition projects
5. `shed_construction` - Storage shed building (demo) ⭐

---

## Shed Construction Project Details

**Specifications**:
- Dimensions: 10 ft × 12 ft × 8 ft (height)
- Foundation: Concrete slab (120 sq ft)
- Structure: Wood frame
- Roof: Asphalt shingles
- Door: 1 entry door
- Window: 1 window for ventilation
- Electrical: 1 outlet + 1 overhead light
- Finish: Exterior paint

**Task Breakdown**: 10 tasks across 6 phases

**Agents Involved**:
1. Architect - Design plans
2. Mason - Pour foundation
3. Carpenter - Frame walls, roof, siding, doors/windows (5 tasks)
4. Roofer - Install roofing
5. Electrician - Wire electrical
6. Painter - Exterior finish

**Estimated Execution Time**: 5-10 minutes (with valid AWS credentials)

---

## AWS Bedrock Configuration

Before running execution mode, configure your AWS Bedrock credentials:

### Option 1: Using AWS Access Keys

Edit `.env`:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_SESSION_TOKEN=your_token  # Optional, for temporary credentials
AWS_REGION=us-east-1

DEFAULT_MODEL=us.anthropic.claude-sonnet-4-5-v1:0
```

### Option 2: Using AWS Profile

Edit `.env`:
```bash
AWS_PROFILE=default
AWS_REGION=us-east-1

DEFAULT_MODEL=us.anthropic.claude-sonnet-4-5-v1:0
```

### Finding the Correct Model ID

1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Find the exact model ID or inference profile for Claude Sonnet 4.5
4. Common formats:
   - Regional: `us.anthropic.claude-sonnet-4-5-v1:0`
   - Cross-region: `anthropic.claude-sonnet-4-5-20250929-v1:0`
   - ARN: `arn:aws:bedrock:us-east-1::foundation-model/...`

---

## Expected Output (Execution Mode)

When running with execution mode, you'll see:

```
🤖 Agent is thinking and using tools...
--------------------------------------------------------------------------------

💭 I'll design a comprehensive shed plan for a 10x12 ft storage shed...
💭 Let me create the floor plan first...

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

💭 Now I'll create the structural specifications...

✅ TASK COMPLETED
--------------------------------------------------------------------------------
📝 Agent Reasoning: I'll design a comprehensive shed plan...
🔧 Tools Used: create_floor_plan, create_structural_plan
✓ Results: 2 tool(s) executed successfully
```

---

## Troubleshooting

### Error: "The provided model identifier is invalid"

**Solution**: Update `DEFAULT_MODEL` in `.env` with the correct model ID from your AWS Bedrock console.

### Error: "ValidationException: Invocation of model ID ... isn't supported"

**Solution**: You're using a direct model ID instead of an inference profile. Use the regional format: `us.anthropic.claude-sonnet-4-5-v1:0`

### Error: "Extra inputs are not permitted: aws_session_token"

**Solution**: This was fixed in the latest version. Make sure you have the updated `backend/config.py` with the `aws_session_token` field.

### Planning Mode Works but Execution Fails

**Solution**: This is likely an AWS configuration issue. Verify:
1. AWS credentials are valid
2. You have access to AWS Bedrock in the specified region
3. Claude model is enabled in your AWS Bedrock account
4. IAM permissions include `bedrock:InvokeModel`

---

## Next Steps

1. **Review the planning output** to understand the task flow
2. **Configure AWS credentials** in `.env`
3. **Run execution mode** to see AI agents in action
4. **Modify project parameters** in the test scripts to experiment
5. **Create your own project types** by adding to `TaskManager`

---

## Contributing

To add a new project type:

1. Add a new method to `TaskManager`: `_create_[project_type]_tasks()`
2. Add the project type to the `create_project_tasks()` method
3. Create a test script to demonstrate the new project type

Example:
```python
def _create_deck_construction_tasks(self, **kwargs) -> List[Task]:
    """Create tasks for building a deck."""
    return [
        Task("1", "Architect", "Design deck plans", [], "planning"),
        Task("2", "Mason", "Pour concrete footings", ["1"], "foundation"),
        # ... more tasks
    ]
```
