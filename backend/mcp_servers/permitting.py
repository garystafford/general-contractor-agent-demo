"""
Permitting Service MCP Server.

This MCP server provides tools for managing construction permits and inspections,
including permit applications, status checking, inspection scheduling, and
determining required permits for projects.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Pydantic models for input validation
class ApplyForPermitInput(BaseModel):
    """Input for applying for a permit."""

    permit_type: str = Field(
        ...,
        description="Type of permit (building, electrical, plumbing, mechanical, demolition, "
        "roofing)",
    )
    project_address: str = Field(..., description="Address of construction project")
    project_description: str = Field(..., description="Description of work to be performed")
    applicant: str = Field(..., description="Name of applicant/contractor")


class CheckPermitStatusInput(BaseModel):
    """Input for checking permit status."""

    permit_id: str = Field(..., description="ID of the permit to check")


class ScheduleInspectionInput(BaseModel):
    """Input for scheduling an inspection."""

    permit_id: str = Field(..., description="ID of the associated permit")
    inspection_type: str = Field(
        ..., description="Type of inspection (framing, electrical, plumbing, final)"
    )
    requested_date: Optional[str] = Field(None, description="Requested date in ISO format")


class GetRequiredPermitsInput(BaseModel):
    """Input for determining required permits."""

    project_type: str = Field(
        ..., description="Type of project (new_construction, renovation, addition)"
    )
    work_items: List[str] = Field(
        ..., description="List of work items (framing, electrical, plumbing, hvac, etc.)"
    )


class GetInspectionInput(BaseModel):
    """Input for retrieving inspection details."""

    inspection_id: str = Field(..., description="Inspection ID to retrieve")


class PermittingService:
    """Service for construction permits and inspections."""

    def __init__(self):
        self.permits = {}
        self.inspections = {}
        self.permit_counter = 0
        self.inspection_counter = 0
        logger.info("Permitting Service initialized")

    def apply_for_permit(
        self,
        permit_type: str,
        project_address: str,
        project_description: str,
        applicant: str,
    ) -> Dict[str, Any]:
        """
        Apply for a construction permit.

        Args:
            permit_type: Type of permit (building, electrical, plumbing, mechanical)
            project_address: Address of construction project
            project_description: Description of work to be performed
            applicant: Name of applicant/contractor

        Returns:
            Permit application confirmation
        """
        self.permit_counter += 1
        permit_id = f"PERMIT_{self.permit_counter}_{datetime.now().strftime('%Y%m%d')}"

        # Calculate processing time based on permit type
        processing_times = {
            "building": 10,
            "electrical": 5,
            "plumbing": 5,
            "mechanical": 5,
            "demolition": 7,
            "roofing": 3,
        }

        days = processing_times.get(permit_type, 5)
        approval_date = datetime.now() + timedelta(days=days)

        permit = {
            "permit_id": permit_id,
            "type": permit_type,
            "status": "submitted",
            "project_address": project_address,
            "description": project_description,
            "applicant": applicant,
            "submission_date": datetime.now().isoformat(),
            "estimated_approval": approval_date.isoformat(),
            "fee": self._calculate_permit_fee(permit_type),
        }

        self.permits[permit_id] = permit

        logger.info(f"Permit {permit_id} application submitted")

        return {
            "status": "success",
            "permit": permit,
            "message": f"Permit application submitted. Estimated approval in {days} business days.",
        }

    def check_permit_status(self, permit_id: str) -> Dict[str, Any]:
        """Check the status of a permit application."""
        if permit_id in self.permits:
            return {"status": "success", "permit": self.permits[permit_id]}
        return {"status": "error", "message": "Permit not found"}

    def schedule_inspection(
        self, permit_id: str, inspection_type: str, requested_date: str = None
    ) -> Dict[str, Any]:
        """
        Schedule a construction inspection.

        Args:
            permit_id: ID of the associated permit
            inspection_type: Type of inspection (framing, electrical, plumbing, final)
            requested_date: Requested date for inspection (ISO format)

        Returns:
            Inspection scheduling confirmation
        """
        if permit_id not in self.permits:
            return {"status": "error", "message": "Invalid permit ID"}

        self.inspection_counter += 1
        inspection_id = f"INSP_{self.inspection_counter}"

        # Use requested date or schedule for tomorrow
        if requested_date:
            scheduled_date = requested_date
        else:
            scheduled_date = (datetime.now() + timedelta(days=1)).isoformat()

        inspection = {
            "inspection_id": inspection_id,
            "permit_id": permit_id,
            "type": inspection_type,
            "status": "scheduled",
            "scheduled_date": scheduled_date,
            "result": None,
            "notes": None,
        }

        self.inspections[inspection_id] = inspection

        logger.info(f"Inspection {inspection_id} scheduled for {scheduled_date}")

        return {
            "status": "success",
            "inspection": inspection,
            "message": f"Inspection scheduled for {scheduled_date}",
        }

    def get_required_permits(self, project_type: str, work_items: List[str]) -> Dict[str, Any]:
        """
        Determine what permits are required for a project.

        Args:
            project_type: Type of project (new_construction, renovation, addition)
            work_items: List of work items (framing, electrical, plumbing, etc.)

        Returns:
            List of required permits
        """
        required_permits = set()

        # Map work items to permit requirements
        permit_mapping = {
            "framing": ["building"],
            "foundation": ["building"],
            "electrical": ["electrical"],
            "plumbing": ["plumbing"],
            "hvac": ["mechanical"],
            "roofing": ["roofing"],
            "structural": ["building"],
            "demolition": ["demolition"],
        }

        for item in work_items:
            if item in permit_mapping:
                required_permits.update(permit_mapping[item])

        # New construction always needs building permit
        if project_type == "new_construction":
            required_permits.add("building")

        total_fees = sum(self._calculate_permit_fee(p) for p in required_permits)

        return {
            "project_type": project_type,
            "required_permits": list(required_permits),
            "estimated_total_fees": total_fees,
            "estimated_total_time": f"{len(required_permits) * 5} business days",
        }

    def _calculate_permit_fee(self, permit_type: str) -> float:
        """Calculate permit fee based on type."""
        fees = {
            "building": 500.00,
            "electrical": 150.00,
            "plumbing": 150.00,
            "mechanical": 150.00,
            "roofing": 100.00,
            "demolition": 200.00,
        }
        return fees.get(permit_type, 100.00)

    def get_inspection(self, inspection_id: str) -> Dict[str, Any]:
        """Get inspection details by ID."""
        if inspection_id in self.inspections:
            return self.inspections[inspection_id]
        else:
            return {"error": "Inspection not found"}


# Initialize the permitting service
service = PermittingService()

# Create MCP server
server = Server("permitting-service")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="apply_for_permit",
            description="Submit an application for a construction permit. Returns permit ID and "
            "estimated approval timeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "permit_type": {
                        "type": "string",
                        "description": "Type of permit (building, electrical, plumbing, "
                        "mechanical, demolition, roofing)",
                    },
                    "project_address": {
                        "type": "string",
                        "description": "Address of the construction project",
                    },
                    "project_description": {
                        "type": "string",
                        "description": "Description of the work to be performed",
                    },
                    "applicant": {
                        "type": "string",
                        "description": "Name of the applicant or contractor",
                    },
                },
                "required": ["permit_type", "project_address", "project_description", "applicant"],
            },
        ),
        Tool(
            name="check_permit_status",
            description="Check the current status of a permit application",
            inputSchema={
                "type": "object",
                "properties": {
                    "permit_id": {
                        "type": "string",
                        "description": "ID of the permit to check (e.g., 'PERMIT_1_20250119')",
                    }
                },
                "required": ["permit_id"],
            },
        ),
        Tool(
            name="schedule_inspection",
            description="Schedule a construction inspection for an approved permit",
            inputSchema={
                "type": "object",
                "properties": {
                    "permit_id": {
                        "type": "string",
                        "description": "ID of the associated permit",
                    },
                    "inspection_type": {
                        "type": "string",
                        "description": "Type of inspection (framing, electrical, plumbing, final)",
                    },
                    "requested_date": {
                        "type": "string",
                        "description": "Requested date in ISO format (optional, defaults to "
                        "tomorrow)",
                    },
                },
                "required": ["permit_id", "inspection_type"],
            },
        ),
        Tool(
            name="get_required_permits",
            description="Determine what permits are required for a construction project based on "
            "project type and work items",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_type": {
                        "type": "string",
                        "description": "Type of project (new_construction, renovation, addition)",
                    },
                    "work_items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of work items (framing, foundation, electrical, "
                        "plumbing, hvac, roofing, structural, demolition)",
                    },
                },
                "required": ["project_type", "work_items"],
            },
        ),
        Tool(
            name="get_inspection",
            description="Retrieve details of a scheduled or completed inspection",
            inputSchema={
                "type": "object",
                "properties": {
                    "inspection_id": {
                        "type": "string",
                        "description": "Inspection ID to retrieve (e.g., 'INSP_1')",
                    }
                },
                "required": ["inspection_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "apply_for_permit":
            validated_input = ApplyForPermitInput(**arguments)
            result = service.apply_for_permit(
                validated_input.permit_type,
                validated_input.project_address,
                validated_input.project_description,
                validated_input.applicant,
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "check_permit_status":
            validated_input = CheckPermitStatusInput(**arguments)
            result = service.check_permit_status(validated_input.permit_id)
            return [TextContent(type="text", text=str(result))]

        elif name == "schedule_inspection":
            validated_input = ScheduleInspectionInput(**arguments)
            result = service.schedule_inspection(
                validated_input.permit_id,
                validated_input.inspection_type,
                validated_input.requested_date,
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "get_required_permits":
            validated_input = GetRequiredPermitsInput(**arguments)
            result = service.get_required_permits(
                validated_input.project_type, validated_input.work_items
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "get_inspection":
            validated_input = GetInspectionInput(**arguments)
            result = service.get_inspection(validated_input.inspection_id)
            return [TextContent(type="text", text=str(result))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error in tool '{name}': {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Permitting Service MCP server starting...")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
