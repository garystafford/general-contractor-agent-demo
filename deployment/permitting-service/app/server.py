"""
Permitting Service MCP Server - HTTP Transport Version.

This MCP server provides tools for managing construction permits and inspections,
including permit applications, status checking, inspection scheduling, and
determining required permits for projects.

Refactored from stdio transport to streamable HTTP for ECS deployment.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Configuration from environment
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# Create FastMCP server with HTTP transport settings
mcp = FastMCP(
    name="permitting-service",
    instructions="Construction permitting service for managing permits, inspections, and determining permit requirements.",
    host=HOST,
    port=PORT,
)


# Add health check endpoint using FastMCP custom_route
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for ALB/ECS."""
    from starlette.responses import JSONResponse

    return JSONResponse(
        {
            "status": "healthy",
            "service": "permitting-service",
            "tools": [
                "apply_for_permit",
                "check_permit_status",
                "schedule_inspection",
                "get_required_permits",
                "get_inspection",
            ],
        }
    )


# Pydantic models for input validation
class ApplyForPermitInput(BaseModel):
    """Input for applying for a permit."""

    permit_type: str = Field(
        ...,
        description="Type of permit (building, electrical, plumbing, mechanical, demolition, roofing)",
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
        """Apply for a construction permit."""
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
        """Schedule a construction inspection."""
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
        """Determine what permits are required for a project."""
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


# Register tools with FastMCP
@mcp.tool(
    name="apply_for_permit",
    description="Submit an application for a construction permit. Returns permit ID and "
    "estimated approval timeline. Permit types: building, electrical, plumbing, mechanical, "
    "demolition, roofing.",
)
def apply_for_permit(
    permit_type: str,
    project_address: str,
    project_description: str,
    applicant: str,
) -> Dict[str, Any]:
    """Apply for a construction permit."""
    return service.apply_for_permit(permit_type, project_address, project_description, applicant)


@mcp.tool(
    name="check_permit_status",
    description="Check the current status of a permit application by permit ID (e.g., 'PERMIT_1_20250120').",
)
def check_permit_status(permit_id: str) -> Dict[str, Any]:
    """Check permit status."""
    return service.check_permit_status(permit_id)


@mcp.tool(
    name="schedule_inspection",
    description="Schedule a construction inspection for an approved permit. "
    "Inspection types: framing, electrical, plumbing, final.",
)
def schedule_inspection(
    permit_id: str,
    inspection_type: str,
    requested_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Schedule an inspection."""
    return service.schedule_inspection(permit_id, inspection_type, requested_date)


@mcp.tool(
    name="get_required_permits",
    description="Determine what permits are required for a construction project based on "
    "project type (new_construction, renovation, addition) and work items (framing, "
    "foundation, electrical, plumbing, hvac, roofing, structural, demolition).",
)
def get_required_permits(project_type: str, work_items: List[str]) -> Dict[str, Any]:
    """Get required permits for a project."""
    return service.get_required_permits(project_type, work_items)


@mcp.tool(
    name="get_inspection",
    description="Retrieve details of a scheduled or completed inspection by inspection ID (e.g., 'INSP_1').",
)
def get_inspection(inspection_id: str) -> Dict[str, Any]:
    """Get inspection details."""
    return service.get_inspection(inspection_id)


def get_mcp_server() -> FastMCP:
    """Return the MCP server instance."""
    return mcp
