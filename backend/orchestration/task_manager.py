"""
Task Manager for handling task sequencing and dependencies.
"""

from typing import Dict, List, Any, Set, Optional
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enum."""

    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a construction task."""

    task_id: str
    agent: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    phase: str = "construction"
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    requirements: Dict[str, Any] = field(default_factory=dict)
    materials: List[str] = field(default_factory=list)


class TaskManager:
    """Manages task sequencing and dependencies for construction projects."""

    # Define phase ordering
    PHASE_ORDER = [
        "planning",
        "permitting",
        "foundation",
        "framing",
        "rough_in",
        "inspection",
        "finishing",
        "final_inspection",
    ]

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()

        logger.info("TaskManager initialized")

    def add_task(self, task: Task) -> None:
        """Add a task to the project."""
        self.tasks[task.task_id] = task
        logger.info(f"Added task {task.task_id}: {task.description}")

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_ready_tasks(self) -> List[Task]:
        """Get all tasks that are ready to execute (dependencies met)."""
        ready_tasks = []

        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                if self._are_dependencies_met(task):
                    task.status = TaskStatus.READY
                    ready_tasks.append(task)
                    logger.info(f"Task {task.task_id} is now ready")

        return ready_tasks

    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all dependencies for a task are completed."""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True

    def mark_in_progress(self, task_id: str) -> bool:
        """Mark a task as in progress."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.IN_PROGRESS
            logger.info(f"Task {task_id} marked as in progress")
            return True
        return False

    def mark_completed(self, task_id: str, result: Any = None) -> bool:
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].result = result
            self.completed_tasks.add(task_id)
            logger.info(f"Task {task_id} completed")
            return True
        return False

    def mark_failed(self, task_id: str, error: str) -> bool:
        """Mark a task as failed."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].result = {"error": error}
            self.failed_tasks.add(task_id)
            logger.error(f"Task {task_id} failed: {error}")
            return True
        return False

    def get_parallel_tasks(self) -> List[List[Task]]:
        """
        Group tasks that can run in parallel.

        Returns groups of tasks that have no dependencies on each other
        and are in the same phase.
        """
        ready_tasks = self.get_ready_tasks()

        # Group by phase
        phase_groups: Dict[str, List[Task]] = {}
        for task in ready_tasks:
            if task.phase not in phase_groups:
                phase_groups[task.phase] = []
            phase_groups[task.phase].append(task)

        # Return groups in phase order
        parallel_groups = []
        for phase in self.PHASE_ORDER:
            if phase in phase_groups:
                parallel_groups.append(phase_groups[phase])

        return parallel_groups

    def get_next_phase_tasks(self) -> List[Task]:
        """Get tasks for the next phase that's ready to start."""
        ready_tasks = self.get_ready_tasks()

        if not ready_tasks:
            return []

        # Get the earliest phase that has ready tasks
        for phase in self.PHASE_ORDER:
            phase_tasks = [t for t in ready_tasks if t.phase == phase]
            if phase_tasks:
                return phase_tasks

        return ready_tasks

    def create_project_tasks(self, project_type: str, **kwargs) -> List[Task]:
        """
        Create standard task sequence for a project type.

        Args:
            project_type: Type of project (kitchen_remodel, new_construction, etc.)
            **kwargs: Additional parameters specific to project type

        Returns:
            List of created tasks
        """
        tasks = []

        if project_type == "kitchen_remodel":
            tasks = self._create_kitchen_remodel_tasks(**kwargs)
        elif project_type == "bathroom_remodel":
            tasks = self._create_bathroom_remodel_tasks(**kwargs)
        elif project_type == "new_construction":
            tasks = self._create_new_construction_tasks(**kwargs)
        elif project_type == "addition":
            tasks = self._create_addition_tasks(**kwargs)
        elif project_type == "shed_construction":
            tasks = self._create_shed_construction_tasks(**kwargs)
        else:
            logger.warning(f"Unknown project type: {project_type}")

        # Add all tasks to manager
        for task in tasks:
            self.add_task(task)

        return tasks

    def _create_kitchen_remodel_tasks(self, **kwargs) -> List[Task]:
        """Create tasks for a kitchen remodel project."""
        return [
            Task("1", "Architect", "Design kitchen layout", [], "planning"),
            Task("2", "Permitting", "Apply for building permit", ["1"], "permitting"),
            Task("3", "Carpenter", "Remove old cabinets", ["2"], "demolition"),
            Task("4", "Plumber", "Update plumbing rough-in", ["3"], "rough_in"),
            Task("5", "Electrician", "Update electrical rough-in", ["3"], "rough_in"),
            Task(
                "6",
                "Permitting",
                "Schedule rough-in inspection",
                ["4", "5"],
                "inspection",
            ),
            Task("7", "Carpenter", "Install new cabinets", ["6"], "finishing"),
            Task("8", "Electrician", "Install lighting fixtures", ["7"], "finishing"),
            Task("9", "Plumber", "Install sink and fixtures", ["7"], "finishing"),
            Task("10", "Painter", "Paint walls", ["7"], "finishing"),
            Task(
                "11",
                "Permitting",
                "Final inspection",
                ["8", "9", "10"],
                "final_inspection",
            ),
        ]

    def _create_bathroom_remodel_tasks(self, **kwargs) -> List[Task]:
        """Create tasks for a bathroom remodel project."""
        return [
            Task("1", "Architect", "Design bathroom layout", [], "planning"),
            Task("2", "Permitting", "Apply for permits", ["1"], "permitting"),
            Task("3", "Carpenter", "Demolition work", ["2"], "demolition"),
            Task("4", "Plumber", "Rough-in plumbing", ["3"], "rough_in"),
            Task("5", "Electrician", "Rough-in electrical", ["3"], "rough_in"),
            Task(
                "6",
                "Permitting",
                "Rough-in inspection",
                ["4", "5"],
                "inspection",
            ),
            Task("7", "Carpenter", "Install drywall", ["6"], "finishing"),
            Task("8", "Painter", "Paint and tile work", ["7"], "finishing"),
            Task("9", "Plumber", "Install fixtures", ["8"], "finishing"),
            Task("10", "Electrician", "Install light fixtures", ["8"], "finishing"),
            Task(
                "11",
                "Permitting",
                "Final inspection",
                ["9", "10"],
                "final_inspection",
            ),
        ]

    def _create_new_construction_tasks(self, **kwargs) -> List[Task]:
        """Create tasks for a new construction project."""
        return [
            Task("1", "Architect", "Create architectural plans", [], "planning"),
            Task("2", "Permitting", "Apply for building permits", ["1"], "permitting"),
            Task("3", "Mason", "Pour foundation", ["2"], "foundation"),
            Task("4", "Carpenter", "Frame walls and roof", ["3"], "framing"),
            Task("5", "Roofer", "Install roof", ["4"], "framing"),
            Task("6", "Electrician", "Electrical rough-in", ["4"], "rough_in"),
            Task("7", "Plumber", "Plumbing rough-in", ["4"], "rough_in"),
            Task("8", "HVAC", "HVAC installation", ["4"], "rough_in"),
            Task(
                "9",
                "Permitting",
                "Rough-in inspection",
                ["6", "7", "8"],
                "inspection",
            ),
            Task("10", "Carpenter", "Install drywall", ["9"], "finishing"),
            Task("11", "Painter", "Paint interior", ["10"], "finishing"),
            Task("12", "Carpenter", "Install flooring and trim", ["11"], "finishing"),
            Task("13", "Electrician", "Install fixtures", ["10"], "finishing"),
            Task("14", "Plumber", "Install fixtures", ["10"], "finishing"),
            Task(
                "15",
                "Permitting",
                "Final inspection",
                ["12", "13", "14"],
                "final_inspection",
            ),
        ]

    def _create_addition_tasks(self, **kwargs) -> List[Task]:
        """Create tasks for a home addition project."""
        return [
            Task("1", "Architect", "Design addition plans", [], "planning"),
            Task("2", "Permitting", "Apply for permits", ["1"], "permitting"),
            Task("3", "Mason", "Pour foundation", ["2"], "foundation"),
            Task("4", "Carpenter", "Frame addition", ["3"], "framing"),
            Task("5", "Roofer", "Extend roof", ["4"], "framing"),
            Task("6", "Electrician", "Electrical rough-in", ["4"], "rough_in"),
            Task("7", "Plumber", "Plumbing rough-in", ["4"], "rough_in"),
            Task("8", "HVAC", "Extend HVAC", ["4"], "rough_in"),
            Task(
                "9",
                "Permitting",
                "Rough-in inspection",
                ["6", "7", "8"],
                "inspection",
            ),
            Task("10", "Carpenter", "Drywall and finishing", ["9"], "finishing"),
            Task("11", "Painter", "Paint", ["10"], "finishing"),
            Task(
                "12",
                "Permitting",
                "Final inspection",
                ["11"],
                "final_inspection",
            ),
        ]

    def _create_shed_construction_tasks(self, **kwargs) -> List[Task]:
        """Create tasks for a storage shed construction project."""
        has_electrical = kwargs.get("has_electrical", False)
        has_foundation = kwargs.get("has_foundation", True)
        dimensions = kwargs.get("dimensions", {"width": 10, "length": 12})

        tasks = []
        task_id = 1

        # Planning phase
        tasks.append(
            Task(
                str(task_id),
                "Architect",
                f"Design shed plans ({dimensions['width']}x{dimensions['length']} ft)",
                [],
                "planning",
                requirements=dimensions,
                materials=["blueprints", "specifications"],
            )
        )
        task_id += 1

        # Foundation phase (if needed)
        if has_foundation:
            tasks.append(
                Task(
                    str(task_id),
                    "Mason",
                    "Pour concrete foundation slab",
                    [str(task_id - 1)],
                    "foundation",
                    requirements={"area": dimensions["width"] * dimensions["length"]},
                    materials=["concrete", "rebar", "gravel"],
                )
            )
            foundation_task_id = str(task_id)
            task_id += 1
        else:
            foundation_task_id = "1"  # Depends on planning if no foundation

        # Framing phase
        tasks.append(
            Task(
                str(task_id),
                "Carpenter",
                "Frame walls and install door/window openings",
                [foundation_task_id],
                "framing",
                requirements={"wall_count": 4, "door_count": 1, "window_count": 1},
                materials=[
                    "2x4 lumber",
                    "plywood",
                    "nails",
                    "door frame",
                    "window frame",
                ],
            )
        )
        framing_task_id = str(task_id)
        task_id += 1

        tasks.append(
            Task(
                str(task_id),
                "Carpenter",
                "Build and install roof trusses",
                [framing_task_id],
                "framing",
                requirements={"span": dimensions["width"]},
                materials=["2x4 lumber", "truss plates", "plywood sheathing"],
            )
        )
        roof_framing_task_id = str(task_id)
        task_id += 1

        # Roofing phase
        tasks.append(
            Task(
                str(task_id),
                "Roofer",
                "Install roofing (shingles and underlayment)",
                [roof_framing_task_id],
                "rough_in",
                requirements={"area": dimensions["width"] * dimensions["length"] * 1.3},
                materials=["asphalt shingles", "roofing felt", "drip edge", "nails"],
            )
        )
        roofing_task_id = str(task_id)
        task_id += 1

        # Electrical (if needed)
        if has_electrical:
            tasks.append(
                Task(
                    str(task_id),
                    "Electrician",
                    "Install electrical wiring, outlet, and light fixture",
                    [framing_task_id],
                    "rough_in",
                    requirements={"outlets": 1, "lights": 1},
                    materials=["electrical wire", "outlet", "light fixture", "breaker"],
                )
            )
            electrical_dependencies = [roofing_task_id, str(task_id)]
            task_id += 1
        else:
            electrical_dependencies = [roofing_task_id]

        # Exterior finishing
        tasks.append(
            Task(
                str(task_id),
                "Carpenter",
                "Install exterior siding",
                electrical_dependencies,
                "finishing",
                requirements={
                    "area": (dimensions["width"] + dimensions["length"])
                    * 2
                    * dimensions.get("height", 8)
                },
                materials=["siding panels", "trim", "corner boards", "nails"],
            )
        )
        siding_task_id = str(task_id)
        task_id += 1

        tasks.append(
            Task(
                str(task_id),
                "Carpenter",
                "Install door and window",
                [siding_task_id],
                "finishing",
                requirements={"door_count": 1, "window_count": 1},
                materials=["entry door", "window", "hinges", "hardware"],
            )
        )
        doors_windows_task_id = str(task_id)
        task_id += 1

        # Painting
        tasks.append(
            Task(
                str(task_id),
                "Painter",
                "Paint exterior finish",
                [doors_windows_task_id],
                "finishing",
                requirements={"coats": 2},
                materials=["exterior paint", "primer", "brushes", "rollers"],
            )
        )
        painting_task_id = str(task_id)
        task_id += 1

        # Final inspection
        final_dependencies = [painting_task_id]
        tasks.append(
            Task(
                str(task_id),
                "Carpenter",
                "Final walkthrough and cleanup",
                final_dependencies,
                "final_inspection",
                requirements={
                    "checklist": [
                        "doors close properly",
                        "roof is sealed",
                        "paint is dry",
                    ]
                },
                materials=[],
            )
        )

        return tasks

    def get_project_status(self) -> Dict[str, Any]:
        """Get overall project status."""
        total_tasks = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        in_progress = len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
        pending = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_percentage": ((completed / total_tasks * 100) if total_tasks > 0 else 0),
        }

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values())

    def clear(self) -> None:
        """Clear all tasks and reset state."""
        self.tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        logger.info("TaskManager cleared")
