"""
General Contractor orchestration agent.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands.tools.mcp import MCPClient

from backend.agents import (
    create_architect_agent,
    create_carpenter_agent,
    create_electrician_agent,
    create_hvac_agent,
    create_mason_agent,
    create_painter_agent,
    create_plumber_agent,
    create_project_planner_agent,
    create_roofer_agent,
)
from backend.config import settings
from backend.orchestration.task_manager import Task, TaskManager

logger = logging.getLogger(__name__)


class GeneralContractorAgent:
    """
    Orchestration agent that coordinates all specialized trade agents.

    The General Contractor is responsible for:
    - Breaking down projects into tasks
    - Managing dependencies and sequencing
    - Delegating tasks to appropriate agents
    - Monitoring progress
    - Handling exceptions and errors
    """

    def __init__(self):
        # Initialize task manager
        self.task_manager = TaskManager()

        # Initialize all specialized agents using Strands Agents
        self.agents: Dict[str, Any] = {
            "Architect": create_architect_agent(),
            "Carpenter": create_carpenter_agent(),
            "Electrician": create_electrician_agent(),
            "Plumber": create_plumber_agent(),
            "Mason": create_mason_agent(),
            "Painter": create_painter_agent(),
            "HVAC": create_hvac_agent(),
            "Roofer": create_roofer_agent(),
        }

        # Planning agent (lazy-loaded on first use to save costs)
        self._planning_agent = None

        # Initialize MCP clients for external services
        self.mcp_clients: Dict[str, Optional[MCPClient]] = {
            "materials": None,
            "permitting": None,
        }
        self._mcp_initialized = False

        # Project state
        self.current_project: Optional[Dict[str, Any]] = None
        self.project_phase = "idle"  # idle, planning, in_progress, completed

        logger.info("General Contractor initialized with 8 specialized Strands agents")

    @property
    def planning_agent(self):
        """Lazy-load planning agent on first use."""
        if self._planning_agent is None:
            logger.info("Initializing Planning Agent for dynamic project planning")
            self._planning_agent = create_project_planner_agent()
        return self._planning_agent

    async def initialize_mcp_clients(self) -> None:
        """Initialize MCP client connections to external services."""
        if self._mcp_initialized:
            return

        try:
            # Get the project root directory
            project_root = Path.cwd()

            # Use the same Python executable that's running this process
            python_exe = sys.executable

            logger.info(f"Initializing MCP clients using Python: {python_exe}")
            logger.info(f"Project root: {project_root}")

            # Initialize Materials Supplier MCP client
            materials_path = project_root / settings.materials_mcp_path
            logger.info(f"Materials MCP server path: {materials_path}")

            materials_server_params = StdioServerParameters(
                command=python_exe,
                args=[str(materials_path)],
                env=None,
            )
            # Create a callable that returns the stdio transport
            materials_transport = lambda: stdio_client(materials_server_params)
            materials_client = MCPClient(materials_transport)
            logger.info("Starting Materials Supplier MCP client...")
            materials_client.start()  # Note: start() is NOT async
            self.mcp_clients["materials"] = materials_client
            logger.info("✓ Materials Supplier MCP client initialized")

            # Initialize Permitting Service MCP client
            permitting_path = project_root / settings.permitting_mcp_path
            logger.info(f"Permitting MCP server path: {permitting_path}")

            permitting_server_params = StdioServerParameters(
                command=python_exe,
                args=[str(permitting_path)],
                env=None,
            )
            # Create a callable that returns the stdio transport
            permitting_transport = lambda: stdio_client(permitting_server_params)
            permitting_client = MCPClient(permitting_transport)
            logger.info("Starting Permitting Service MCP client...")
            permitting_client.start()  # Note: start() is NOT async
            self.mcp_clients["permitting"] = permitting_client
            logger.info("✓ Permitting Service MCP client initialized")

            self._mcp_initialized = True
            logger.info("✓ All MCP clients initialized successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing MCP clients: {e}", exc_info=True)
            raise

    async def close_mcp_clients(self) -> None:
        """Close MCP client connections."""
        for name, client in self.mcp_clients.items():
            if client:
                try:
                    # MCPClient uses context manager protocol, just clear the reference
                    # The client will clean up when garbage collected
                    self.mcp_clients[name] = None
                    logger.info(f"{name} MCP client closed")
                except Exception as e:
                    logger.error(f"Error closing {name} MCP client: {e}")

        self._mcp_initialized = False

    async def call_mcp_tool(self, service: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on an MCP service.

        Args:
            service: Name of the MCP service ('materials' or 'permitting')
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool result
        """
        if not self._mcp_initialized:
            await self.initialize_mcp_clients()

        client = self.mcp_clients.get(service)
        if not client:
            raise ValueError(f"MCP service '{service}' not found")

        try:
            # Generate a unique tool use ID
            import uuid

            tool_use_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"

            # Call the tool with proper signature: (tool_use_id, name, arguments)
            mcp_result = await client.call_tool_async(tool_use_id, tool_name, arguments)

            # Extract the actual result from MCP response
            # MCPToolResult can be dict or object with: status, toolUseId, content (list of TextContent)
            if isinstance(mcp_result, dict):
                # Dict format
                if "content" in mcp_result and mcp_result["content"]:
                    text_content = mcp_result["content"][0]["text"]
                    result = eval(text_content)
                    return result
            elif hasattr(mcp_result, "content") and mcp_result.content:
                # Object format
                text_content = mcp_result.content[0].text
                result = eval(text_content)
                return result

            logger.error(f"Unexpected MCP result format: {mcp_result}")
            return mcp_result
        except Exception as e:
            logger.error(f"Error calling MCP tool {service}.{tool_name}: {e}")
            raise

    async def check_materials_availability(self, material_ids: List[str]) -> Dict[str, Any]:
        """Check availability of materials via MCP."""
        return await self.call_mcp_tool(
            "materials", "check_availability", {"material_ids": material_ids}
        )

    async def order_materials(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Order materials via MCP."""
        return await self.call_mcp_tool("materials", "order_materials", {"orders": orders})

    async def get_materials_catalog(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get materials catalog via MCP."""
        args = {"category": category} if category else {}
        return await self.call_mcp_tool("materials", "get_catalog", args)

    async def apply_for_permit(
        self, permit_type: str, project_address: str, project_description: str, applicant: str
    ) -> Dict[str, Any]:
        """Apply for a construction permit via MCP."""
        return await self.call_mcp_tool(
            "permitting",
            "apply_for_permit",
            {
                "permit_type": permit_type,
                "project_address": project_address,
                "project_description": project_description,
                "applicant": applicant,
            },
        )

    async def check_permit_status(self, permit_id: str) -> Dict[str, Any]:
        """Check permit status via MCP."""
        return await self.call_mcp_tool(
            "permitting", "check_permit_status", {"permit_id": permit_id}
        )

    async def schedule_inspection(
        self, permit_id: str, inspection_type: str, requested_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schedule an inspection via MCP."""
        args = {"permit_id": permit_id, "inspection_type": inspection_type}
        if requested_date:
            args["requested_date"] = requested_date
        return await self.call_mcp_tool("permitting", "schedule_inspection", args)

    async def get_required_permits(
        self, project_type: str, work_items: List[str]
    ) -> Dict[str, Any]:
        """Get required permits for a project via MCP."""
        return await self.call_mcp_tool(
            "permitting",
            "get_required_permits",
            {"project_type": project_type, "work_items": work_items},
        )

    async def _create_dynamic_project_plan(
        self, project_type: str, description: str, **kwargs
    ) -> List[Task]:
        """
        Use Planning Agent to create a dynamic project plan.

        Args:
            project_type: Type of project (e.g., "dog_house", "deck", "treehouse")
            description: Detailed project description
            **kwargs: Additional parameters

        Returns:
            List of Task objects
        """
        logger.info(f"Using dynamic planning for project type: {project_type}")

        # Prepare prompt for planning agent
        planning_prompt = f"""Create a complete construction project plan for the following:

Project Type: {project_type}
Description: {description}
Parameters: {kwargs if kwargs else 'None specified'}

Use ALL your tools in sequence to create a comprehensive, executable plan:
1. analyze_project_scope - Analyze the requirements
2. generate_task_breakdown - Create detailed task list
3. validate_task_dependencies - Ensure dependencies are valid
4. assign_construction_phases - Assign phases appropriately
5. finalize_project_plan - Output the final structured plan

Remember to output the final plan in exact JSON format with the 'tasks' and 'summary' fields."""

        try:
            # Call planning agent with timeout
            result = await asyncio.wait_for(
                self.planning_agent.invoke_async(planning_prompt),
                timeout=120,  # 2 minute timeout for planning
            )

            logger.info(f"Planning agent result: {result}")

            # Parse the result to extract task plan
            task_plan = self._parse_planning_result(result)

            # Create tasks from the plan
            tasks = self.task_manager.create_tasks_from_plan(task_plan)

            logger.info(f"Created {len(tasks)} tasks from dynamic planning")
            return tasks

        except asyncio.TimeoutError:
            logger.error("Planning agent timed out")
            raise Exception("Dynamic planning timed out after 120 seconds")
        except Exception as e:
            logger.error(f"Error in dynamic planning: {e}")
            raise

    def _parse_planning_result(self, planning_result: Any) -> List[Dict[str, Any]]:
        """
        Parse the planning agent result into a list of task dictionaries.

        Args:
            planning_result: AgentResult or string result from planning agent

        Returns:
            List of task dictionaries
        """
        import json
        import re

        # Extract text from AgentResult if needed
        if hasattr(planning_result, "text"):
            # Strands AgentResult object
            result_text = planning_result.text
        elif isinstance(planning_result, str):
            # Already a string
            result_text = planning_result
        else:
            # Try to convert to string
            result_text = str(planning_result)

        logger.info(f"Parsing planning result (first 500 chars): {result_text[:500]}")

        # Try to extract JSON from the result
        # Look for JSON blocks in the result
        json_pattern = r'\{[\s\S]*"tasks"[\s\S]*\}'
        matches = re.findall(json_pattern, result_text)

        if matches:
            # Try to parse the first (likely best) match
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if "tasks" in parsed:
                        return parsed["tasks"]
                except json.JSONDecodeError:
                    continue

        # Fallback: look for task list pattern
        logger.warning("Could not find structured JSON in planning result, attempting manual parse")

        # If we can't parse, return empty list and log error
        logger.error(f"Failed to parse planning result: {result_text[:500]}")
        raise ValueError("Could not parse planning agent output into task list")

    async def start_project(
        self,
        project_description: str,
        project_type: str,
        use_dynamic_planning: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Start a new construction project.

        Args:
            project_description: Description of the project
            project_type: Type of project (kitchen_remodel, new_construction, etc.)
            use_dynamic_planning: Force use of dynamic planning even for supported types
            **kwargs: Additional project parameters

        Returns:
            Dictionary with project details and initial status
        """
        logger.info(f"Starting new project: {project_type}")

        # Create project record
        self.current_project = {
            "description": project_description,
            "type": project_type,
            "parameters": kwargs,
            "start_time": None,
            "status": "planning",
            "planning_method": "unknown",
        }

        # Determine if we should use dynamic planning
        is_supported_type = project_type in self.task_manager.SUPPORTED_PROJECT_TYPES
        should_use_dynamic = use_dynamic_planning or not is_supported_type

        if should_use_dynamic:
            # Use dynamic planning with LLM
            logger.info(f"Using dynamic planning for '{project_type}'")
            self.current_project["planning_method"] = "dynamic"
            tasks = await self._create_dynamic_project_plan(
                project_type, project_description, **kwargs
            )
        else:
            # Use hardcoded template
            logger.info(f"Using hardcoded template for '{project_type}'")
            self.current_project["planning_method"] = "template"
            tasks = self.task_manager.create_project_tasks(project_type, **kwargs)

        self.project_phase = "planning"

        return {
            "status": "success",
            "message": f"Project initialized: {project_type} (using {self.current_project['planning_method']} planning)",
            "project": self.current_project,
            "total_tasks": len(tasks),
            "task_breakdown": self._get_task_breakdown(tasks),
        }

    def _get_task_breakdown(self, tasks: List[Task]) -> Dict[str, Any]:
        """Get a breakdown of tasks by phase and agent."""
        breakdown = {
            "by_phase": {},
            "by_agent": {},
        }

        for task in tasks:
            # By phase
            if task.phase not in breakdown["by_phase"]:
                breakdown["by_phase"][task.phase] = []
            breakdown["by_phase"][task.phase].append(
                {"id": task.task_id, "description": task.description}
            )

            # By agent
            if task.agent not in breakdown["by_agent"]:
                breakdown["by_agent"][task.agent] = 0
            breakdown["by_agent"][task.agent] += 1

        return breakdown

    async def execute_next_phase(self) -> Dict[str, Any]:
        """
        Execute the next phase of tasks that are ready.

        Returns:
            Dictionary with execution results
        """
        if self.project_phase == "idle":
            return {"status": "error", "message": "No active project"}

        # Get tasks ready for the next phase
        ready_tasks = self.task_manager.get_next_phase_tasks()

        if not ready_tasks:
            # Check if project is complete
            project_status = self.task_manager.get_project_status()
            if project_status["pending"] == 0 and project_status["in_progress"] == 0:
                self.project_phase = "completed"
                return {
                    "status": "success",
                    "message": "Project completed",
                    "project_status": project_status,
                }
            else:
                return {
                    "status": "waiting",
                    "message": "Waiting for dependencies",
                    "project_status": project_status,
                }

        logger.info(f"Executing {len(ready_tasks)} tasks in next phase")

        # Execute tasks (can be parallelized for independent tasks)
        results = []
        for task in ready_tasks:
            result = await self.execute_task(task)
            results.append(result)

        return {
            "status": "success",
            "message": f"Executed {len(results)} tasks",
            "results": results,
            "project_status": self.task_manager.get_project_status(),
        }

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task by delegating to the appropriate agent.

        Args:
            task: Task object to execute

        Returns:
            Dictionary with execution results
        """
        agent_name = task.agent

        # Check if agent exists
        if agent_name not in self.agents:
            error_msg = f"Agent {agent_name} not found"
            logger.error(error_msg)
            self.task_manager.mark_failed(task.task_id, error_msg)
            return {
                "status": "error",
                "task_id": task.task_id,
                "error": error_msg,
            }

        # Mark task as in progress
        self.task_manager.mark_in_progress(task.task_id)

        # Get the agent
        agent = self.agents[agent_name]

        # Prepare task prompt for Strands agent
        max_consecutive = getattr(settings, "max_consecutive_tool_calls", 3)
        task_prompt = f"""Task ID: {task.task_id}
Description: {task.description}

Requirements: {task.requirements}
Materials needed: {task.materials}

IMPORTANT CONSTRAINTS:
- Do NOT call the same tool more than {max_consecutive} times in a row
- If a tool fails or returns an error, try a different approach instead of repeating
- Each tool should be called AT MOST ONCE unless absolutely necessary
- Provide a concise summary when complete

Complete this task using your specialized tools efficiently."""

        try:
            # Execute task with Strands agent using invoke_async
            # Add timeout protection to prevent infinite loops
            logger.info(f"Delegating task {task.task_id} to {agent_name}")

            # Set a timeout per task - catch infinite loops faster
            timeout_seconds = getattr(settings, "task_timeout_seconds", 300)

            try:
                result = await asyncio.wait_for(
                    agent.invoke_async(task_prompt), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                error_msg = (
                    f"Task {task.task_id} timed out after {timeout_seconds} seconds. "
                    f"Agent '{agent_name}' likely stuck in a loop. "
                    f"Check if the agent is calling the same tool repeatedly."
                )
                logger.error(error_msg)
                logger.error(f"Task description: {task.description}")
                self.task_manager.mark_failed(task.task_id, error_msg)
                return {
                    "status": "failed",
                    "task_id": task.task_id,
                    "error": error_msg,
                    "agent": agent_name,
                }

            # Format result for task manager
            task_result = {
                "status": "completed",
                "task_id": task.task_id,
                "agent": agent_name,
                "result": result,
            }

            # Mark task as completed
            self.task_manager.mark_completed(task.task_id, task_result)

            return task_result

        except Exception as e:
            error_msg = f"Error executing task {task.task_id}: {str(e)}"
            logger.error(error_msg)
            self.task_manager.mark_failed(task.task_id, error_msg)
            return {
                "status": "error",
                "task_id": task.task_id,
                "error": error_msg,
            }

    async def execute_entire_project(self) -> Dict[str, Any]:
        """
        Execute the entire project from start to finish.

        Returns:
            Dictionary with final project results
        """
        if self.project_phase == "idle":
            return {"status": "error", "message": "No active project"}

        self.project_phase = "in_progress"
        logger.info("Starting full project execution")

        all_results = []
        max_iterations = 50  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            result = await self.execute_next_phase()

            all_results.append(result)

            if result["status"] == "success" and self.project_phase == "completed":
                logger.info("Project execution completed")
                break

            if result["status"] == "error":
                logger.error(f"Project execution failed: {result.get('message')}")
                break

            if result["status"] == "waiting":
                # Tasks are waiting for dependencies to complete
                # Check if there are any in-progress tasks that will eventually complete
                project_status = result.get("project_status", {})
                in_progress = project_status.get("in_progress", 0)
                pending = project_status.get("pending", 0)

                if in_progress == 0 and pending > 0:
                    # No tasks running but some are pending - this is a dependency deadlock
                    logger.error(f"Dependency deadlock detected: {pending} pending tasks but none can execute")
                    break
                elif in_progress == 0 and pending == 0:
                    # Nothing running and nothing pending - we're done
                    logger.info("Project complete - no tasks remaining")
                    break
                else:
                    # Tasks are in progress, just wait a bit and try again
                    logger.info(f"Waiting for {in_progress} tasks to complete before next phase")
                    await asyncio.sleep(1)
                    continue

            # Small delay between phases
            await asyncio.sleep(0.1)

        final_status = self.task_manager.get_project_status()

        return {
            "status": "completed" if self.project_phase == "completed" else "partial",
            "project": self.current_project,
            "final_status": final_status,
            "total_iterations": iteration,
            "execution_summary": all_results,
        }

    def get_project_status(self) -> Dict[str, Any]:
        """Get current project status."""
        if not self.current_project:
            return {"status": "no_active_project"}

        return {
            "project": self.current_project,
            "phase": self.project_phase,
            "task_status": self.task_manager.get_project_status(),
            "agents": list(self.agents.keys()),
        }

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of a specific agent."""
        if agent_name not in self.agents:
            return {"error": f"Agent {agent_name} not found"}

        agent = self.agents[agent_name]
        return {
            "name": agent.name if agent.name else agent_name,
            "status": "available",
            "tools": agent.tool_names,
        }

    def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            name: {
                "name": agent.name if agent.name else name,
                "status": "available",
                "tools": agent.tool_names,
            }
            for name, agent in self.agents.items()
        }

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID."""
        return self.task_manager.get_task(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return self.task_manager.get_all_tasks()

    async def reset(self) -> None:
        """Reset the contractor for a new project."""
        # Close MCP clients
        await self.close_mcp_clients()

        self.task_manager.clear()
        self.current_project = None
        self.project_phase = "idle"
        logger.info("General Contractor reset")
