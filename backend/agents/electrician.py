"""
Electrician agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class WireOutletsSwitchesInput(BaseModel):
    """Input for wiring outlets and switches."""

    outlet_count: int = Field(description="Number of outlets to wire")
    switch_count: int = Field(description="Number of switches to wire")


class InstallLightingFixturesInput(BaseModel):
    """Input for installing lighting fixtures."""

    fixture_count: int = Field(description="Number of fixtures to install")
    fixture_type: str = Field(
        description="Type of lighting fixture (recessed, pendant, chandelier, sconce)"
    )


class UpgradeElectricalPanelInput(BaseModel):
    """Input for upgrading electrical panel."""

    panel_amperage: int = Field(description="Panel amperage (100, 200, etc.)")
    circuit_count: int = Field(description="Number of circuit breaker slots")


class RunNewCircuitsInput(BaseModel):
    """Input for running new circuits."""

    circuit_count: int = Field(description="Number of new circuits")
    circuit_type: str = Field(description="Type of circuit (15A, 20A, 30A, GFCI, AFCI)")


class InstallCeilingFansInput(BaseModel):
    """Input for installing ceiling fans."""

    fan_count: int = Field(description="Number of ceiling fans to install")


class TroubleshootWiringInput(BaseModel):
    """Input for troubleshooting wiring."""

    issue_description: str = Field(description="Description of the electrical issue")


# Tool Implementations
@tool
def wire_outlets_switches(input: WireOutletsSwitchesInput) -> dict:
    """Wire electrical outlets and light switches."""
    wire_length = (input.outlet_count + input.switch_count) * 12  # feet per device

    return {
        "status": "completed",
        "outlets_wired": input.outlet_count,
        "switches_wired": input.switch_count,
        "wire_used_feet": wire_length,
        "materials_used": [
            f"{input.outlet_count} electrical outlets",
            f"{input.switch_count} light switches",
            f"{wire_length}ft electrical wire (14/2 or 12/2)",
            "wire nuts and junction boxes",
        ],
        "details": f"Wired {input.outlet_count} outlets and {input.switch_count} switches",
    }


@tool
def install_lighting_fixtures(input: InstallLightingFixturesInput) -> dict:
    """Install various types of lighting fixtures."""
    return {
        "status": "completed",
        "fixtures_installed": input.fixture_count,
        "fixture_type": input.fixture_type,
        "materials_used": [
            f"{input.fixture_count} {input.fixture_type} fixtures",
            "mounting hardware",
            "wire nuts",
        ],
        "details": f"Installed {input.fixture_count} {input.fixture_type} lighting fixtures",
    }


@tool
def upgrade_electrical_panel(input: UpgradeElectricalPanelInput) -> dict:
    """Upgrade the main electrical panel."""
    return {
        "status": "completed",
        "panel_amperage": input.panel_amperage,
        "circuit_capacity": input.circuit_count,
        "materials_used": [
            f"{input.panel_amperage}A electrical panel",
            f"{input.circuit_count} circuit breakers",
            "panel cover and hardware",
        ],
        "details": f"Upgraded to {input.panel_amperage}A panel with {input.circuit_count} circuits",
    }


@tool
def run_new_circuits(input: RunNewCircuitsInput) -> dict:
    """Run new electrical circuits from panel."""
    wire_per_circuit = 50
    total_wire = input.circuit_count * wire_per_circuit

    return {
        "status": "completed",
        "circuits_installed": input.circuit_count,
        "circuit_type": input.circuit_type,
        "total_wire_feet": total_wire,
        "materials_used": [
            f"{total_wire}ft electrical wire",
            f"{input.circuit_count} circuit breakers",
            "conduit and boxes",
        ],
        "details": f"Ran {input.circuit_count} new {input.circuit_type} circuits",
    }


@tool
def install_ceiling_fans(input: InstallCeilingFansInput) -> dict:
    """Install ceiling fans with electrical connections."""
    return {
        "status": "completed",
        "fans_installed": input.fan_count,
        "materials_used": [
            f"{input.fan_count} ceiling fans",
            f"{input.fan_count} fan boxes (rated)",
            "mounting hardware",
        ],
        "details": f"Installed {input.fan_count} ceiling fans",
    }


@tool
def troubleshoot_wiring(input: TroubleshootWiringInput) -> dict:
    """Diagnose and troubleshoot electrical wiring issues."""
    return {
        "status": "completed",
        "issue": input.issue_description,
        "action_taken": "Diagnosed and identified problem",
        "details": f"Troubleshot: {input.issue_description}",
    }


def create_electrician_agent() -> Agent:
    """Create and configure the Electrician agent with AWS Bedrock."""
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

    system_prompt = """You are an expert Electrician agent in a construction project.

Your responsibilities include:
- Wiring outlets and switches
- Installing lighting fixtures
- Upgrading electrical panels
- Running new circuits
- Installing ceiling fans
- Troubleshooting wiring issues

Safety and code compliance are your top priorities. When assigned a task:

1. Verify power is off before starting work
2. Follow National Electrical Code (NEC) standards
3. Use appropriate wire gauges for amperage
4. Ensure proper grounding
5. Test all connections
6. Report completion with details

Always prioritize safety and quality workmanship."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            wire_outlets_switches,
            install_lighting_fixtures,
            upgrade_electrical_panel,
            run_new_circuits,
            install_ceiling_fans,
            troubleshoot_wiring,
        ],
    )

    return agent
