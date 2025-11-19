"""
FastAPI routes for the General Contractor Agent Demo.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.agents.general_contractor import GeneralContractorAgent
from backend.mcp_servers.materials_supplier import materials_supplier
from backend.mcp_servers.permitting import permitting_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="General Contractor Orchestration API",
    description="Multi-agent system for construction project management",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize General Contractor
contractor = GeneralContractorAgent()


# Pydantic models
class ProjectRequest(BaseModel):
    description: str
    project_type: str
    parameters: Optional[Dict[str, Any]] = {}


class MaterialOrderRequest(BaseModel):
    orders: List[Dict[str, Any]]


class PermitApplicationRequest(BaseModel):
    permit_type: str
    project_address: str
    project_description: str
    applicant: str


class InspectionRequest(BaseModel):
    permit_id: str
    inspection_type: str
    requested_date: Optional[str] = None


# Health check
@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": "General Contractor Orchestration API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Project Management Endpoints
@app.post("/api/projects/start")
async def start_project(request: ProjectRequest):
    """Start a new construction project."""
    try:
        result = await contractor.start_project(
            project_description=request.description,
            project_type=request.project_type,
            **request.parameters,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error starting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/execute-next-phase")
async def execute_next_phase():
    """Execute the next phase of tasks."""
    try:
        result = await contractor.execute_next_phase()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error executing next phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/execute-all")
async def execute_entire_project():
    """Execute the entire project from start to finish."""
    try:
        result = await contractor.execute_entire_project()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error executing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/status")
async def get_project_status():
    """Get current project status."""
    try:
        status = contractor.get_project_status()
        return {"status": "success", "data": status}
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/reset")
async def reset_project():
    """Reset the contractor for a new project."""
    try:
        contractor.reset()
        return {"status": "success", "message": "Project reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Management Endpoints
@app.get("/api/agents")
async def get_all_agents():
    """Get list of all available agents."""
    try:
        agents = list(contractor.agents.keys())
        return {
            "status": "success",
            "data": {"agents": agents, "total": len(agents)},
        }
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
async def get_all_agents_status():
    """Get status of all agents."""
    try:
        status = contractor.get_all_agents_status()
        return {"status": "success", "data": status}
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_name}")
async def get_agent_status(agent_name: str):
    """Get status of a specific agent."""
    try:
        status = contractor.get_agent_status(agent_name)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return {"status": "success", "data": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task Management Endpoints
@app.get("/api/tasks")
async def get_all_tasks():
    """Get all tasks in the current project."""
    try:
        tasks = contractor.get_all_tasks()
        # Convert Task objects to dictionaries
        tasks_dict = [
            {
                "task_id": t.task_id,
                "agent": t.agent,
                "description": t.description,
                "status": t.status.value,
                "phase": t.phase,
                "dependencies": t.dependencies,
            }
            for t in tasks
        ]
        return {"status": "success", "data": {"tasks": tasks_dict, "total": len(tasks)}}
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get details of a specific task."""
    try:
        task = contractor.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        task_dict = {
            "task_id": task.task_id,
            "agent": task.agent,
            "description": task.description,
            "status": task.status.value,
            "phase": task.phase,
            "dependencies": task.dependencies,
            "result": task.result,
        }
        return {"status": "success", "data": task_dict}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Materials Supplier Endpoints
@app.get("/api/materials/catalog")
async def get_materials_catalog(category: Optional[str] = None):
    """Get materials catalog, optionally filtered by category."""
    try:
        catalog = materials_supplier.get_catalog(category)
        return {"status": "success", "data": catalog}
    except Exception as e:
        logger.error(f"Error getting catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/materials/check-availability")
async def check_materials_availability(material_ids: List[str]):
    """Check availability of specific materials."""
    try:
        availability = materials_supplier.check_availability(material_ids)
        return {"status": "success", "data": availability}
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/materials/order")
async def order_materials(request: MaterialOrderRequest):
    """Order materials from the supplier."""
    try:
        result = materials_supplier.order_materials(request.orders)
        if result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result.get("error"))
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ordering materials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/materials/orders/{order_id}")
async def get_order(order_id: str):
    """Get details of a specific order."""
    try:
        order = materials_supplier.get_order(order_id)
        if "error" in order:
            raise HTTPException(status_code=404, detail=order["error"])
        return {"status": "success", "data": order}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Permitting Endpoints
@app.post("/api/permits/apply")
async def apply_for_permit(request: PermitApplicationRequest):
    """Apply for a construction permit."""
    try:
        result = permitting_service.apply_for_permit(
            permit_type=request.permit_type,
            project_address=request.project_address,
            project_description=request.project_description,
            applicant=request.applicant,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error applying for permit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/permits/{permit_id}")
async def get_permit_status(permit_id: str):
    """Check status of a permit."""
    try:
        result = permitting_service.check_permit_status(permit_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/permits/inspections")
async def schedule_inspection(request: InspectionRequest):
    """Schedule a construction inspection."""
    try:
        result = permitting_service.schedule_inspection(
            permit_id=request.permit_id,
            inspection_type=request.inspection_type,
            requested_date=request.requested_date,
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/permits/inspections/{inspection_id}")
async def get_inspection(inspection_id: str):
    """Get details of a specific inspection."""
    try:
        inspection = permitting_service.get_inspection(inspection_id)
        if "error" in inspection:
            raise HTTPException(status_code=404, detail=inspection["error"])
        return {"status": "success", "data": inspection}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/permits/required")
async def get_required_permits(project_type: str, work_items: List[str]):
    """Determine what permits are required for a project."""
    try:
        result = permitting_service.get_required_permits(project_type, work_items)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error getting required permits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
