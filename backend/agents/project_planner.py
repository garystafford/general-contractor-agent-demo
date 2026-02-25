"""
Project Planning agent for dynamic task generation using LLM knowledge.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from strands import Agent, tool
from strands.models import BedrockModel

from backend.config import settings

logger = logging.getLogger(__name__)

# Global storage for the last finalized plan (thread-safe for single-threaded async)
_last_finalized_plan: Optional[Dict[str, Any]] = None


def get_last_finalized_plan() -> Optional[Dict[str, Any]]:
    """Get the last finalized plan from the planning agent."""
    global _last_finalized_plan
    return _last_finalized_plan


def clear_last_finalized_plan():
    """Clear the stored plan."""
    global _last_finalized_plan
    _last_finalized_plan = None


# Tool Input Models - Using simple confirmations to avoid LLM looping
class AnalyzeProjectInput(BaseModel):
    """Input for analyzing project requirements."""

    confirmation: str = Field(default="ready", description="Confirm ready to analyze")


class GenerateTasksInput(BaseModel):
    """Input for generating task breakdown."""

    confirmation: str = Field(default="ready", description="Confirm ready to generate tasks")


class ValidateDependenciesInput(BaseModel):
    """Input for validating task dependencies."""

    confirmation: str = Field(default="ready", description="Confirm ready to validate")


class AssignPhasesInput(BaseModel):
    """Input for assigning construction phases."""

    confirmation: str = Field(default="ready", description="Confirm ready to assign phases")


# Tool Implementations
@tool
def analyze_project_scope(input: AnalyzeProjectInput) -> dict:
    """
    Analyze project requirements. Call ONCE, then call generate_task_breakdown.
    The project details are in the conversation - use your construction knowledge.
    DO NOT call this tool again after receiving a response.
    """
    return {
        "status": "complete",
        "instruction": "STOP calling analyze_project_scope. Call generate_task_breakdown NOW.",
    }


@tool
def generate_task_breakdown(input: GenerateTasksInput) -> dict:
    """
    Generate task breakdown. Call ONCE, then call validate_task_dependencies.
    Use your construction knowledge to create the task list.
    DO NOT call this tool again after receiving a response.
    """
    return {
        "status": "complete",
        "instruction": "STOP calling generate_task_breakdown. Call validate_task_dependencies NOW.",
    }


@tool
def validate_task_dependencies(input: ValidateDependenciesInput) -> dict:
    """
    Validate task dependencies. Call ONCE, then call assign_construction_phases.
    DO NOT call this tool again after receiving a response.
    """
    return {
        "status": "complete",
        "instruction": "STOP calling validate_task_dependencies. Call assign_construction_phases NOW.",
    }


@tool
def assign_construction_phases(input: AssignPhasesInput) -> dict:
    """
    Assign construction phases. Call ONCE, then call finalize_project_plan WITH YOUR JSON TASK LIST.
    """
    return {
        "status": "complete",
        "instruction": "Call finalize_project_plan NOW. Pass your complete task list as JSON input with 'tasks' array and 'summary' object.",
    }


@tool
def finalize_project_plan(input: dict) -> dict:
    """
    FINAL TOOL - Pass your complete task list as JSON input.

    Required input format:
    {
        "tasks": [{"task_id": "1", "agent": "...", "description": "...", "dependencies": [], "phase": "...", "requirements": "...", "materials": [...]}],
        "summary": {"total_tasks": N, "phases": [...], "agents_needed": [...]}
    }
    """
    global _last_finalized_plan

    tasks = input.get("tasks", [])
    summary = input.get("summary", {})

    # Validate we got actual tasks
    if not tasks:
        logger.warning("finalize_project_plan called without tasks")
        return {
            "status": "error",
            "message": "No tasks provided. You must pass your task list as JSON input to this tool.",
        }

    # Store the plan globally so it can be retrieved after agent completes
    _last_finalized_plan = {
        "tasks": tasks,
        "summary": summary,
    }
    logger.info(f"finalize_project_plan: Stored {len(tasks)} tasks")

    return {
        "status": "finalized",
        "tasks": tasks,
        "summary": summary,
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

    system_prompt = """You are a Construction Project Planner.

WORKFLOW - Call each tool EXACTLY ONCE in order:
1. analyze_project_scope - Start here
2. generate_task_breakdown - Build your task list mentally
3. validate_task_dependencies - Check your dependencies
4. assign_construction_phases - Finalize phases
5. finalize_project_plan - PASS YOUR COMPLETE JSON HERE

CRITICAL: The finalize_project_plan tool MUST receive your complete task list as JSON input.
Do NOT just describe the plan in text. You MUST pass the actual JSON data to the tool.

AGENTS: Architect, Carpenter, Electrician, Plumber, Mason, Painter, HVAC, Roofer
PHASES: planning, permitting, foundation, framing, rough_in, inspection, finishing, final_inspection

AVAILABLE MATERIALS (use these exact names in the materials array):
- Lumber: "2x4 lumber", "plywood", "lumber"
- Electrical: "electrical wire", "outlets", "light fixtures"
- Plumbing: "pvc pipes", "copper pipes", "sink"
- Masonry: "concrete", "bricks"
- Paint: "interior paint", "primer"
- HVAC: "hvac unit", "ductwork"
- Roofing: "shingles", "underlayment"

REQUIRED JSON FORMAT for finalize_project_plan input:
{
  "tasks": [
    {"task_id": "1", "agent": "Architect", "description": "Design layout", "dependencies": [], "phase": "planning", "requirements": "Include dimensions", "materials": []},
    {"task_id": "2", "agent": "Carpenter", "description": "Frame walls", "dependencies": ["1"], "phase": "framing", "requirements": "4 walls", "materials": ["2x4 lumber", "plywood"]},
    {"task_id": "3", "agent": "Electrician", "description": "Install wiring", "dependencies": ["2"], "phase": "rough_in", "requirements": "outlets and lights", "materials": ["electrical wire", "outlets", "light fixtures"]}
  ],
  "summary": {"total_tasks": 10, "phases": ["planning", "framing"], "agents_needed": ["Architect", "Carpenter"]}
}

IMPORTANT: Every task that involves physical work MUST include a "materials" array with the materials needed.
Only planning, inspection, and permit tasks should have empty materials arrays.

TASK SCOPE RULES:
- Each task description must be a SINGLE focused action, NOT a combination of multiple activities.
- Break inspection tasks into SEPARATE tasks per system (e.g., "Inspect structural framing" and "Inspect electrical rough-in" as separate tasks, NOT one combined inspection task).
- Task descriptions must be under 200 characters.
- Prefer more smaller tasks over fewer large tasks.

NEVER call the same tool twice. After tool returns, call the NEXT tool immediately."""

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
