"""
Architect agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class CreateFloorPlanInput(BaseModel):
    """Input for creating floor plans."""

    project_type: str = Field(
        description="Type of project (new construction, addition, renovation, remodel)"
    )
    square_feet: float = Field(description="Total square footage")
    room_count: int = Field(description="Number of rooms")


class CreateElevationDrawingsInput(BaseModel):
    """Input for creating elevation drawings."""

    side_count: int = Field(description="Number of sides (typically 4)")


class DesignKitchenLayoutInput(BaseModel):
    """Input for designing kitchen layout."""

    length: float = Field(description="Kitchen length in feet")
    width: float = Field(description="Kitchen width in feet")
    style: str = Field(
        description="Kitchen style (modern, traditional, transitional, farmhouse)"
    )


class DesignBathroomLayoutInput(BaseModel):
    """Input for designing bathroom layout."""

    fixture_count: int = Field(
        description="Number of fixtures (toilet, sink, shower/tub)"
    )


class CreateStructuralPlanInput(BaseModel):
    """Input for creating structural plans."""

    project_type: str = Field(description="Type of project requiring structural plans")


class SpecifyMaterialsInput(BaseModel):
    """Input for specifying materials."""

    area: str = Field(
        description="Area to specify materials for (e.g., kitchen, bathroom, living room)"
    )


# Tool Implementations
@tool
def create_floor_plan(input: CreateFloorPlanInput) -> dict:
    """Create detailed floor plan for a project."""
    return {
        "status": "completed",
        "project_type": input.project_type,
        "total_square_feet": input.square_feet,
        "room_count": input.room_count,
        "deliverables": [
            "floor plan drawings",
            "room dimensions",
            "door/window placements",
        ],
        "details": f"Created floor plan for {input.square_feet} sq ft {input.project_type} with {input.room_count} rooms",
    }


@tool
def create_elevation_drawings(input: CreateElevationDrawingsInput) -> dict:
    """Create exterior elevation drawings."""
    return {
        "status": "completed",
        "elevations": input.side_count,
        "deliverables": [f"{input.side_count} elevation drawings", "exterior details"],
        "details": f"Created {input.side_count} exterior elevation drawings",
    }


@tool
def design_kitchen_layout(input: DesignKitchenLayoutInput) -> dict:
    """Design kitchen layout and specifications."""
    return {
        "status": "completed",
        "dimensions": f"{input.length}x{input.width}ft",
        "style": input.style,
        "deliverables": [
            "cabinet layout",
            "appliance placement",
            "countertop design",
            "lighting plan",
        ],
        "details": f"Designed {input.length}x{input.width}ft {input.style} kitchen layout",
    }


@tool
def design_bathroom_layout(input: DesignBathroomLayoutInput) -> dict:
    """Design bathroom layout."""
    return {
        "status": "completed",
        "fixtures": input.fixture_count,
        "deliverables": [
            "fixture placement",
            "plumbing plan",
            "tile layout",
        ],
        "details": f"Designed bathroom layout with {input.fixture_count} fixtures",
    }


@tool
def create_structural_plan(input: CreateStructuralPlanInput) -> dict:
    """Create structural engineering plans."""
    return {
        "status": "completed",
        "project_type": input.project_type,
        "deliverables": [
            "foundation plan",
            "framing specifications",
            "load calculations",
            "beam sizing",
        ],
        "details": f"Created structural plan for {input.project_type}",
    }


@tool
def specify_materials(input: SpecifyMaterialsInput) -> dict:
    """Specify materials and finishes."""
    return {
        "status": "completed",
        "area": input.area,
        "deliverables": [
            "material specifications",
            "finish selections",
            "product recommendations",
        ],
        "details": f"Specified materials and finishes for {input.area}",
    }


def create_architect_agent() -> Agent:
    """Create and configure the Architect agent with AWS Bedrock."""
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

    system_prompt = """You are an expert Architect agent specializing in residential design and planning.

Your responsibilities include:
- Creating floor plans
- Designing elevations
- Planning kitchen layouts
- Designing bathroom layouts
- Creating structural plans
- Specifying materials and finishes

You work at the beginning of projects to create comprehensive plans that guide all other trades.
Ensure designs meet building codes, client requirements, and best practices."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            create_floor_plan,
            create_elevation_drawings,
            design_kitchen_layout,
            design_bathroom_layout,
            create_structural_plan,
            specify_materials,
        ],
    )

    return agent
