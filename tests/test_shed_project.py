"""
Test script demonstrating the orchestration of building a storage shed.

This script uses the GeneralContractorAgent to coordinate multiple specialized
agents (Architect, Carpenter, Electrician, etc.) to complete a shed construction project.
"""

import asyncio
import json
from backend.agents.general_contractor import GeneralContractorAgent


async def test_shed_construction():
    """Test building a complete storage shed project."""

    print("=" * 70)
    print("STORAGE SHED CONSTRUCTION PROJECT")
    print("=" * 70)
    print()

    # Initialize the General Contractor
    print("Initializing General Contractor with specialized agents...")
    gc = GeneralContractorAgent()
    print(f"✓ General Contractor initialized with {len(gc.agents)} specialized agents")
    print()

    # Show available agents
    print("Available Agents:")
    for agent_name in gc.agents.keys():
        print(f"  • {agent_name}")
    print()

    # Define the shed project
    project_description = """
    Build a 10x12 storage shed in the customer's backyard.

    Requirements:
    - Concrete foundation
    - Wood frame construction
    - Asphalt shingle roof
    - One entry door and one window
    - Basic electrical (one outlet and overhead light)
    - Exterior paint finish

    The shed will be used for storing garden tools and equipment.
    """

    print("PROJECT DETAILS:")
    print("-" * 70)
    print(project_description)
    print()

    # Start the project
    print("PHASE 1: PROJECT PLANNING")
    print("-" * 70)

    try:
        result = await gc.start_project(
            project_description=project_description,
            project_type="shed_construction",
            dimensions={"width": 10, "length": 12, "height": 8},
            has_foundation=True,
            has_electrical=True,
            has_plumbing=False,
        )

        print(f"✓ Status: {result['status']}")
        print(f"✓ Total tasks planned: {result['total_tasks']}")
        print()

        # Show task breakdown
        if "task_breakdown" in result:
            breakdown = result["task_breakdown"]

            print("Tasks by Phase:")
            for phase, tasks in breakdown["by_phase"].items():
                print(f"\n  {phase.upper()}:")
                for task in tasks:
                    print(f"    - {task['description']}")

            print("\n\nTasks by Agent:")
            for agent, count in breakdown["by_agent"].items():
                print(f"  • {agent}: {count} tasks")

        print()
        print()

        # Execute the project
        print("PHASE 2: PROJECT EXECUTION")
        print("-" * 70)
        print("Executing project phases... (this may take a while)")
        print()

        execution_result = await gc.execute_entire_project()

        print()
        print("=" * 70)
        print("PROJECT COMPLETION SUMMARY")
        print("=" * 70)
        print()

        print(f"Status: {execution_result['status']}")
        print(f"Total Iterations: {execution_result['total_iterations']}")
        print()

        final_status = execution_result["final_status"]
        print("Final Task Status:")
        print(f"  ✓ Completed: {final_status['completed']}")
        print(f"  ⚠ Failed: {final_status['failed']}")
        print(f"  ⏳ In Progress: {final_status['in_progress']}")
        print(f"  ⏸ Pending: {final_status['pending']}")
        print()

        # Show execution summary
        if "execution_summary" in execution_result:
            print("\nPhase Execution Summary:")
            for i, phase_result in enumerate(execution_result["execution_summary"], 1):
                status = phase_result.get("status", "unknown")
                if status == "success" and "results" in phase_result:
                    completed_tasks = len(phase_result["results"])
                    print(f"  Phase {i}: ✓ Completed {completed_tasks} tasks")
                elif status == "waiting":
                    print(f"  Phase {i}: ⏳ {phase_result.get('message', 'Waiting')}")
                elif status == "error":
                    print(f"  Phase {i}: ✗ {phase_result.get('message', 'Error')}")

        print()

        # Show individual task results (if available)
        all_tasks = gc.get_all_tasks()
        if all_tasks:
            print("\nDetailed Task Results:")
            print("-" * 70)
            for task in all_tasks:
                status_icon = {
                    "pending": "⏸",
                    "in_progress": "⏳",
                    "completed": "✓",
                    "failed": "✗",
                }.get(task.status.value, "?")

                print(f"{status_icon} [{task.agent}] {task.description}")
                if task.result:
                    # Handle AgentResult object which isn't JSON serializable
                    try:
                        if isinstance(task.result, dict):
                            result_str = json.dumps(task.result, indent=6)[:200]
                        else:
                            # Convert AgentResult to string representation
                            result_str = str(task.result)[:200]
                        print(f"     Result: {result_str}...")
                    except Exception:
                        print(f"     Result: [AgentResult object]")
                if task.error:
                    print(f"     Error: {task.error}")

        print()
        print("=" * 70)
        print("✅ SHED CONSTRUCTION PROJECT TEST COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error during project execution: {e}")
        import traceback

        traceback.print_exc()

        # Show current project status even if there was an error
        print("\nCurrent Project Status:")
        status = gc.get_project_status()
        print(json.dumps(status, indent=2, default=str))


async def test_simple_shed():
    """Test a simpler version that just plans without executing."""

    print("=" * 70)
    print("SIMPLE SHED CONSTRUCTION - PLANNING ONLY")
    print("=" * 70)
    print()

    gc = GeneralContractorAgent()

    result = await gc.start_project(
        project_description="Build a basic 8x10 storage shed",
        project_type="shed_construction",
        dimensions={"width": 8, "length": 10, "height": 8},
        has_foundation=True,
        has_electrical=False,
        has_plumbing=False,
    )

    print(f"Project Status: {result['status']}")
    print(f"Total Tasks: {result['total_tasks']}")
    print()

    # Get agent statuses
    print("Agent Status:")
    all_agents = gc.get_all_agents_status()
    for name, status in all_agents.items():
        print(f"  • {name}: {len(status['tools'])} tools available")

    print()
    print("✅ Planning test completed")


if __name__ == "__main__":
    print()
    print("Select test mode:")
    print("1. Full shed construction (with execution)")
    print("2. Simple shed planning (no execution)")
    print()

    # For automated testing, default to simple planning
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "full":
        print("Running full construction test...")
        print()
        asyncio.run(test_shed_construction())
    else:
        print("Running simple planning test...")
        print("(Use 'python test_shed_project.py full' for full execution)")
        print()
        asyncio.run(test_simple_shed())
