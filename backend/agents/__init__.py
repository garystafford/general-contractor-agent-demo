"""
Agent initialization module for Strands Agents framework.
"""

from backend.agents.architect import create_architect_agent
from backend.agents.carpenter import create_carpenter_agent
from backend.agents.electrician import create_electrician_agent
from backend.agents.hvac import create_hvac_agent
from backend.agents.mason import create_mason_agent
from backend.agents.painter import create_painter_agent
from backend.agents.plumber import create_plumber_agent
from backend.agents.project_planner import create_project_planner_agent
from backend.agents.roofer import create_roofer_agent


def initialize_all_agents():
    """
    Initialize all trade agents using Strands Agents framework with AWS Bedrock.

    Returns:
        dict: Dictionary of agent name to Agent instance
    """
    agents = {
        "Architect": create_architect_agent(),
        "Carpenter": create_carpenter_agent(),
        "Electrician": create_electrician_agent(),
        "Plumber": create_plumber_agent(),
        "Mason": create_mason_agent(),
        "Painter": create_painter_agent(),
        "HVAC": create_hvac_agent(),
        "Roofer": create_roofer_agent(),
        "Project Planning": create_project_planner_agent(),
    }

    return agents


__all__ = [
    "initialize_all_agents",
    "create_architect_agent",
    "create_carpenter_agent",
    "create_electrician_agent",
    "create_plumber_agent",
    "create_mason_agent",
    "create_painter_agent",
    "create_hvac_agent",
    "create_roofer_agent",
    "create_project_planner_agent",
]
