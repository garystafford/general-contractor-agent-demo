"""
General Contractor orchestration agent.
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands.tools.mcp import MCPClient

# Try to import streamable HTTP client for Docker/AWS deployments
# Falls back to SSE client if not available
try:
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:
    try:
        from mcp.client.sse import sse_client as streamablehttp_client
        import logging

        logging.getLogger(__name__).warning(
            "streamablehttp_client not available, using sse_client as fallback"
        )
    except ImportError:
        streamablehttp_client = None

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
from backend.orchestration.task_manager import Task, TaskManager, TaskStatus
from backend.utils.activity_logger import get_activity_logger

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
        self.last_error: Optional[Dict[str, Any]] = None  # Stores detailed error information

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
            mcp_mode = settings.mcp_mode.lower()
            logger.info(f"Initializing MCP clients in {mcp_mode} mode")

            if mcp_mode == "http":
                # HTTP mode: Connect to remote MCP servers via HTTP/SSE
                await self._initialize_http_mcp_clients()
            else:
                # Stdio mode: Launch MCP servers as local subprocesses
                await self._initialize_stdio_mcp_clients()

            self._mcp_initialized = True
            logger.info("✓ All MCP clients initialized successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing MCP clients: {e}", exc_info=True)
            raise

    async def _initialize_stdio_mcp_clients(self) -> None:
        """Initialize MCP clients in stdio mode (local subprocesses)."""
        project_root = Path.cwd()
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
        logger.info("✓ Materials Supplier MCP client initialized (stdio)")

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
        logger.info("✓ Permitting Service MCP client initialized (stdio)")

    async def _initialize_http_mcp_clients(self) -> None:
        """Initialize MCP clients in HTTP mode (remote servers via HTTP/SSE)."""
        # Check that HTTP client is available
        if streamablehttp_client is None:
            raise ValueError(
                "HTTP MCP client not available. Install mcp with HTTP support or use mcp_mode=stdio"
            )

        # Validate HTTP URLs are configured
        if not settings.materials_mcp_url:
            raise ValueError("materials_mcp_url must be set when mcp_mode=http")
        if not settings.permitting_mcp_url:
            raise ValueError("permitting_mcp_url must be set when mcp_mode=http")

        logger.info(f"Materials MCP server URL: {settings.materials_mcp_url}")
        logger.info(f"Permitting MCP server URL: {settings.permitting_mcp_url}")

        # Initialize Materials Supplier MCP client via HTTP (streamable-http transport)
        materials_url = settings.materials_mcp_url
        materials_transport = lambda: streamablehttp_client(materials_url)
        materials_client = MCPClient(materials_transport)
        logger.info("Starting Materials Supplier MCP client (HTTP)...")
        materials_client.start()
        self.mcp_clients["materials"] = materials_client
        logger.info(f"✓ Materials Supplier MCP client initialized (HTTP: {materials_url})")

        # Initialize Permitting Service MCP client via HTTP (streamable-http transport)
        permitting_url = settings.permitting_mcp_url
        permitting_transport = lambda: streamablehttp_client(permitting_url)
        permitting_client = MCPClient(permitting_transport)
        logger.info("Starting Permitting Service MCP client (HTTP)...")
        permitting_client.start()
        self.mcp_clients["permitting"] = permitting_client
        logger.info(f"✓ Permitting Service MCP client initialized (HTTP: {permitting_url})")

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

    async def check_mcp_health(self) -> Dict[str, Any]:
        """
        Check health status of all MCP clients.

        Returns:
            Dictionary with health status for each MCP service
        """
        health_status = {
            "materials": {"status": "unknown", "details": None},
            "permitting": {"status": "unknown", "details": None},
            "initialized": self._mcp_initialized,
        }

        # If not initialized, try to initialize
        if not self._mcp_initialized:
            try:
                await self.initialize_mcp_clients()
            except Exception as e:
                health_status["error"] = f"Failed to initialize MCP clients: {str(e)}"
                health_status["materials"]["status"] = "down"
                health_status["materials"]["details"] = "Not initialized"
                health_status["permitting"]["status"] = "down"
                health_status["permitting"]["details"] = "Not initialized"
                return health_status

        # Check each MCP client
        for service_name in ["materials", "permitting"]:
            client = self.mcp_clients.get(service_name)

            if not client:
                health_status[service_name]["status"] = "down"
                health_status[service_name]["details"] = "Client not initialized"
                continue

            try:
                # Simple health check - verify client exists and is initialized
                # MCPClient doesn't expose list_tools, so we just verify it's ready
                if client and hasattr(client, "call_tool_async"):
                    health_status[service_name]["status"] = "up"
                    health_status[service_name]["details"] = "Client initialized and ready"
                    # List known tools for each service
                    if service_name == "materials":
                        health_status[service_name]["tools"] = [
                            "get_catalog",
                            "check_availability",
                            "order_materials",
                            "get_order_status",
                        ]
                    elif service_name == "permitting":
                        health_status[service_name]["tools"] = [
                            "apply_for_permit",
                            "check_permit_status",
                            "schedule_inspection",
                            "get_required_permits",
                        ]
                else:
                    health_status[service_name]["status"] = "unknown"
                    health_status[service_name]["details"] = "Client state unclear"
            except Exception as e:
                health_status[service_name]["status"] = "down"
                health_status[service_name]["details"] = f"Error: {str(e)}"
                logger.warning(f"MCP {service_name} health check failed: {e}")

        return health_status

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

        # Log MCP call to activity logger
        activity_logger = get_activity_logger()
        await activity_logger.log_mcp_call(service, tool_name, arguments)

        try:
            # Generate a unique tool use ID
            import uuid

            tool_use_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"

            # Call the tool with proper signature: (tool_use_id, name, arguments)
            mcp_result = await client.call_tool_async(tool_use_id, tool_name, arguments)

            # Extract the actual result from MCP response
            # MCPToolResult can be dict or object with: status, toolUseId, content (list of TextContent)
            result = None
            if isinstance(mcp_result, dict):
                # Dict format
                if "content" in mcp_result and mcp_result["content"]:
                    text_content = mcp_result["content"][0]["text"]
                    result = eval(text_content)
            elif hasattr(mcp_result, "content") and mcp_result.content:
                # Object format
                text_content = mcp_result.content[0].text
                result = eval(text_content)

            if result is not None:
                # Log MCP result to activity logger
                await activity_logger.log_mcp_result(service, tool_name, result)
                return result

            logger.error(f"Unexpected MCP result format: {mcp_result}")
            await activity_logger.log_mcp_result(service, tool_name, mcp_result)
            return mcp_result
        except Exception as e:
            logger.error(f"Error calling MCP tool {service}.{tool_name}: {e}")
            await activity_logger.log_error(f"MCP {service}.{tool_name} failed: {str(e)}")
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
        activity_logger = get_activity_logger()

        # Clear any stored plan from previous runs
        from backend.agents.project_planner import clear_last_finalized_plan

        clear_last_finalized_plan()

        # Log planning start
        await activity_logger.log_planning_start(project_type)

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
            # Call planning agent with timeout and streaming for activity logging
            await activity_logger.log_info("Planning agent starting...", "Planner")

            result = await asyncio.wait_for(
                self._execute_planning_with_streaming(planning_prompt),
                timeout=120,  # 2 minute timeout for planning
            )

            logger.info(f"Planning agent result: {result}")

            # Parse the result to extract task plan
            task_plan = self._parse_planning_result(result)

            # Create tasks from the plan
            tasks = self.task_manager.create_tasks_from_plan(task_plan)

            # Log planning complete
            await activity_logger.log_planning_complete(len(tasks))

            logger.info(f"Created {len(tasks)} tasks from dynamic planning")
            return tasks

        except asyncio.TimeoutError:
            logger.error("Planning agent timed out")
            await activity_logger.log_error("Planning timed out after 120 seconds", "Planner")
            raise Exception("Dynamic planning timed out after 120 seconds")
        except Exception as e:
            logger.error(f"Error in dynamic planning: {e}")
            await activity_logger.log_error(f"Planning failed: {str(e)}", "Planner")
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

        # Log what we received (debug level)
        logger.debug(f"Planning result type: {type(planning_result).__name__}")

        # First, check if finalize_project_plan stored the tasks globally
        from backend.agents.project_planner import (
            get_last_finalized_plan,
            clear_last_finalized_plan,
        )

        stored_plan = get_last_finalized_plan()
        if stored_plan and stored_plan.get("tasks"):
            tasks = stored_plan["tasks"]
            logger.info(f"Retrieved {len(tasks)} tasks from stored finalize_project_plan result")
            clear_last_finalized_plan()  # Clear for next run
            return tasks

        # First, try to extract tasks from tool results (finalize_project_plan)
        if hasattr(planning_result, "messages"):
            logger.info(f"Checking {len(planning_result.messages)} messages for tool results")
            for i, msg in enumerate(planning_result.messages):
                # Log message structure for debugging
                msg_type = type(msg).__name__
                logger.debug(f"Message {i}: type={msg_type}, role={getattr(msg, 'role', 'N/A')}")

                # Check for tool results in content
                if hasattr(msg, "content"):
                    content = msg.content
                    if isinstance(content, list):
                        for j, content_block in enumerate(content):
                            block_type = type(content_block).__name__
                            logger.debug(f"  Content block {j}: type={block_type}")

                            # Try to get tool result content
                            try:
                                tool_content = None

                                # Check various ways tool results might be structured
                                if hasattr(content_block, "content"):
                                    tool_content = content_block.content
                                elif hasattr(content_block, "result"):
                                    tool_content = content_block.result
                                elif isinstance(content_block, dict):
                                    tool_content = content_block.get(
                                        "content"
                                    ) or content_block.get("result")

                                if tool_content is None:
                                    continue

                                # Parse the content
                                if isinstance(tool_content, str):
                                    parsed = json.loads(tool_content)
                                elif isinstance(tool_content, dict):
                                    parsed = tool_content
                                else:
                                    continue

                                # Check if this has tasks
                                if "tasks" in parsed and isinstance(parsed["tasks"], list):
                                    if len(parsed["tasks"]) > 0:
                                        logger.info(
                                            f"Found {len(parsed['tasks'])} tasks from tool result"
                                        )
                                        return parsed["tasks"]
                            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                                logger.debug(f"  Could not parse content block: {e}")
                                continue
                    elif isinstance(content, str):
                        # Content might be a JSON string directly
                        try:
                            parsed = json.loads(content)
                            if "tasks" in parsed and isinstance(parsed["tasks"], list):
                                if len(parsed["tasks"]) > 0:
                                    logger.info(
                                        f"Found {len(parsed['tasks'])} tasks from message content"
                                    )
                                    return parsed["tasks"]
                        except (json.JSONDecodeError, TypeError):
                            pass

        # Extract text from AgentResult if needed
        if hasattr(planning_result, "text"):
            result_text = planning_result.text
        elif isinstance(planning_result, str):
            result_text = planning_result
        else:
            result_text = str(planning_result)

        logger.info(f"Parsing planning result (first 500 chars): {result_text[:500]}")

        # Try to extract JSON from the text result
        json_pattern = r'\{[\s\S]*"tasks"[\s\S]*\}'
        matches = re.findall(json_pattern, result_text)

        if matches:
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if "tasks" in parsed and isinstance(parsed["tasks"], list):
                        if len(parsed["tasks"]) > 0:
                            return parsed["tasks"]
                except json.JSONDecodeError:
                    continue

        logger.warning("Could not find structured JSON in planning result, attempting manual parse")
        logger.error(f"Failed to parse planning result: {result_text[:500]}")
        raise ValueError("Could not parse planning agent output into task list")

    def _validate_project_requirements(
        self, project_type: str, description: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Validate that required information is present for the project type.

        Returns:
            Dictionary with validation result:
            - valid: bool
            - missing_fields: List[str] (if not valid)
            - suggestions: List[str] (if not valid)
        """
        missing_fields = []
        suggestions = []
        description_lower = description.lower()

        # Validation rules by project type
        if project_type == "kitchen_remodel":
            # Check for dimensions
            if (
                not re.search(r"\d+\s*[xX×]\s*\d+", description)
                and "feet" not in description_lower
                and "square" not in description_lower
            ):
                missing_fields.append('Kitchen dimensions (e.g., "12 feet by 15 feet" or "12x15")')
                suggestions.append("Add the length and width of your kitchen space")

            # Check for style
            styles = [
                "modern",
                "traditional",
                "transitional",
                "farmhouse",
                "contemporary",
                "rustic",
            ]
            if not any(style in description_lower for style in styles):
                missing_fields.append(
                    "Kitchen style preference (modern, traditional, transitional, or farmhouse)"
                )
                suggestions.append("Specify your preferred kitchen style")

        elif project_type == "bathroom_remodel":
            # Check for dimensions
            if (
                not re.search(r"\d+\s*[xX×]\s*\d+", description)
                and "feet" not in description_lower
                and "square" not in description_lower
            ):
                missing_fields.append('Bathroom dimensions (e.g., "8x10 feet")')
                suggestions.append("Add the dimensions of your bathroom")

            # Check for fixtures
            fixtures = ["toilet", "sink", "shower", "tub", "bathtub", "vanity"]
            if not any(fixture in description_lower for fixture in fixtures):
                missing_fields.append("Fixture requirements (toilet, sink, shower, tub, etc.)")
                suggestions.append("List which fixtures you want to install or replace")

        elif project_type == "addition":
            # Check for size
            if (
                "square" not in description_lower
                and "sq" not in description_lower
                and not re.search(r"\d+\s*[xX×]\s*\d+", description)
            ):
                missing_fields.append("Size of addition (square footage or dimensions)")
                suggestions.append("Specify how large the addition should be")

            # Check for room type
            room_types = ["bedroom", "room", "office", "living", "family", "kitchen", "bathroom"]
            if not any(room_type in description_lower for room_type in room_types):
                missing_fields.append(
                    "Type of room being added (bedroom, office, family room, etc.)"
                )
                suggestions.append("Describe what type of space you're adding")

        elif project_type == "shed_construction":
            # Check for dimensions
            if not re.search(r"\d+\s*[xX×]\s*\d+", description):
                missing_fields.append('Shed dimensions (e.g., "10x12 feet")')
                suggestions.append("Specify the length and width of the shed")

        elif project_type == "new_construction":
            # Check for square footage
            if (
                "square" not in description_lower
                and "sq ft" not in description_lower
                and "sqft" not in description_lower
            ):
                missing_fields.append("Total square footage of the building")
                suggestions.append("Provide the total size of the construction project")

            # Check for number of floors
            if (
                "story" not in description_lower
                and "stories" not in description_lower
                and "floor" not in description_lower
                and "level" not in description_lower
            ):
                missing_fields.append("Number of floors/stories")
                suggestions.append("Specify how many floors the building will have")

        # Return validation result
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "suggestions": suggestions,
                "message": f'The {project_type.replace("_", " ")} description needs additional details to proceed.',
            }

        return {"valid": True}

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

        Raises:
            ValueError: If required project information is missing
        """
        logger.info(f"Starting new project: {project_type}")

        # Validate project requirements (skip for custom projects or dynamic planning)
        if not use_dynamic_planning and project_type != "custom_project":
            validation_result = self._validate_project_requirements(
                project_type, project_description, **kwargs
            )
            if not validation_result["valid"]:
                logger.warning(
                    f"Project validation failed for {project_type}: {validation_result['missing_fields']}"
                )
                raise ValueError(
                    f"Missing required information: {', '.join(validation_result['missing_fields'])}"
                )

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

        Uses streaming to capture and log agent reasoning and tool calls in real-time.

        Args:
            task: Task object to execute

        Returns:
            Dictionary with execution results
        """
        agent_name = task.agent
        activity_logger = get_activity_logger()

        # Check if agent exists
        if agent_name not in self.agents:
            error_msg = f"Agent {agent_name} not found"
            logger.error(error_msg)
            await activity_logger.log_error(error_msg, agent_name)
            self.task_manager.mark_failed(task.task_id, error_msg)
            return {
                "status": "error",
                "task_id": task.task_id,
                "error": error_msg,
            }

        # Mark task as in progress
        self.task_manager.mark_in_progress(task.task_id)

        # Log task start
        await activity_logger.log_task_start(agent_name, task.task_id, task.description)

        # Check if task requires materials - call Materials Supplier MCP
        if task.materials:
            try:
                await self._handle_task_materials(task, activity_logger)
            except Exception as e:
                logger.warning(f"Materials handling failed for task {task.task_id}: {e}")
                # Continue with task execution even if materials check fails

        # Check if task involves permits - call Permitting Service MCP
        task_desc_lower = task.description.lower()
        if "permit" in task_desc_lower or task.phase == "permitting":
            try:
                await self._handle_task_permitting(task, activity_logger)
            except Exception as e:
                logger.warning(f"Permitting handling failed for task {task.task_id}: {e}")
                # Continue with task execution even if permitting check fails

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
            # Execute task with Strands agent using streaming for real-time activity
            logger.info(f"Delegating task {task.task_id} to {agent_name}")

            # Set a timeout per task - catch infinite loops faster
            timeout_seconds = getattr(settings, "task_timeout_seconds", 300)

            try:
                # Try streaming first for real-time activity logging
                result = await asyncio.wait_for(
                    self._execute_with_streaming(agent, agent_name, task.task_id, task_prompt),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                error_msg = (
                    f"Task {task.task_id} timed out after {timeout_seconds} seconds. "
                    f"Agent '{agent_name}' likely stuck in a loop. "
                    f"Check if the agent is calling the same tool repeatedly."
                )
                logger.error(error_msg)
                logger.error(f"Task description: {task.description}")
                await activity_logger.log_task_failed(agent_name, task.task_id, error_msg)
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

            # Log task completion
            await activity_logger.log_task_complete(agent_name, task.task_id, result)

            # Mark task as completed
            self.task_manager.mark_completed(task.task_id, task_result)

            return task_result

        except Exception as e:
            error_msg = f"Error executing task {task.task_id}: {str(e)}"
            logger.error(error_msg)
            await activity_logger.log_task_failed(agent_name, task.task_id, str(e))
            self.task_manager.mark_failed(task.task_id, error_msg)
            return {
                "status": "error",
                "task_id": task.task_id,
                "error": error_msg,
            }

    async def _handle_task_materials(self, task: Task, activity_logger) -> None:
        """
        Handle materials for a task by checking availability via MCP.
        
        Args:
            task: The task requiring materials
            activity_logger: Activity logger instance
        """
        # Map common material names to material IDs in the supplier catalog
        material_id_map = {
            "2x4": "2x4_studs",
            "2x4 lumber": "2x4_studs",
            "2x4 studs": "2x4_studs",
            "lumber": "2x4_studs",
            "plywood": "plywood_sheets",
            "plywood sheets": "plywood_sheets",
            "electrical wire": "electrical_wire",
            "wire": "electrical_wire",
            "outlets": "outlets",
            "outlet": "outlets",
            "light fixture": "light_fixtures",
            "light fixtures": "light_fixtures",
            "pvc": "pvc_pipes",
            "pvc pipes": "pvc_pipes",
            "copper pipes": "copper_pipes",
            "sink": "sink",
            "concrete": "concrete_bags",
            "concrete mix": "concrete_bags",
            "bricks": "bricks",
            "brick": "bricks",
            "paint": "interior_paint",
            "interior paint": "interior_paint",
            "primer": "primer",
            "hvac": "hvac_unit",
            "hvac unit": "hvac_unit",
            "ductwork": "ductwork",
            "shingles": "shingles",
            "asphalt shingles": "shingles",
            "underlayment": "underlayment",
            "roofing felt": "underlayment",
        }
        
        # Convert task materials to material IDs
        material_ids = []
        for material in task.materials:
            material_lower = material.lower().strip()
            if material_lower in material_id_map:
                material_ids.append(material_id_map[material_lower])
            else:
                # Try partial matching
                for key, value in material_id_map.items():
                    if key in material_lower or material_lower in key:
                        material_ids.append(value)
                        break
        
        # Remove duplicates
        material_ids = list(set(material_ids))
        
        if material_ids:
            logger.info(f"Checking availability for materials: {material_ids}")
            try:
                availability = await self.check_materials_availability(material_ids)
                logger.info(f"Materials availability: {availability}")
            except Exception as e:
                logger.warning(f"Failed to check materials availability: {e}")

    async def _handle_task_permitting(self, task: Task, activity_logger) -> None:
        """
        Handle permitting for a task by interacting with Permitting Service MCP.
        
        Args:
            task: The task involving permits
            activity_logger: Activity logger instance
        """
        task_desc_lower = task.description.lower()
        
        # Determine permit type based on task description
        permit_type = "building"  # default
        if "electrical" in task_desc_lower:
            permit_type = "electrical"
        elif "plumbing" in task_desc_lower:
            permit_type = "plumbing"
        elif "hvac" in task_desc_lower or "mechanical" in task_desc_lower:
            permit_type = "mechanical"
        
        # Get required permits for this type of work
        work_items = [task.description]
        if task.phase:
            work_items.append(task.phase)
        
        try:
            project_type = self.current_project.get("type", "construction") if self.current_project else "construction"
            required_permits = await self.get_required_permits(project_type, work_items)
            logger.info(f"Required permits for task {task.task_id}: {required_permits}")
        except Exception as e:
            logger.warning(f"Failed to get required permits: {e}")

    async def _execute_with_streaming(
        self, agent: Any, agent_name: str, task_id: str, prompt: str
    ) -> Any:
        """
        Execute agent with streaming to capture real-time activity.

        Attempts to use stream_async for real-time logging of reasoning and tool calls.
        Falls back to invoke_async if streaming is not available.
        """
        activity_logger = get_activity_logger()

        # Check if agent supports streaming
        if hasattr(agent, "stream_async"):
            try:
                result_text = ""
                async for event in agent.stream_async(prompt):
                    # Process streaming events
                    if hasattr(event, "event_type"):
                        event_type = event.event_type

                        if event_type == "text":
                            # Agent is generating text (reasoning)
                            text = getattr(event, "text", "")
                            result_text += text

                        elif event_type == "tool_use":
                            # Agent is calling a tool
                            tool_name = getattr(event, "name", "unknown")
                            tool_input = getattr(event, "input", {})
                            await activity_logger.log_tool_call(
                                agent_name, task_id, tool_name, tool_input
                            )

                        elif event_type == "tool_result":
                            # Tool returned a result
                            tool_name = getattr(event, "name", "unknown")
                            tool_output = getattr(event, "output", None)
                            await activity_logger.log_tool_result(
                                agent_name, task_id, tool_name, tool_output
                            )

                    elif hasattr(event, "content"):
                        # Handle content blocks
                        content = event.content
                        if isinstance(content, str):
                            result_text += content

                # Log final reasoning if we captured any
                if result_text:
                    await activity_logger.log_thinking(agent_name, task_id, result_text)

                return result_text or "Task completed"

            except Exception as e:
                logger.warning(f"Streaming failed for {agent_name}, falling back to invoke: {e}")
                # Fall through to invoke_async

        # Fallback to regular invoke_async
        result = await agent.invoke_async(prompt)

        # Try to extract tool calls from the result for logging
        if hasattr(result, "messages"):
            for msg in result.messages:
                if hasattr(msg, "tool_calls"):
                    for tool_call in msg.tool_calls:
                        tool_name = getattr(tool_call, "name", "unknown")
                        tool_args = getattr(tool_call, "arguments", {})
                        await activity_logger.log_tool_call(
                            agent_name, task_id, tool_name, tool_args
                        )

        # Log the result text if available
        result_text = ""
        if hasattr(result, "text"):
            result_text = result.text
        elif isinstance(result, str):
            result_text = result

        if result_text:
            await activity_logger.log_thinking(agent_name, task_id, result_text)

        return result

    async def _execute_planning_with_streaming(self, prompt: str) -> Any:
        """
        Execute planning agent and capture activity.

        Uses invoke_async for reliable results - Strands agents don't support
        the expected streaming interface, so we log activity after completion.
        """
        activity_logger = get_activity_logger()
        agent = self.planning_agent

        # Fallback to regular invoke_async
        await activity_logger.log_info("Using non-streaming planning mode", "Planner")
        result = await agent.invoke_async(prompt)

        # Log final result
        if hasattr(result, "text"):
            await activity_logger.log_thinking("Planner", None, result.text)

        return result

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
                    # Gather information about blocked tasks
                    blocked_tasks = []
                    for task in self.task_manager.tasks.values():
                        if task.status == TaskStatus.PENDING:
                            blocked_tasks.append(f"{task.description} (assigned to {task.agent})")

                    error_msg = f"Dependency deadlock detected: {pending} pending tasks but none can execute"
                    logger.error(error_msg)
                    logger.error(f"Blocked tasks: {blocked_tasks}")

                    # Store detailed error information for API response
                    self.last_error = {
                        "type": "stuck_state",
                        "title": "Project Execution Stuck",
                        "message": "The project cannot proceed because tasks are waiting for dependencies that will never complete.",
                        "blocked_tasks": blocked_tasks,
                        "suggestions": [
                            "Some tasks may be missing required information",
                            "Check if all assigned agents are properly configured",
                            "Consider resetting the project with more complete details",
                        ],
                    }
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

        result = {
            "status": "completed" if self.project_phase == "completed" else "partial",
            "project": self.current_project,
            "final_status": final_status,
            "total_iterations": iteration,
            "execution_summary": all_results,
        }

        # Include error details if project got stuck
        if self.last_error:
            result["error_details"] = self.last_error

        return result

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
