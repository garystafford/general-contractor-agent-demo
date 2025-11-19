"""
General Contractor orchestration agent.
"""

from typing import Dict, List, Any, Optional
from backend.orchestration.task_manager import TaskManager, Task, TaskStatus
from backend.agents import (
    create_architect_agent,
    create_carpenter_agent,
    create_electrician_agent,
    create_plumber_agent,
    create_mason_agent,
    create_painter_agent,
    create_hvac_agent,
    create_roofer_agent,
)
import asyncio
import logging

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

        # Project state
        self.current_project: Optional[Dict[str, Any]] = None
        self.project_phase = "idle"  # idle, planning, in_progress, completed

        logger.info("General Contractor initialized with 8 specialized Strands agents")

    async def start_project(
        self, project_description: str, project_type: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Start a new construction project.

        Args:
            project_description: Description of the project
            project_type: Type of project (kitchen_remodel, new_construction, etc.)
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
        }

        # Generate task sequence for this project type
        tasks = self.task_manager.create_project_tasks(project_type, **kwargs)

        self.project_phase = "planning"

        return {
            "status": "success",
            "message": f"Project initialized: {project_type}",
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
        task_prompt = f"""Task ID: {task.task_id}
Description: {task.description}

Requirements: {task.requirements}
Materials needed: {task.materials}

Please complete this task using your specialized tools."""

        try:
            # Execute task with Strands agent using invoke_async
            logger.info(f"Delegating task {task.task_id} to {agent_name}")
            result = await agent.invoke_async(task_prompt)

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
                # This shouldn't happen in a well-sequenced project
                logger.warning("Project is waiting for dependencies")
                break

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

    def reset(self) -> None:
        """Reset the contractor for a new project."""
        self.task_manager.clear()
        self.current_project = None
        self.project_phase = "idle"
        logger.info("General Contractor reset")
