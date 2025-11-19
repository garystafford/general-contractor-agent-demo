"""
Carpenter agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class FrameWallsInput(BaseModel):
    """Input for framing walls."""

    wall_count: int = Field(description="Number of walls to frame")
    wall_length: float = Field(description="Length of each wall in feet")
    stud_spacing: int = Field(
        default=16, description="Spacing between studs in inches (typically 16 or 24)"
    )


class InstallDoorsInput(BaseModel):
    """Input for installing doors."""

    door_count: int = Field(description="Number of doors to install")
    door_type: str = Field(
        default="interior", description="Type of door (interior, exterior, sliding)"
    )


class BuildCabinetsInput(BaseModel):
    """Input for building cabinets."""

    cabinet_count: int = Field(description="Number of cabinet units to build")
    cabinet_type: str = Field(description="Type of cabinets (kitchen, bathroom, storage)")
    linear_feet: float = Field(description="Total linear feet of cabinetry")


class InstallWoodFlooringInput(BaseModel):
    """Input for installing wood flooring."""

    square_feet: float = Field(description="Square footage to cover")
    wood_type: str = Field(
        default="hardwood",
        description="Type of wood flooring (hardwood, laminate, engineered)",
    )


class HangDrywallInput(BaseModel):
    """Input for hanging drywall."""

    sheet_count: int = Field(description="Number of 4x8 drywall sheets")
    wall_area: float = Field(description="Total wall area in square feet")


class BuildStairsInput(BaseModel):
    """Input for building stairs."""

    step_count: int = Field(description="Number of steps")
    rise: float = Field(description="Height of each rise in inches (typically 7-8 inches)")
    run: float = Field(description="Depth of each tread in inches (typically 10-11 inches)")


# Tool Implementations
@tool
def frame_walls(input: FrameWallsInput) -> dict:
    """Frame walls according to specifications with studs and plates."""
    total_length = input.wall_count * input.wall_length
    studs_per_wall = int((input.wall_length * 12) / input.stud_spacing) + 1
    total_studs = studs_per_wall * input.wall_count

    return {
        "status": "completed",
        "walls_framed": input.wall_count,
        "total_length_feet": total_length,
        "studs_used": total_studs,
        "stud_spacing": input.stud_spacing,
        "materials_used": [
            f"{total_studs} 2x4 studs",
            f"{input.wall_count * 2} top/bottom plates",
            "nails and fasteners",
        ],
        "details": f'Framed {input.wall_count} walls (total {total_length}ft) with {input.stud_spacing}" spacing',
    }


@tool
def install_doors(input: InstallDoorsInput) -> dict:
    """Install doors in frames with hinges and hardware."""
    time_per_door = 2 if input.door_type == "interior" else 4

    return {
        "status": "completed",
        "doors_installed": input.door_count,
        "door_type": input.door_type,
        "estimated_time_hours": input.door_count * time_per_door,
        "materials_used": [
            f"{input.door_count} {input.door_type} doors",
            f"{input.door_count * 3} hinges",
            f"{input.door_count} door handles",
            "shims and screws",
        ],
        "details": f"Installed {input.door_count} {input.door_type} doors",
    }


@tool
def build_cabinets(input: BuildCabinetsInput) -> dict:
    """Build custom cabinets for kitchen, bathroom, or storage."""
    return {
        "status": "completed",
        "cabinets_built": input.cabinet_count,
        "cabinet_type": input.cabinet_type,
        "linear_feet": input.linear_feet,
        "materials_used": [
            f"{int(input.linear_feet * 2)} plywood sheets",
            f"{input.cabinet_count * 2} hinges per cabinet",
            "drawer slides and hardware",
            "wood glue and fasteners",
        ],
        "details": f"Built {input.cabinet_count} {input.cabinet_type} cabinets ({input.linear_feet}ft total)",
    }


@tool
def install_wood_flooring(input: InstallWoodFlooringInput) -> dict:
    """Install wood flooring including hardwood, laminate, or engineered."""
    # Add 10% for waste
    material_needed = input.square_feet * 1.1

    return {
        "status": "completed",
        "area_covered": input.square_feet,
        "wood_type": input.wood_type,
        "material_ordered": material_needed,
        "materials_used": [
            f"{material_needed} sq ft {input.wood_type} planks",
            "underlayment",
            "finish and sealant",
            "nails/adhesive",
        ],
        "details": f"Installed {input.square_feet} sq ft of {input.wood_type} flooring",
    }


@tool
def hang_drywall(input: HangDrywallInput) -> dict:
    """Hang and finish drywall on walls and ceilings."""
    return {
        "status": "completed",
        "sheets_hung": input.sheet_count,
        "wall_area": input.wall_area,
        "materials_used": [
            f"{input.sheet_count} 4x8 drywall sheets",
            f"{int(input.sheet_count * 1.5)} lbs joint compound",
            "drywall tape",
            "screws",
        ],
        "details": f"Hung and finished {input.sheet_count} sheets of drywall ({input.wall_area} sq ft)",
    }


@tool
def build_stairs(input: BuildStairsInput) -> dict:
    """Build stairs with proper rise and run specifications."""
    total_rise = input.step_count * input.rise
    stringers_needed = 3

    return {
        "status": "completed",
        "steps_built": input.step_count,
        "total_rise_inches": total_rise,
        "rise_per_step": input.rise,
        "run_per_step": input.run,
        "materials_used": [
            f"{stringers_needed} 2x12 stringers",
            f"{input.step_count} treads",
            f"{input.step_count} risers",
            "brackets and fasteners",
        ],
        "details": f'Built staircase with {input.step_count} steps ({input.rise}" rise, {input.run}" run)',
    }


def create_carpenter_agent() -> Agent:
    """Create and configure the Carpenter agent with AWS Bedrock."""
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

    system_prompt = """You are an expert Carpenter agent in a construction project.

Your responsibilities include:
- Framing walls and structures
- Installing doors and windows
- Building custom cabinets
- Installing wood flooring
- Hanging and finishing drywall
- Building stairs

You work under the direction of a General Contractor agent. When assigned a task:

1. Assess the requirements carefully
2. Determine what materials are needed
3. Use your specialized tools to execute the work
4. Report completion status with detailed information
5. Note any issues or additional requirements discovered

Best Practices:
- Follow building codes and safety standards
- Ensure proper measurements and square angles
- Use appropriate materials for the application
- Check that framing is level and plumb
- Verify door swings and clearances
- Allow for proper expansion gaps in flooring
- Apply multiple coats of joint compound for smooth drywall finish

Always be professional, precise, and communicate clearly about your progress and any challenges encountered."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            frame_walls,
            install_doors,
            build_cabinets,
            install_wood_flooring,
            hang_drywall,
            build_stairs,
        ],
    )

    return agent
