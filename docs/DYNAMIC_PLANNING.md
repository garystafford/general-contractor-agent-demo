# Dynamic Project Planning

The backend now supports **ANY construction project type**, not just the 5 predefined templates!

## Overview

The system uses a **hybrid approach**:

- **Hardcoded templates** for common projects (fast, predictable, no extra cost)
- **Dynamic LLM planning** for arbitrary projects (flexible, uses Claude's construction knowledge)

## Supported Project Types

### Hardcoded Templates (Fast)

These use predefined task sequences:

- `kitchen_remodel` - Kitchen renovation
- `bathroom_remodel` - Bathroom renovation
- `new_construction` - New building construction
- `addition` - Home addition
- `shed_construction` - Storage shed

### Dynamic Planning (Flexible)

**ANY other project type** will automatically use dynamic planning:

- `dog_house` - Build a dog house
- `deck` - Build a deck
- `treehouse` - Build a treehouse
- `fence` - Install a fence
- `pool` - Build a pool
- `garage` - Build a garage
- `gazebo` - Build a gazebo
- ...and literally anything else!

## How It Works

1. **Project Request** → API receives project type
2. **Type Detection** → System checks if it's in the hardcoded list
3. **Planning Decision**:
   - If hardcoded: Use fast template
   - If not hardcoded: Use Planning Agent (LLM)
4. **Planning Agent** (for dynamic projects):
   - Analyzes project requirements
   - Generates task breakdown
   - Determines dependencies
   - Assigns construction phases
   - Selects specialist agents
5. **Execution** → Standard execution flow (same for both)

## Quick Start

### Test Without AWS (Structure Only)

```bash
# Verify the dynamic planning system is integrated
uv run python tests/test_dynamic_structure.py
```

### Test With AWS (Plan Only)

```bash
# Generate a plan for building a dog house (requires AWS)
uv run python tests/test_dynamic_planning.py
```

### Test With AWS (Full Execution)

```bash
# Plan AND execute the dog house project (requires AWS)
uv run python tests/test_dynamic_planning.py execute
```

### Test Multiple Project Types

```bash
# Test planning for dog house, deck, treehouse, and fence
uv run python tests/test_dynamic_planning.py --all
```

## API Usage

### Basic Dynamic Planning (Automatic)

```bash
# Any unsupported type automatically uses dynamic planning
curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "dog_house",
    "description": "Build a medium dog house with weatherproof roof",
    "parameters": {
      "dog_size": "medium",
      "dimensions": {"width": 3, "length": 4, "height": 3}
    }
  }'
```

### Force Dynamic Planning (Optional)

```bash
# Use dynamic planning even for hardcoded types
curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "kitchen_remodel",
    "description": "Modern kitchen renovation",
    "parameters": {},
    "use_dynamic_planning": true
  }'
```

## Example Projects

### Dog House

```json
{
  "project_type": "dog_house",
  "description": "Build a medium dog house with insulated walls",
  "parameters": {
    "dog_size": "medium",
    "weatherproof": true,
    "insulated": true
  }
}
```

### Deck

```json
{
  "project_type": "deck",
  "description": "Build a 12x16 wooden deck with stairs and railing",
  "parameters": {
    "dimensions": { "width": 12, "length": 16 },
    "material": "pressure-treated pine",
    "stairs": true,
    "railing": true
  }
}
```

### Treehouse

```json
{
  "project_type": "treehouse",
  "description": "Build a simple treehouse platform with ladder",
  "parameters": {
    "height": 8,
    "platform_size": "6x8",
    "has_ladder": true,
    "has_railing": true
  }
}
```

### Fence

```json
{
  "project_type": "fence",
  "description": "Install 100 feet of 6-foot privacy fence",
  "parameters": {
    "length": 100,
    "height": 6,
    "style": "privacy",
    "material": "cedar"
  }
}
```

## Architecture

### Planning Agent

**File**: [`backend/agents/project_planner.py`](backend/agents/project_planner.py)

The Planning Agent uses Claude's construction knowledge to:

- Analyze project scope and requirements
- Generate structured task breakdowns
- Validate task dependencies (no circular references)
- Assign appropriate construction phases
- Select the right specialist agents

**Tools**:

- `analyze_project_scope` - Extract project characteristics
- `generate_task_breakdown` - Create task list
- `validate_task_dependencies` - Check dependency graph
- `assign_construction_phases` - Map to timeline
- `finalize_project_plan` - Output structured JSON

### Task Manager

**File**: [`backend/orchestration/task_manager.py`](backend/orchestration/task_manager.py)

**Enhanced with**:

- `SUPPORTED_PROJECT_TYPES` - List of hardcoded types
- `create_tasks_from_plan()` - Convert LLM output to Task objects

### General Contractor

**File**: [`backend/agents/general_contractor.py`](backend/agents/general_contractor.py)

**Enhanced with**:

- `planning_agent` - Lazy-loaded Planning Agent
- `_create_dynamic_project_plan()` - LLM-based planning
- `_parse_planning_result()` - Parse JSON from LLM
- `start_project()` - Auto-detects when to use dynamic planning

### API Routes

**File**: [`backend/api/routes.py`](backend/api/routes.py)

**Enhanced with**:

- `use_dynamic_planning` parameter (optional)
- Better documentation for dynamic planning

## Benefits

### Flexibility

- Build **ANYTHING** - not limited to 5 project types
- System uses LLM's construction knowledge
- No code changes needed for new project types

### Cost Efficiency

- Hardcoded templates: Free (no LLM calls for planning)
- Dynamic planning: Only pays for LLM when needed
- Planning agent is lazy-loaded (only created when used)

### Backward Compatibility

- Existing templates still work exactly the same
- No breaking changes to API
- Opt-in dynamic planning for hardcoded types

### Quality

- LLM understands construction best practices
- Generates logical task sequences
- Validates dependencies automatically
- Assigns appropriate specialist agents

## Requirements

### For Structure Tests (No AWS)

```bash
uv run python tests/test_dynamic_structure.py
```

No requirements - tests the code structure only.

### For Dynamic Planning (With AWS)

```bash
uv run python tests/test_dynamic_planning.py
```

Requires AWS Bedrock access:

- AWS account with Bedrock enabled
- Claude Sonnet 4.5 model access
- AWS credentials configured

**Configure AWS**:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_REGION=us-east-1
export AWS_PROFILE=default
# OR
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

## Cost Considerations

### Hardcoded Templates

- **Cost**: $0 (no LLM calls for planning)
- **Speed**: Instant (no API latency)
- **Use for**: Common projects where template works well

### Dynamic Planning

- **Cost**: ~$0.01-0.05 per planning session (depends on project complexity)
- **Speed**: 5-30 seconds for planning (LLM API calls)
- **Use for**: Arbitrary projects, custom requirements

### Optimization Tips

1. Use hardcoded templates when possible (free and fast)
2. Cache planning results for repeated projects
3. Planning agent is lazy-loaded (only created when needed)
4. Only plan once - execution uses the plan

## Troubleshooting

### "ModuleNotFoundError: No module named 'strands'"

**Solution**: Use `uv run` to execute with proper environment

```bash
uv run python tests/test_dynamic_planning.py
```

### "AWS credentials not found"

**Solution**: Configure AWS credentials

```bash
aws configure
# OR
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### "Could not parse planning agent output"

**Solution**: The LLM didn't return valid JSON. This can happen if:

- The prompt is unclear
- The model is overloaded
- Network issues during API call

Try running again - LLM outputs can vary.

### "Planning agent timed out"

**Solution**: Planning took >2 minutes. This can happen for very complex projects.

- Simplify the project description
- Break large projects into phases
- Check network connectivity

## Examples

### Example 1: Simple Dog House

```bash
uv run python tests/test_dynamic_planning.py
```

**Expected Output**:

- Planning method: dynamic
- Total tasks: 6-10 (depends on LLM)
- Phases: planning, framing, finishing
- Agents: Architect, Carpenter, Painter

### Example 2: Complex Deck

```bash
# Start API server
python start.py

# In another terminal
curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "deck",
    "description": "Build 16x20 deck with stairs, railing, and built-in bench",
    "parameters": {
      "dimensions": {"width": 16, "length": 20},
      "stairs": true,
      "railing": true,
      "bench": true
    }
  }'
