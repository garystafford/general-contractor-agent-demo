# General Contractor Agent Demo

A multi-agent orchestration system demonstrating construction project management using AI agents. This project uses the analogy of a general contractor coordinating specialized trade agents to illustrate how complex, multi-agent AI systems can be designed and orchestrated.

**Built with [Strands Agents](https://strandsagents.com/latest/) framework and AWS Bedrock.**

## Overview

This system models a construction project where a **General Contractor** agent orchestrates multiple specialized trade agents (Architect, Carpenter, Electrician, Plumber, Mason, Painter, HVAC, and Roofer). Each agent has specialized tools and expertise, and the General Contractor manages task dependencies, sequencing, and resource allocation.

### Key Features

- **8 Specialized Trade Agents**: Each with domain-specific tools and expertise
- **Task Dependency Management**: Automatic sequencing based on construction workflows
- **Phase-based Orchestration**: Projects progress through planning, permitting, foundation, framing, rough-in, inspection, and finishing phases
- **Material Management**: Integrated building materials supplier service
- **Permitting System**: Construction permit and inspection management
- **REST API**: Complete API for project management and monitoring
- **Real-time Status Tracking**: Monitor agent status, task progress, and project completion

## Architecture

- **General Contractor (Orchestrator)**

- **Specialized Agents**

  - Architect Agent (design & planning)
  - Carpenter Agent (framing, cabinetry, finishing)
  - Electrician Agent (wiring, fixtures)
  - Plumber Agent (pipes, fixtures)
  - Mason Agent (concrete, masonry)
  - Painter Agent (painting, finishing)
  - HVAC Agent (heating, cooling systems)
  - Roofer Agent (roofing, gutters)

- **Support Services**

  - Materials Supplier (inventory & ordering)
  - Permitting Service (permits & inspections)

- **Task Manager** (dependencies & sequencing)

## Project Structure

```text
general-contractor-agent-demo/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Base agent class
│   │   ├── general_contractor.py   # Orchestration agent
│   │   ├── architect.py            # Design agent
│   │   ├── carpenter.py            # Carpentry agent
│   │   ├── electrician.py          # Electrical agent
│   │   ├── plumber.py              # Plumbing agent
│   │   ├── mason.py                # Masonry agent
│   │   ├── painter.py              # Painting agent
│   │   ├── hvac.py                 # HVAC agent
│   │   └── roofer.py               # Roofing agent
│   ├── mcp_servers/
│   │   ├── __init__.py
│   │   ├── materials_supplier.py   # Materials service
│   │   └── permitting.py           # Permitting service
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── task_manager.py         # Task & dependency management
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py               # FastAPI endpoints
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   └── config.py                   # Configuration settings
├── main.py                         # Application entry point
├── pyproject.toml                  # Project dependencies
├── .env                            # Environment configuration
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

## Getting Started

### Prerequisites

- Python 3.13+
- uv package manager
- AWS account with Bedrock access
- AWS credentials configured (access key ID and secret access key, or IAM role)

### Installation

1. **Install uv package manager** (if not already installed):

   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Or visit [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/) for other installation methods.

2. **Navigate to the project directory**:

   ```bash
   cd general-contractor-agent-demo
   ```

3. **Install dependencies**:

   ```bash
   uv sync
   source .venv/bin/activate
   ```

4. **Set up environment variables**:

   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` file** and add your AWS credentials:

   ```text
   # AWS Bedrock Configuration
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   # Or use AWS profile instead:
   # AWS_PROFILE=default

   # Model Configuration (Bedrock model ID - use inference profile format)
   DEFAULT_MODEL=us.anthropic.claude-sonnet-4-5-v1:0
   ```

   **Note**: You can use either AWS access keys or an AWS profile. If using a profile, comment out the access key lines and uncomment the AWS_PROFILE line.

### AWS Bedrock Setup

Before running the application, you need to enable Claude models in AWS Bedrock:

1. **Log into AWS Console** and navigate to Amazon Bedrock
2. **Enable Model Access**:
   - Go to "Model access" in the left sidebar
   - Click "Enable specific models"
   - Find "Claude" and enable "Claude Sonnet 4.5 v1" (use inference profile: `us.anthropic.claude-sonnet-4-5-v1:0`)
   - Wait for the model to show as "Access granted" (may take a few minutes)
3. **Verify Permissions**:
   - Ensure your IAM user/role has permission to invoke Bedrock models
   - Required permissions: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`

For detailed instructions, see [AWS Bedrock Model Access Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html).

### Testing the Setup

Before running the full application, you can test a single agent:

```bash
# Test the Carpenter agent with AWS Bedrock
uv run python test_agent.py
```

This will verify that:

- AWS credentials are configured correctly
- Bedrock access is working
- The Strands Agents framework is properly set up

### Running the Application

#### Start the API Server

```bash
# Using uv
uv run python main.py

# Or activate the virtual environment first
source .venv/bin/activate
python main.py
```

The API will be available at `http://localhost:8000`

#### API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### 1. Start a New Project

```bash
curl -X POST http://localhost:8000/api/projects/start \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Remodel kitchen with new cabinets and appliances",
    "project_type": "kitchen_remodel",
    "parameters": {}
  }'
```

### 2. Execute the Entire Project

```bash
curl -X POST http://localhost:8000/api/projects/execute-all
```

### 3. Check Project Status

```bash
curl http://localhost:8000/api/projects/status
```

### 4. Get Agent Status

```bash
curl http://localhost:8000/api/agents/Carpenter
```

### 5. View All Tasks

```bash
curl http://localhost:8000/api/tasks
```

### 6. Order Materials

```bash
curl -X POST http://localhost:8000/api/materials/order \
  -H "Content-Type: application/json" \
  -d '{
    "orders": [
      {"material_id": "2x4_studs", "quantity": 100},
      {"material_id": "plywood_sheets", "quantity": 20}
    ]
  }'
```

### 7. Apply for Permit

```bash
curl -X POST http://localhost:8000/api/permits/apply \
  -H "Content-Type: application/json" \
  -d '{
    "permit_type": "building",
    "project_address": "123 Main St",
    "project_description": "Kitchen remodel",
    "applicant": "General Contractor"
  }'
```

## Project Types

The system supports several pre-configured project types with automatic task sequencing:

### Kitchen Remodel

- Architectural design
- Permit application
- Demolition
- Plumbing & electrical rough-in
- Inspection
- Cabinet installation
- Fixture installation
- Painting
- Final inspection

### Bathroom Remodel

- Design and planning
- Permitting
- Demolition
- Plumbing & electrical work
- Drywall and finishing
- Fixture installation
- Final inspection

### New Construction

- Architectural plans
- Building permits
- Foundation
- Framing
- Roofing
- Systems (electrical, plumbing, HVAC)
- Inspections
- Finishing work
- Final inspection

### Home Addition

- Design
- Permits
- Foundation
- Framing
- Roof extension
- System integration
- Finishing

## Specialized Agents

Each agent has specific tools for their trade:

### Carpenter

- Frame walls
- Install doors
- Build cabinets
- Install wood flooring
- Hang drywall
- Build stairs

### Electrician

- Wire outlets/switches
- Install lighting fixtures
- Upgrade electrical panel
- Run new circuits
- Install ceiling fans
- Troubleshoot wiring

### Plumber

- Install sinks
- Install toilets
- Install showers
- Repair/replace pipes
- Unclog drains
- Install water heaters

### Mason

- Lay brick walls
- Pour concrete foundations
- Repair masonry
- Install pavers
- Build fireplaces

### Painter

- Paint interior walls
- Paint exterior
- Prime surfaces
- Remove old paint
- Refinish cabinets
- Apply wallpaper

### HVAC

- Install heating systems
- Install AC units
- Install ductwork
- Install thermostats
- Perform maintenance

### Roofer

- Install shingles
- Repair leaks
- Install flashing
- Install underlayment
- Clean gutters
- Inspect roof

### Architect

- Create floor plans
- Create elevation drawings
- Design kitchen layouts
- Design bathroom layouts
- Create structural plans
- Specify materials

## API Endpoints

### Project Management

- `POST /api/projects/start` - Start a new project
- `POST /api/projects/execute-next-phase` - Execute next phase
- `POST /api/projects/execute-all` - Execute entire project
- `GET /api/projects/status` - Get project status
- `POST /api/projects/reset` - Reset for new project

### Agent Management

- `GET /api/agents` - List all agents
- `GET /api/agents/status` - Get all agents' status
- `GET /api/agents/{agent_name}` - Get specific agent status

### Task Management

- `GET /api/tasks` - Get all tasks
- `GET /api/tasks/{task_id}` - Get specific task details

### Materials

- `GET /api/materials/catalog` - Get materials catalog
- `POST /api/materials/check-availability` - Check material availability
- `POST /api/materials/order` - Order materials
- `GET /api/materials/orders/{order_id}` - Get order details

### Permitting

- `POST /api/permits/apply` - Apply for permit
- `GET /api/permits/{permit_id}` - Check permit status
- `POST /api/permits/inspections` - Schedule inspection
- `GET /api/permits/inspections/{inspection_id}` - Get inspection details
- `POST /api/permits/required` - Get required permits for project

## Configuration

Configuration is managed through environment variables (`.env` file):

```text
# AWS Bedrock Configuration (Required)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
# Or use AWS profile:
# AWS_PROFILE=default

# Model Configuration (Required - Bedrock inference profile)
DEFAULT_MODEL=us.anthropic.claude-sonnet-4-5-v1:0

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000

# Project Settings (optional)
MAX_PARALLEL_TASKS=3
TASK_TIMEOUT_SECONDS=300

# Logging (optional)
LOG_LEVEL=INFO
```

## Development

### Project Dependencies

The project uses uv for dependency management. All dependencies are defined in `pyproject.toml`:

- **strands-agents**: Multi-agent framework for building AI systems (includes Claude API client as transitive dependency)
- **boto3**: AWS SDK for Python (Bedrock integration)
- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **pydantic-settings**: Settings management
- **python-dotenv**: Environment variable loading
- **httpx**: HTTP client

### Adding New Agents

To add a new specialized agent using Strands Agents framework:

1. Create a new file in `backend/agents/` (e.g., `new_agent.py`)
2. Define Pydantic models for tool inputs
3. Create tools using the `@tool` decorator
4. Create an agent factory function

Example:

```python
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings

# Tool Input Model
class PerformTaskInput(BaseModel):
    """Input for performing a task."""
    task_name: str = Field(description="Name of the task")
    complexity: int = Field(description="Task complexity (1-10)")

# Tool Implementation
@tool
def perform_task(input: PerformTaskInput) -> dict:
    """Perform a specific task."""
    return {
        "status": "completed",
        "task": input.task_name,
        "complexity": input.complexity,
        "details": f"Completed {input.task_name} with complexity {input.complexity}"
    }

# Agent Factory
def create_new_agent() -> Agent:
    """Create and configure the New agent with AWS Bedrock."""
    model = BedrockModel(
        model_id=settings.default_model,
        region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        aws_profile=settings.aws_profile,
    )

    agent = Agent(
        name="NewAgent",
        model=model,
        instructions="You are an expert agent...",
        tools=[perform_task],
    )

    return agent
```

Then add the new agent to `backend/agents/__init__.py` in the `initialize_all_agents()` function.

### Task Sequencing

Tasks are automatically sequenced based on:

1. **Dependencies**: Tasks wait for prerequisite tasks to complete
2. **Phases**: Tasks are organized into construction phases
3. **Agent Availability**: Agents can only work on one task at a time

Phase order:

1. Planning
2. Permitting
3. Foundation
4. Framing
5. Rough-in
6. Inspection
7. Finishing
8. Final Inspection

## Educational Value

This project demonstrates key concepts in multi-agent AI systems:

1. **Agent Orchestration**: How a central agent coordinates multiple specialized agents
2. **Task Dependencies**: Managing prerequisites and sequencing
3. **Tool Use**: Agents using specialized tools to accomplish tasks
4. **State Management**: Tracking project and agent states
5. **Resource Allocation**: Coordinating shared resources (materials, permits)
6. **Error Handling**: Managing failures and retries
7. **Parallel Execution**: Running independent tasks simultaneously
8. **Real-world Modeling**: Applying AI agents to complex domain problems

## Limitations & Future Enhancements

### Current Limitations

- Simplified MCP server implementations (not full MCP protocol)
- No persistent storage (in-memory only)
- No authentication/authorization
- Frontend not yet implemented

### Planned Enhancements

- Full MCP server protocol implementation
- AWS Cloudscape React frontend
- Database integration for persistence
- Authentication and user management
- Cost estimation and budget tracking
- Timeline visualization
- Agent performance metrics
- Multi-project support
- Real-time WebSocket updates

## Troubleshooting

### Common Issues

**Issue**: `Module 'backend' not found`

- **Solution**: Make sure you're running from the project root directory

**Issue**: `AWS credentials not found` or `botocore.exceptions.NoCredentialsError`

- **Solution**: Ensure `.env` file exists with AWS credentials set (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) or `AWS_PROFILE` configured

**Issue**: `AccessDeniedException` when invoking Bedrock

- **Solution**:
  - Verify Claude Sonnet 4.5 v1 model is enabled in AWS Bedrock console
  - Check your IAM user/role has `bedrock:InvokeModel` permission
  - Confirm you're using the correct region (default: `us-east-1`)

**Issue**: `ValidationException: The provided model identifier is invalid`

- **Solution**: Verify the inference profile in `.env` matches the format: `us.anthropic.claude-sonnet-4-5-v1:0`

**Issue**: `Port 8000 already in use`

- **Solution**: Change `API_PORT` in `.env` or stop the other service using port 8000

**Issue**: Agent not responding

- **Solution**: Check logs for errors, verify AWS credentials are valid and Bedrock access is enabled

## License

This project is for educational and training purposes.

## Contributing

This is a training workshop project. Feedback and suggestions are welcome!

## Acknowledgments

- Built with [Strands Agents](https://strandsagents.com/latest/) framework
- Powered by Claude via AWS Bedrock
- Inspired by real-world construction project management
- Designed to demonstrate multi-agent AI orchestration patterns

---

For questions or issues, please refer to the API documentation at http://localhost:8000/docs
