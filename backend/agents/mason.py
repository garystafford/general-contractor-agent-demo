"""
Mason agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class LayBrickWallInput(BaseModel):
    """Input for laying brick walls."""

    wall_length: float = Field(description="Length of wall in feet")
    wall_height: float = Field(description="Height of wall in feet")


class PourConcreteFoundationInput(BaseModel):
    """Input for pouring concrete foundation."""

    length: float = Field(description="Length in feet")
    width: float = Field(description="Width in feet")
    depth: float = Field(description="Depth in feet")


class RepairMasonryInput(BaseModel):
    """Input for repairing masonry."""

    area_sq_ft: float = Field(description="Area to repair in square feet")


class InstallPaversInput(BaseModel):
    """Input for installing pavers."""

    area_sq_ft: float = Field(description="Area to cover in square feet")
    paver_type: str = Field(description="Type of pavers (concrete, brick, stone)")


# Tool Implementations
@tool
def lay_brick_wall(input: LayBrickWallInput) -> dict:
    """Build brick or block walls."""
    brick_count = int(input.wall_length * input.wall_height * 7)  # ~7 bricks per sq ft
    return {
        "status": "completed",
        "wall_length_feet": input.wall_length,
        "wall_height_feet": input.wall_height,
        "bricks_used": brick_count,
        "materials_used": [
            f"{brick_count} bricks",
            "mortar",
            "rebar",
        ],
        "details": f"Laid {input.wall_length}ft x {input.wall_height}ft brick wall",
    }


@tool
def pour_concrete_foundation(input: PourConcreteFoundationInput) -> dict:
    """Pour concrete foundation or slab."""
    cubic_yards = (input.length * input.width * input.depth) / 27
    return {
        "status": "completed",
        "dimensions": f"{input.length}x{input.width}x{input.depth}ft",
        "concrete_cubic_yards": cubic_yards,
        "materials_used": [
            f"{cubic_yards} cubic yards concrete",
            "rebar grid",
            "forms",
        ],
        "details": f"Poured {cubic_yards} cu yd concrete foundation",
    }


@tool
def repair_masonry(input: RepairMasonryInput) -> dict:
    """Repair damaged masonry."""
    return {
        "status": "completed",
        "area_repaired": input.area_sq_ft,
        "materials_used": ["mortar", "replacement bricks/blocks"],
        "details": f"Repaired {input.area_sq_ft} sq ft of masonry",
    }


@tool
def install_pavers(input: InstallPaversInput) -> dict:
    """Install paver patio or walkway."""
    return {
        "status": "completed",
        "area_covered": input.area_sq_ft,
        "paver_type": input.paver_type,
        "materials_used": [
            f"{input.area_sq_ft} sq ft {input.paver_type} pavers",
            "sand base",
            "edge restraints",
        ],
        "details": f"Installed {input.area_sq_ft} sq ft of {input.paver_type} pavers",
    }


@tool
def build_fireplace() -> dict:
    """Build fireplace and chimney."""
    return {
        "status": "completed",
        "materials_used": [
            "firebrick",
            "regular brick/stone",
            "mortar",
            "flue liner",
        ],
        "details": "Built fireplace with chimney",
    }


def create_mason_agent() -> Agent:
    """Create and configure the Mason agent with AWS Bedrock."""
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

    system_prompt = """You are an expert Mason agent specializing in brick, stone, and concrete work.

Your responsibilities include:
- Laying brick and block walls
- Pouring concrete foundations and slabs
- Repairing masonry
- Installing pavers
- Building fireplaces

Ensure proper mixing ratios, level work, and adequate curing time."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            lay_brick_wall,
            pour_concrete_foundation,
            repair_masonry,
            install_pavers,
            build_fireplace,
        ],
    )

    return agent
