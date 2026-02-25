"""
FastAPI routes for the General Contractor Agent Demo.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.general_contractor import GeneralContractorAgent
from backend.utils.activity_logger import get_activity_logger
from backend.utils.token_tracker import get_token_tracker

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


# Startup event to initialize MCP servers
@app.on_event("startup")
async def startup_event():
    """Initialize MCP servers on application startup."""
    logger.info("Starting up application...")
    try:
        logger.info("Initializing MCP clients...")
        await contractor.initialize_mcp_clients()
        logger.info("✓ MCP clients initialized successfully on startup")
    except Exception as e:
        logger.warning(f"⚠️  MCP clients failed to initialize on startup: {e}")
        logger.warning("MCP services will be initialized on first use")


# Shutdown event to clean up MCP connections
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MCP connections on application shutdown."""
    logger.info("Shutting down application...")
    try:
        await contractor.close_mcp_clients()
        logger.info("✓ MCP clients closed successfully")
    except Exception as e:
        logger.error(f"Error closing MCP clients: {e}")


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        self.active_connections -= disconnected


manager = ConnectionManager()


# Pydantic models
class ProjectRequest(BaseModel):
    description: str
    project_type: str
    parameters: Optional[Dict[str, Any]] = {}
    use_dynamic_planning: Optional[bool] = False


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
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/health/detailed")
async def detailed_health_check():
    """
    Comprehensive health check for all system components.

    Returns status for:
    - Backend API
    - MCP Materials Server
    - MCP Permitting Server
    - Database/Task Manager
    - Agents
    """
    logger.debug("Performing detailed health check")

    health_report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {},
    }

    try:
        # Check backend API
        health_report["components"]["backend_api"] = {
            "status": "up",
            "details": "API server is running",
            "version": "1.0.0",
        }

        # Check MCP servers
        try:
            mcp_health = await contractor.check_mcp_health()
            health_report["components"]["mcp_services"] = mcp_health

            # Update overall status if any MCP service is down
            for service_name in ["materials", "permitting"]:
                if mcp_health.get(service_name, {}).get("status") == "down":
                    health_report["overall_status"] = "degraded"
                    logger.debug(f"MCP {service_name} service is down")

        except Exception as e:
            health_report["components"]["mcp_services"] = {"status": "down", "error": str(e)}
            health_report["overall_status"] = "degraded"
            logger.debug(f"MCP services check failed: {e}")

        # Check task manager
        try:
            task_count = len(contractor.task_manager.tasks)
            health_report["components"]["task_manager"] = {
                "status": "up",
                "details": f"{task_count} tasks in memory",
            }
        except Exception as e:
            health_report["components"]["task_manager"] = {"status": "down", "error": str(e)}
            health_report["overall_status"] = "unhealthy"

        # Check agents
        try:
            agent_count = len(contractor.agents)
            health_report["components"]["agents"] = {
                "status": "up",
                "details": f"{agent_count} agents available",
                "agents": list(contractor.agents.keys()),
            }
        except Exception as e:
            health_report["components"]["agents"] = {"status": "down", "error": str(e)}
            health_report["overall_status"] = "unhealthy"

        logger.debug(f"Health check complete: {health_report['overall_status']}")

    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        health_report["overall_status"] = "unhealthy"
        health_report["error"] = str(e)

    return {"status": "success", "data": health_report}


