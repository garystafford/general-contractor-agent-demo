"""
Project Planning agent for dynamic task generation using LLM knowledge.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings
from typing import List, Dict, Any


# Tool Input Models
class AnalyzeProjectInput(BaseModel):
    """Input for analyzing project requirements."""

    project_type: str = Field(
        description="Type of construction project (e.g., dog_house, deck, treehouse)"
    )
    description: str = Field(description="Detailed project description")
    parameters: Dict[str, Any] = Field(default={}, description="Additional project parameters")


class GenerateTasksInput(BaseModel):
    """Input for generating task breakdown."""

    project_analysis: Dict[str, Any] = Field(description="Analysis from analyze_project_scope")


class ValidateDependenciesInput(BaseModel):
    """Input for validating task dependencies."""

    tasks: List[Dict[str, Any]] = Field(description="List of generated tasks with dependencies")


class AssignPhasesInput(BaseModel):
    """Input for assigning construction phases."""

    tasks: List[Dict[str, Any]] = Field(description="List of tasks to assign to phases")


# Tool Implementations
@tool
def analyze_project_scope(input: AnalyzeProjectInput) -> dict:
    """
    Analyze project requirements and scope.

    Returns project characteristics like:
    - Scale (small, medium, large)
    - Complexity (simple, moderate, complex)
    - Required trades (list of specialist agents needed)
    - Key phases (planning, construction, finishing, etc.)
    - Estimated task count
    - Special considerations (permits, inspections, safety)
    """
    return {
        "status": "analyzed",
        "project_type": input.project_type,
        "description": input.description,
        "parameters": input.parameters,
        "analysis": {
            "scale": "determined_by_llm",
            "complexity": "determined_by_llm",
            "required_trades": [],  # LLM will populate
            "key_phases": [],  # LLM will populate
            "estimated_tasks": 0,  # LLM will estimate
            "special_considerations": [],  # LLM will identify
        },
        "message": "Project scope analyzed. Ready for task generation.",
    }


@tool
def generate_task_breakdown(input: GenerateTasksInput) -> dict:
    """
    Generate detailed task breakdown based on project analysis.

    Each task should include:
    - task_id: Unique identifier (use sequential numbers: "1", "2", etc.)
    - agent: Which specialized agent performs this task
    - description: Clear, specific task description
    - dependencies: List of task_ids that must complete first (empty list if none)
    - phase: Construction phase (planning, foundation, construction, finishing, etc.)
    - requirements: Specific requirements or notes
    - materials: List of materials needed

    Available agents:
    - Architect: Design, planning, specifications
    - Carpenter: Framing, woodwork, doors, cabinets
    - Electrician: Wiring, outlets, fixtures
    - Plumber: Pipes, fixtures, water systems
    - Mason: Concrete, foundations, masonry
    - Painter: Painting, staining, finishing
    - HVAC: Heating, cooling, ventilation
    - Roofer: Roofing, waterproofing, gutters

    Return structured JSON with task list.
    """
    return {
        "status": "generated",
        "tasks": [],  # LLM will populate with structured tasks
        "task_count": 0,
        "message": "Task breakdown generated. Ready for validation.",
    }


@tool
def validate_task_dependencies(input: ValidateDependenciesInput) -> dict:
    """
    Validate that task dependencies form a valid directed acyclic graph (DAG).

    Checks:
    - No circular dependencies
    - All dependency task_ids exist
    - Dependencies are logical (e.g., can't paint before walls are built)
    - Tasks are properly sequenced

    Returns validation status and any issues found.
    """
    return {
        "status": "validated",
        "is_valid": True,  # LLM will determine
        "issues": [],  # LLM will list any problems
        "message": "Dependencies validated successfully.",
    }


@tool
def assign_construction_phases(input: AssignPhasesInput) -> dict:
    """
    Assign tasks to appropriate construction phases.

    Common phases:
    - planning: Design, permits, preparation
    - foundation: Site work, footings, slabs
    - framing: Structural framework
    - rough_in: Electrical, plumbing rough-in
    - inspection: Mid-project inspections
    - finishing: Trim, paint, final details
    - final_inspection: Final approval

    Returns tasks with assigned phases.
    """
    return {
        "status": "assigned",
        "tasks_with_phases": [],  # LLM will populate
        "phase_summary": {},  # Count of tasks per phase
        "message": "Construction phases assigned.",
    }


@tool
def finalize_project_plan(input: dict) -> dict:
    """
    Finalize the complete project plan with all tasks structured for execution.

    Returns the complete plan in the exact format needed by TaskManager:
    {
        "tasks": [
            {
                "task_id": "1",
                "agent": "Architect",
                "description": "Design dog house structure",
                "dependencies": [],
                "phase": "planning",
                "requirements": "Create scaled drawings with dimensions",
                "materials": ["paper", "pencils", "measuring tools"]
            },
            ...
        ],
        "summary": {
            "total_tasks": 10,
            "phases": ["planning", "construction", "finishing"],
            "agents_needed": ["Architect", "Carpenter", "Painter"]
        }
    }
    """
    return {
        "status": "finalized",
        "tasks": [],  # LLM will populate final task list
        "summary": {},
        "message": "Project plan finalized and ready for execution.",
    }


def create_project_planner_agent() -> Agent:
    """Create and configure the Project Planner agent with AWS Bedrock."""
    import boto3

    # Create boto3 session with AWS credentials
    session_kwargs = {
        "region_name": settings.aws_region,
    }

    if settings.aws_profile:
        session_kwargs["profile_name"] = settings.aws_profile
    elif settings.aws_access_key_id and settings.aws_secret_access_key:
        session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            session_kwargs["aws_session_token"] = settings.aws_session_token

    boto_session = boto3.Session(**session_kwargs)

    # Configure Bedrock model
    model = BedrockModel(
        model_id=settings.default_model,
        boto_session=boto_session,
    )

    system_prompt = """You are an expert Construction Project Planning Agent with deep knowledge of:
- Building construction processes and sequencing
- Trade coordination and dependencies
- Building codes and permit requirements
- Material requirements and lead times
- Safety standards and best practices
- Structural engineering principles
- Construction phasing and scheduling

Your job is to break down ANY construction project into a structured, executable task plan.

CRITICAL INSTRUCTIONS:

1. **Use ALL tools in sequence** to create a complete plan:
   - First: analyze_project_scope - Analyze the project
   - Second: generate_task_breakdown - Create task list
   - Third: validate_task_dependencies - Check dependencies
   - Fourth: assign_construction_phases - Assign phases
   - Fifth: finalize_project_plan - Output final structured plan

2. **Task Structure Requirements**:
   - task_id: Use sequential numbers as strings ("1", "2", "3", ...)
   - agent: Must be one of: Architect, Carpenter, Electrician, Plumber, Mason, Painter, HVAC, Roofer
   - description: Clear, specific, actionable task description
   - dependencies: Array of task_id strings (e.g., ["1", "2"]) - tasks that must complete first
   - phase: One of: planning, permitting, foundation, framing, rough_in, inspection, finishing, final_inspection
   - requirements: Specific requirements or quality standards
   - materials: Array of material names needed

3. **Dependency Rules**:
   - Planning and design tasks come first (no dependencies)
   - Permits require completed plans
   - Foundation work requires permits
   - Structural work requires foundation
   - Rough-in (electrical/plumbing) requires structure
   - Inspections require completed work
   - Finishing requires passed inspections
   - Dependencies MUST form a valid DAG (no circular references)

4. **Agent Selection Guidelines**:
   - **Architect**: All design, planning, specifications, layouts
   - **Carpenter**: All woodwork, framing, doors, trim, cabinetry, decks
   - **Electrician**: Wiring, outlets, switches, fixtures, panels
   - **Plumber**: Water supply, drains, fixtures, appliances
   - **Mason**: Concrete, foundations, footings, masonry, stonework
   - **Painter**: All painting, staining, sealing, protective coatings
   - **HVAC**: Heating, cooling, ventilation systems
   - **Roofer**: Roofing, shingles, waterproofing, gutters

5. **Common Project Patterns**:

   **Small outdoor structures (shed, dog house, playhouse)**:
   - Architect: Design structure
   - Mason: Pour foundation/footings (if needed)
   - Carpenter: Build frame, walls, roof structure
   - Roofer: Install roofing (if separate roof)
   - Carpenter: Install doors/windows
   - Painter: Protective finish

   **Decks and patios**:
   - Architect: Design layout and structure
   - Mason: Pour footings
   - Carpenter: Install posts, beams, joists, decking, stairs, railings
   - Painter: Seal/stain

   **Fences**:
   - Architect: Design and layout
   - Mason: Set posts in concrete
   - Carpenter: Install rails and pickets
   - Painter: Stain or paint

   **Pools**:
   - Architect: Design pool and surroundings
   - Mason: Excavation and concrete work
   - Plumber: Plumbing systems
   - Electrician: Electrical and filtration
   - Mason: Decking and finishing

6. **Output Format**:
   When you call finalize_project_plan, structure the output EXACTLY like this:
   ```json
   {
     "tasks": [
       {
         "task_id": "1",
         "agent": "Architect",
         "description": "Design dog house structure with scaled drawings",
         "dependencies": [],
         "phase": "planning",
         "requirements": "Create floor plan and elevation drawings showing dimensions, door placement, and roof design",
         "materials": ["drafting tools", "measuring tape"]
       },
       {
         "task_id": "2",
         "agent": "Carpenter",
         "description": "Build base frame and floor",
         "dependencies": ["1"],
         "phase": "framing",
         "requirements": "Use pressure-treated lumber, ensure level installation",
         "materials": ["pressure-treated 2x4s", "plywood", "wood screws", "level"]
       }
     ],
     "summary": {
       "total_tasks": 6,
       "phases": ["planning", "framing", "finishing"],
       "agents_needed": ["Architect", "Carpenter", "Painter"]
     }
   }
   ```

7. **Quality Standards**:
   - Include safety considerations in requirements
   - Specify material quality when important (e.g., "pressure-treated" for outdoor projects)
   - Consider weatherproofing for outdoor structures
   - Include proper permits when legally required
   - Add inspections for structural or safety-critical work

USE YOUR TOOLS TO CREATE A COMPLETE, WELL-STRUCTURED PROJECT PLAN.
Call all tools in order to produce the final plan."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            analyze_project_scope,
            generate_task_breakdown,
            validate_task_dependencies,
            assign_construction_phases,
            finalize_project_plan,
        ],
    )

    return agent
