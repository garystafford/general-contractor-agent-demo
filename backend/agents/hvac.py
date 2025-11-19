"""
HVAC agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class InstallHeatingSystemInput(BaseModel):
    """Input for installing heating system."""

    system_type: str = Field(
        description="Type of system (gas furnace, electric furnace, boiler, heat pump)"
    )
    btu_capacity: int = Field(description="BTU capacity")


class InstallACUnitInput(BaseModel):
    """Input for installing AC unit."""

    tons: float = Field(description="Cooling capacity in tons")
    seer_rating: int = Field(description="SEER energy efficiency rating")


class InstallDuctworkInput(BaseModel):
    """Input for installing ductwork."""

    linear_feet: float = Field(description="Length of ductwork in feet")
    duct_size: int = Field(description="Duct size in inches")


class InstallThermostatInput(BaseModel):
    """Input for installing thermostat."""

    thermostat_type: str = Field(description="Type of thermostat (basic, programmable, smart)")
    zone_count: int = Field(description="Number of zones")


class PerformMaintenanceInput(BaseModel):
    """Input for performing maintenance."""

    system_type: str = Field(description="System type (heating, cooling, both)")


# Tool Implementations
@tool
def install_heating_system(input: InstallHeatingSystemInput) -> dict:
    """Install or repair heating system."""
    return {
        "status": "completed",
        "system_type": input.system_type,
        "capacity_btu": input.btu_capacity,
        "materials_used": [
            f"{input.system_type} furnace/boiler ({input.btu_capacity} BTU)",
            "ductwork/piping",
            "thermostat",
        ],
        "details": f"Installed {input.btu_capacity} BTU {input.system_type} heating system",
    }


@tool
def install_ac_unit(input: InstallACUnitInput) -> dict:
    """Install or repair AC unit."""
    return {
        "status": "completed",
        "capacity_tons": input.tons,
        "seer_rating": input.seer_rating,
        "materials_used": [
            f"{input.tons} ton AC unit (SEER {input.seer_rating})",
            "refrigerant lines",
            "thermostat connection",
        ],
        "details": f"Installed {input.tons} ton AC unit with SEER {input.seer_rating}",
    }


@tool
def install_ductwork(input: InstallDuctworkInput) -> dict:
    """Install or replace ductwork."""
    return {
        "status": "completed",
        "ductwork_feet": input.linear_feet,
        "duct_size_inches": input.duct_size,
        "materials_used": [
            f'{input.linear_feet}ft {input.duct_size}" ductwork',
            "registers and vents",
            "insulation",
        ],
        "details": f'Installed {input.linear_feet}ft of {input.duct_size}" ductwork',
    }


@tool
def install_thermostat(input: InstallThermostatInput) -> dict:
    """Install thermostat system."""
    return {
        "status": "completed",
        "thermostat_type": input.thermostat_type,
        "zones": input.zone_count,
        "materials_used": [
            f"{input.zone_count} {input.thermostat_type} thermostats",
            "wiring",
        ],
        "details": f"Installed {input.zone_count} {input.thermostat_type} thermostat(s)",
    }


@tool
def perform_maintenance(input: PerformMaintenanceInput) -> dict:
    """Perform seasonal HVAC maintenance."""
    return {
        "status": "completed",
        "system_type": input.system_type,
        "tasks_performed": [
            "filter replacement",
            "system cleaning",
            "performance check",
        ],
        "details": f"Performed seasonal maintenance on {input.system_type}",
    }


def create_hvac_agent() -> Agent:
    """Create and configure the HVAC agent with AWS Bedrock."""
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

    system_prompt = """You are an expert HVAC agent specializing in heating, ventilation, and cooling systems.

Your responsibilities include:
- Installing heating systems
- Installing AC units
- Installing and repairing ductwork
- Installing thermostats
- Performing seasonal maintenance

Ensure proper sizing, efficient operation, and code compliance."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            install_heating_system,
            install_ac_unit,
            install_ductwork,
            install_thermostat,
            perform_maintenance,
        ],
    )

    return agent