# Project Management Endpoints
@app.post("/api/projects/start")
async def start_project(request: ProjectRequest):
    """
    Start a new construction project.

    Supports both hardcoded templates and dynamic LLM-based planning:
    - Hardcoded templates: kitchen_remodel, bathroom_remodel, new_construction, addition, shed_construction
    - Dynamic planning: Any other project type (dog_house, deck, treehouse, etc.)
    - Use use_dynamic_planning=true to force dynamic planning for any project type
    """
    try:
        result = await contractor.start_project(
            project_description=request.description,
            project_type=request.project_type,
            use_dynamic_planning=request.use_dynamic_planning,
            **request.parameters,
        )
        return {"status": "success", "data": result}
    except ValueError as e:
        # Handle validation errors with structured response
        error_message = str(e)
        if error_message.startswith("Missing required information:"):
            # Extract validation details from the contractor's validation result
            validation_result = contractor._validate_project_requirements(
                request.project_type, request.description, **request.parameters
            )
            if not validation_result["valid"]:
                logger.warning(
                    f"Validation error for {request.project_type}: {validation_result['missing_fields']}"
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": validation_result["message"],
                        "missing_fields": validation_result["missing_fields"],
                        "suggestions": validation_result["suggestions"],
                    },
                )
        logger.error(f"ValueError starting project: {e}")
        raise HTTPException(status_code=400, detail=str(e))
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
        await contractor.reset()
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


