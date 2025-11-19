"""
Permitting service (simplified MCP implementation).
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


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


# Global instance
permitting_service = PermittingService()
