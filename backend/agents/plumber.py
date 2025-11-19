"""
Plumber agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class InstallSinkInput(BaseModel):
    """Input for installing sink."""

    sink_type: str = Field(description="Type of sink (kitchen, bathroom, utility)")
    faucet_type: str = Field(
        description="Type of faucet (single-handle, double-handle, touchless)"
    )


class InstallToiletInput(BaseModel):
    """Input for installing toilets."""

    toilet_count: int = Field(description="Number of toilets to install")


class InstallShowerInput(BaseModel):
    """Input for installing shower."""

    shower_type: str = Field(description="Type of shower (standard, walk-in, steam)")


class RepairPipesInput(BaseModel):
    """Input for repairing pipes."""

    pipe_length: float = Field(description="Length of pipe in feet")
    pipe_material: str = Field(description="Pipe material (copper, PVC, PEX)")


class UnclogDrainInput(BaseModel):
    """Input for unclogging drain."""

    location: str = Field(description="Location of the drain")


class InstallWaterHeaterInput(BaseModel):
    """Input for installing water heater."""

    capacity_gallons: int = Field(description="Water heater capacity in gallons")
    heater_type: str = Field(
        description="Type of water heater (tank, tankless, hybrid)"
    )


# Tool Implementations
@tool
def install_sink(input: InstallSinkInput) -> dict:
    """Install bathroom or kitchen sink with faucet."""
    return {
        "status": "completed",
        "sink_type": input.sink_type,
        "faucet_type": input.faucet_type,
        "materials_used": [
            f"{input.sink_type} sink",
            f"{input.faucet_type} faucet",
            "drain assembly",
            "supply lines",
        ],
        "details": f"Installed {input.sink_type} sink with {input.faucet_type} faucet",
    }


@tool
def install_toilet(input: InstallToiletInput) -> dict:
    """Install toilets."""
    return {
        "status": "completed",
        "toilets_installed": input.toilet_count,
        "materials_used": [
            f"{input.toilet_count} toilets",
            f"{input.toilet_count} wax rings",
            "supply lines and bolts",
        ],
        "details": f"Installed {input.toilet_count} toilet(s)",
    }


@tool
def install_shower(input: InstallShowerInput) -> dict:
    """Install shower system."""
    return {
        "status": "completed",
        "shower_type": input.shower_type,
        "materials_used": [
            f"{input.shower_type} shower unit",
            "shower valve",
            "drain assembly",
            "fixtures",
        ],
        "details": f"Installed {input.shower_type} shower system",
    }


@tool
def repair_pipes(input: RepairPipesInput) -> dict:
    """Repair or replace pipes."""
    return {
        "status": "completed",
        "pipe_length_feet": input.pipe_length,
        "pipe_material": input.pipe_material,
        "materials_used": [
            f"{input.pipe_length}ft {input.pipe_material} pipe",
            "fittings",
            "solder/adhesive",
        ],
        "details": f"Repaired/replaced {input.pipe_length}ft of {input.pipe_material} pipe",
    }


@tool
def unclog_drain(input: UnclogDrainInput) -> dict:
    """Unclog drains."""
    return {
        "status": "completed",
        "location": input.location,
        "method": "snake/auger",
        "details": f"Unclogged drain at {input.location}",
    }


@tool
def install_water_heater(input: InstallWaterHeaterInput) -> dict:
    """Install water heater."""
    return {
        "status": "completed",
        "capacity": input.capacity_gallons,
        "heater_type": input.heater_type,
        "materials_used": [
            f"{input.capacity_gallons}gal {input.heater_type} water heater",
            "expansion tank",
            "connections",
        ],
        "details": f"Installed {input.capacity_gallons}gal {input.heater_type} water heater",
    }


def create_plumber_agent() -> Agent:
    """Create and configure the Plumber agent with AWS Bedrock."""
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

    system_prompt = """You are an expert Plumber agent in a construction project.

Your responsibilities include:
- Installing sinks and faucets
- Installing toilets
- Installing showers and tubs
- Repairing/replacing pipes
- Unclogging drains
- Installing water heaters

Follow plumbing codes and ensure proper connections. Always test for leaks."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            install_sink,
            install_toilet,
            install_shower,
            repair_pipes,
            unclog_drain,
            install_water_heater,
        ],
    )

    return agent