@app.post("/api/tasks/{task_id}/skip")
async def skip_task(task_id: str):
    """Skip a failed or stuck task and mark it as completed with a note."""
    try:
        task = contractor.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        # Mark as completed with a skipped note
        contractor.task_manager.mark_completed(
            task_id,
            {
                "status": "skipped",
                "message": "Task manually skipped due to failure or timeout",
                "original_status": task.status.value,
            },
        )

        logger.info(f"Task {task_id} manually skipped by user")
        return {
            "status": "success",
            "message": f"Task {task_id} skipped successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry a failed task."""
    try:
        task = contractor.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status.value != "failed":
            raise HTTPException(
                status_code=400,
                detail=f"Task is {task.status.value}, can only retry failed tasks",
            )

        # Reset task to ready state
        contractor.task_manager.mark_ready(task_id)

        # Execute the task again
        result = await contractor.execute_task(task)

        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Materials Supplier Endpoints
@app.get("/api/materials/catalog")
async def get_materials_catalog(category: Optional[str] = None):
    """Get materials catalog, optionally filtered by category."""
    try:
        catalog = await contractor.get_materials_catalog(category)
        return {"status": "success", "data": catalog}
    except Exception as e:
        logger.error(f"Error getting catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/materials/check-availability")
async def check_materials_availability(material_ids: List[str]):
    """Check availability of specific materials."""
    try:
        availability = await contractor.check_materials_availability(material_ids)
        return {"status": "success", "data": availability}
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/materials/order")
async def order_materials(request: MaterialOrderRequest):
    """Order materials from the supplier."""
    try:
        result = await contractor.order_materials(request.orders)
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
        # Note: get_order is not exposed via MCP yet - needs to be added
        order = await contractor.call_mcp_tool("materials", "get_order", {"order_id": order_id})
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
        result = await contractor.apply_for_permit(
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
        result = await contractor.check_permit_status(permit_id)
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
        result = await contractor.schedule_inspection(
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
        # Note: get_inspection is not exposed via helper method yet
        inspection = await contractor.call_mcp_tool(
            "permitting", "get_inspection", {"inspection_id": inspection_id}
        )
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
        result = await contractor.get_required_permits(project_type, work_items)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error getting required permits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoints
@app.websocket("/ws/project-updates")
async def websocket_project_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time project updates.
    Streams project status, task updates, and agent activity.
    """
    await manager.connect(websocket)
    try:
        # Send initial project status
        initial_status = contractor.get_project_status()
        await websocket.send_json({"type": "project_status", "data": initial_status})

        # Keep connection alive and send updates
        while True:
            try:
                # Check for messages from client (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

                # Handle client messages if needed
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data == "get_status":
                    status = contractor.get_project_status()
                    await websocket.send_json({"type": "project_status", "data": status})

            except asyncio.TimeoutError:
                # No message received, send periodic update
                status = contractor.get_project_status()
                await websocket.send_json({"type": "project_status", "data": status})
                await asyncio.sleep(2)  # Update every 2 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/task-updates")
async def websocket_task_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time task updates.
    Streams individual task status changes.
    """
    await manager.connect(websocket)
    try:
        # Send initial task list
        tasks = contractor.get_all_tasks()
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
        await websocket.send_json({"type": "tasks_list", "data": tasks_dict})

        # Keep connection alive and send updates
        previous_tasks_state = {}
        while True:
            try:
                # Check for messages from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data == "get_tasks":
                    tasks = contractor.get_all_tasks()
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
                    await websocket.send_json({"type": "tasks_list", "data": tasks_dict})

            except asyncio.TimeoutError:
                # Check for task changes
                tasks = contractor.get_all_tasks()
                current_state = {t.task_id: t.status.value for t in tasks}

                # Detect changes
                for task in tasks:
                    task_id = task.task_id
                    current_status = task.status.value

                    if (
                        task_id not in previous_tasks_state
                        or previous_tasks_state[task_id] != current_status
                    ):
                        # Task status changed
                        await websocket.send_json(
                            {
                                "type": "task_update",
                                "data": {
                                    "task_id": task.task_id,
                                    "agent": task.agent,
                                    "description": task.description,
                                    "status": current_status,
                                    "phase": task.phase,
                                    "dependencies": task.dependencies,
                                },
                            }
                        )

                previous_tasks_state = current_state
                await asyncio.sleep(1)  # Check every second

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Task WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Task WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/agent-activity")
async def websocket_agent_activity(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent activity.
    Streams which agents are currently working and which tools they're using.
    """
    await manager.connect(websocket)
    try:
        # Keep connection alive and send agent activity updates
        while True:
            try:
                # Check for messages from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # Get current task execution state
                tasks = contractor.get_all_tasks()
                active_agents = {}

                for task in tasks:
                    if task.status.value == "in_progress":
                        active_agents[task.agent] = {
                            "task_id": task.task_id,
                            "description": task.description,
                            "phase": task.phase,
                        }

                # Send agent activity update
                await websocket.send_json(
                    {
                        "type": "agent_activity",
                        "data": {
                            "active_agents": active_agents,
                            "total_agents": len(contractor.agents),
                            "busy_count": len(active_agents),
                        },
                    }
                )

                await asyncio.sleep(0.5)  # Update twice per second for smooth animation

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Agent activity WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Agent activity WebSocket error: {e}")
        manager.disconnect(websocket)


# Activity Monitor Endpoints
@app.get("/api/activity/stream")
async def stream_activity():
    """
    Server-Sent Events endpoint for streaming agent activity in real-time.

    Returns a stream of activity events including:
    - Agent reasoning/thinking
    - Tool calls and results
    - Task state changes
    - Planning events

    Usage: Connect via EventSource in JavaScript:
        const eventSource = new EventSource('/api/activity/stream');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(data);
        };
    """
    activity_logger = get_activity_logger()

    async def event_generator():
        """Generate SSE events from activity queue."""
        queue = activity_logger.subscribe()

        try:
            # Send recent events first (last 20)
            recent_events = activity_logger.get_recent_events(20)
            for event in recent_events:
                yield f"data: {json.dumps(event)}\n\n"

            # Stream new events
            while True:
                try:
                    # Wait for new events with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f": keepalive\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            activity_logger.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.get("/api/activity/recent")
async def get_recent_activity(count: int = 50):
    """
    Get recent activity events (non-streaming).

    Args:
        count: Number of recent events to return (default: 50, max: 500)

    Returns:
        List of recent activity events
    """
    activity_logger = get_activity_logger()
    count = min(count, 500)  # Cap at 500

    events = activity_logger.get_recent_events(count)
    return {
        "status": "success",
        "data": {
            "events": events,
            "total": len(events),
        },
    }


@app.post("/api/activity/clear")
async def clear_activity():
    """Clear all activity logs."""
    activity_logger = get_activity_logger()
    activity_logger.clear()
    return {"status": "success", "message": "Activity log cleared"}


# Token Usage Endpoints
@app.get("/api/token-usage")
async def get_token_usage():
    """
    Get token usage summary for the current project.

    Returns project totals, per-agent breakdown, and per-task breakdown
    of input/output/total tokens consumed by LLM calls.
    """
    token_tracker = get_token_tracker()
    return {"status": "success", "data": token_tracker.get_summary()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