```

**Expected Output**:

- Planning method: dynamic
- Total tasks: 10-15 (depends on complexity)
- Phases: planning, foundation, framing, finishing
- Agents: Architect, Carpenter, Mason

## Future Enhancements

Possible improvements:

1. **Plan caching** - Cache plans for common projects
2. **Plan templates** - Save successful plans as reusable templates
3. **Cost estimation** - LLM estimates material costs
4. **Timeline estimation** - LLM predicts project duration
5. **Risk assessment** - LLM identifies potential issues
6. **More agents** - Landscaper, Pool Builder, etc.

## Summary

✅ **What Changed**:

- Added Planning Agent for dynamic task generation
- Enhanced TaskManager to support LLM-generated tasks
- Modified GeneralContractor to auto-detect project types
- Updated API to support `use_dynamic_planning` parameter

✅ **What You Can Do Now**:

- Build **ANY** construction project (not just 5 types)
- System automatically uses LLM when needed
- Hardcoded templates still work (backward compatible)
- No code changes needed for new project types

✅ **How to Test**:

```bash
# Structure test (no AWS)
uv run python tests/test_dynamic_structure.py

# Dog house plan (with AWS)
uv run python tests/test_dynamic_planning.py

# Full execution (with AWS)
uv run python tests/test_dynamic_planning.py execute
```

🎉 **The backend can now build ANYTHING!**

## Additional Examples

```bash
curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "new_kitch",
    "description": "Replace an existing 8x10 kitchen, tile floor, new cabinets, new sink, lighting, and appliances"
  }

  curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "wooden_deck",
    "description": "Build a 12 x 8 wooden deck on the back of an existing house. The deck should have a wooden railing and two steps down to the lawn at the back of the house."
  }'

  curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "dog_house",
    "description": "Build a doghouse for a large dog with insulated walls, a weatherproof roof, and a concrete floor."
  }'
```
