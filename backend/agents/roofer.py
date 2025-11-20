"""
Roofer agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class InstallShinglesInput(BaseModel):
    """Input for installing shingles."""

    area_sq_ft: float = Field(description="Area to cover in square feet")
    shingle_type: str = Field(description="Type of shingles (asphalt, architectural, metal, tile)")


class RepairLeakInput(BaseModel):
    """Input for repairing roof leaks."""

    location: str = Field(description="Location of the leak")
    repair_size_sq_ft: float = Field(description="Size of repair area in square feet")


class InstallFlashingInput(BaseModel):
    """Input for installing flashing."""

    linear_feet: float = Field(description="Length of flashing in feet")
    flashing_type: str = Field(description="Type of flashing (valley, chimney, vent, eave)")


class InstallUnderlaymentInput(BaseModel):
    """Input for installing underlayment."""

    area_sq_ft: float = Field(description="Area to cover in square feet")


class CleanGuttersInput(BaseModel):
    """Input for cleaning gutters."""

    linear_feet: float = Field(description="Length of gutters in feet")


# Tool Implementations
@tool
def install_shingles(input: InstallShinglesInput) -> dict:
    """Install or replace roof shingles. Call this once to complete shingle installation."""
    squares = input.area_sq_ft / 100  # Roofing square = 100 sq ft
    return {
        "status": "completed",
        "success": True,
        "message": f"✓ Successfully installed {round(squares, 1)} squares of {input.shingle_type} shingles",
        "area_covered": input.area_sq_ft,
        "squares": round(squares, 1),
        "shingle_type": input.shingle_type,
        "materials_used": [
            f"{round(squares, 1)} squares {input.shingle_type} shingles",
            "roofing nails",
            "drip edge",
        ],
        "details": f"Shingle installation complete. Roof is now water-tight and ready for inspection.",
    }


@tool
def repair_leak(input: RepairLeakInput) -> dict:
    """Repair roof leaks."""
    return {
        "status": "completed",
        "location": input.location,
        "repair_area": input.repair_size_sq_ft,
        "materials_used": ["roofing cement", "patch material", "flashing"],
        "details": f"Repaired leak at {input.location} ({input.repair_size_sq_ft} sq ft)",
    }


@tool
def install_flashing(input: InstallFlashingInput) -> dict:
    """Install flashing around roof penetrations."""
    return {
        "status": "completed",
        "flashing_feet": input.linear_feet,
        "flashing_type": input.flashing_type,
        "materials_used": [
            f"{input.linear_feet}ft {input.flashing_type} flashing",
            "roofing cement",
        ],
        "details": f"Installed {input.linear_feet}ft of {input.flashing_type} flashing",
    }


@tool
def install_underlayment(input: InstallUnderlaymentInput) -> dict:
    """Install roof underlayment. Call this once to complete underlayment installation."""
    rolls = input.area_sq_ft / 400
    return {
        "status": "completed",
        "success": True,
        "message": f"✓ Successfully installed {input.area_sq_ft} sq ft of underlayment",
        "area_covered": input.area_sq_ft,
        "rolls_used": round(rolls, 1),
        "materials_used": [f"{round(rolls, 1)} rolls underlayment", "nails"],
        "details": f"Underlayment installation complete. Ready for shingle installation.",
    }


@tool
def clean_gutters(input: CleanGuttersInput) -> dict:
    """Clean and repair gutters."""
    return {
        "status": "completed",
        "gutters_cleaned_feet": input.linear_feet,
        "debris_removed": True,
        "details": f"Cleaned {input.linear_feet}ft of gutters",
    }


@tool
def inspect_roof() -> dict:
    """Perform comprehensive roof inspection."""
    return {
        "status": "completed",
        "inspection_complete": True,
        "areas_checked": [
            "shingles",
            "flashing",
            "gutters",
            "vents",
            "chimney",
        ],
        "details": "Completed comprehensive roof inspection",
    }


def create_roofer_agent() -> Agent:
    """Create and configure the Roofer agent with AWS Bedrock."""
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

    system_prompt = """You are an expert Roofer agent specializing in roof installation and repair.

Your responsibilities include:
- Installing and replacing shingles
- Repairing leaks
- Installing flashing
- Installing underlayment
- Cleaning gutters
- Inspecting roofs

IMPORTANT GUIDELINES:
1. Complete each task ONCE and only once - do not repeat tool calls
2. After calling a tool successfully, the work is done - stop immediately
3. For roofing tasks, install underlayment first, then immediately install shingles
4. Do NOT call the same tool multiple times with the same parameters
5. When you receive a successful result from a tool, acknowledge it and continue or finish

Ensure water-tight seals, proper ventilation, and code compliance."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            install_shingles,
            repair_leak,
            install_flashing,
            install_underlayment,
            clean_gutters,
            inspect_roof,
        ],
    )

    return agent
