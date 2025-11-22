"""
Test dynamic project planning for arbitrary construction projects.

This test demonstrates the system's ability to plan and execute ANY project type,
not just the 5 hardcoded templates.

Usage:
    python tests/test_dynamic_planning.py          # Show plan only
    python tests/test_dynamic_planning.py execute  # Execute with real agents (requires AWS)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

from backend.agents.general_contractor import GeneralContractorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_dog_house_planning():
    """Test dynamic planning for a dog house project."""

    print("=" * 80)
    print(" " * 20 + "DYNAMIC PROJECT PLANNING TEST")
    print(" " * 25 + "DOG HOUSE CONSTRUCTION")
    print("=" * 80)
    print()
    print("This test demonstrates dynamic planning for arbitrary project types.")
    print("The Planning Agent will use Claude's knowledge to break down the project.")
    print()

    # Initialize contractor
    print("🏗️  INITIALIZING GENERAL CONTRACTOR")
    print("-" * 80)
    contractor = GeneralContractorAgent()
    print("✓ Initialized with 8 specialized agents + Planning Agent (lazy-loaded)")
    print()

    # Project details
    project_type = "dog_house"
    description = "Build a medium-sized dog house for a 50-pound dog with weatherproof roof and insulated walls"
    parameters = {
        "dog_size": "medium",
        "dimensions": {"width": 3, "length": 4, "height": 3},
        "weatherproof": True,
        "insulated": True,
    }

    print("📋 PROJECT SPECIFICATIONS")
    print("-" * 80)
    print(f"   • Project Type: {project_type}")
    print(f"   • Description: {description}")
    print(f"   • Dog Size: {parameters['dog_size']}")
    print(
        f"   • Dimensions: {parameters['dimensions']['width']}ft W × {parameters['dimensions']['length']}ft L × {parameters['dimensions']['height']}ft H"
    )
    print(f"   • Weatherproof: {parameters['weatherproof']}")
    print(f"   • Insulated: {parameters['insulated']}")
    print()

    print("🤖 USING DYNAMIC PLANNING (LLM-based)")
    print("-" * 80)
    print("The Planning Agent will:")
    print("  1. Analyze project requirements")
    print("  2. Generate task breakdown")
    print("  3. Determine dependencies")
    print("  4. Assign construction phases")
    print("  5. Select appropriate specialist agents")
    print()

    # Check if we should execute or just plan
    execute_mode = len(sys.argv) > 1 and sys.argv[1] == "execute"

    if execute_mode:
        print("⚠️  EXECUTE MODE: Will use real Claude AI agents (requires AWS)")
        print()
        input("Press ENTER to start planning and execution...")
    else:
        print("ℹ️  PLAN MODE: Will generate plan but not execute (requires AWS for planning)")
        print()
        input("Press ENTER to start planning...")

    print()

    try:
        # Initialize MCP clients
        print("🔌 Initializing MCP clients...")
        await contractor.initialize_mcp_clients()
        print("✓ MCP clients initialized")
        print()

        # Start project (this will trigger dynamic planning)
        print("📝 STARTING PROJECT WITH DYNAMIC PLANNING...")
        print("-" * 80)

        result = await contractor.start_project(
            project_description=description, project_type=project_type, **parameters
        )

        print(f"✓ Status: {result['status'].upper()}")
        print(f"✓ Message: {result['message']}")
        print(f"✓ Planning Method: {result['project']['planning_method']}")
        print(f"✓ Total Tasks: {result['total_tasks']}")
        print()

        # Display task breakdown
        print("=" * 80)
        print("📊 GENERATED PROJECT PLAN")
        print("=" * 80)
        print()

        breakdown = result["task_breakdown"]

        # Tasks by phase
        print("📅 TASKS BY PHASE:")
        print("-" * 80)
        for phase, tasks in breakdown["by_phase"].items():
            print(f"\n{phase.upper().replace('_', ' ')}:")
            for task in tasks:
                print(f"  • Task #{task['id']}: {task['description']}")

        print()

        # Tasks by agent
        print("👥 TASKS BY AGENT:")
        print("-" * 80)
        for agent, count in breakdown["by_agent"].items():
            print(f"  • {agent}: {count} task(s)")

        print()
        print("=" * 80)

        # Get all tasks
        all_tasks = contractor.get_all_tasks()

        if execute_mode:
            print()
            print("🚀 EXECUTING PROJECT")
            print("=" * 80)
            input("Press ENTER to begin execution...")
            print()

            execution_result = await contractor.execute_entire_project()

            print()
            print("=" * 80)
            print("📊 EXECUTION SUMMARY")
            print("=" * 80)
            print()

            final_status = execution_result["final_status"]
            print(f"✅ Completed: {final_status['completed']}/{final_status['total_tasks']}")
            print(f"❌ Failed: {final_status['failed']}")
            print(f"⏳ Pending: {final_status['pending']}")
            print(f"📈 Completion: {final_status['completion_percentage']:.1f}%")
            print()

            if final_status["completion_percentage"] == 100:
                print("🎉 PROJECT COMPLETED SUCCESSFULLY!")
            else:
                print("⚠️  PROJECT PARTIALLY COMPLETED")

            print()
        else:
            print()
            print("ℹ️  PLAN MODE: Execution skipped")
            print()
            print("To execute this plan with real AI agents:")
            print("  python tests/test_dynamic_planning.py execute")
            print()

        # Display individual tasks with details
        print("=" * 80)
        print("📋 DETAILED TASK LIST")
        print("=" * 80)
        print()

        for task in all_tasks:
            print(f"Task #{task.task_id}: {task.description}")
            print(f"  Agent: {task.agent}")
            print(f"  Phase: {task.phase}")
            print(f"  Dependencies: {task.dependencies if task.dependencies else 'None'}")
            if task.requirements:
                print(f"  Requirements: {task.requirements}")
            if task.materials:
                print(f"  Materials: {', '.join(task.materials)}")
            print()

        # Clean up
        await contractor.close_mcp_clients()

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        print()
        print("=" * 80)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 80)
        print()

        if "AWS" in str(e) or "credentials" in str(e).lower():
            print("⚠️  This test requires AWS Bedrock credentials.")
            print()
            print("To configure AWS credentials:")
            print("  1. Set up AWS CLI: aws configure")
            print("  2. Or set environment variables:")
            print("     - AWS_REGION")
            print("     - AWS_PROFILE or AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY")
            print()

        raise


async def test_multiple_project_types():
    """Test dynamic planning with various project types."""

    print("=" * 80)
    print(" " * 15 + "DYNAMIC PLANNING - MULTIPLE PROJECT TYPES")
    print("=" * 80)
    print()

    projects = [
        {
            "type": "dog_house",
            "description": "Build a medium dog house with weatherproof roof",
            "params": {"dog_size": "medium"},
        },
        {
            "type": "deck",
            "description": "Build a 12x16 wooden deck with stairs and railing",
            "params": {"dimensions": {"width": 12, "length": 16}},
        },
        {
            "type": "treehouse",
            "description": "Build a simple treehouse platform with ladder",
            "params": {"height": 8, "platform_size": "6x8"},
        },
        {
            "type": "fence",
            "description": "Install 100 linear feet of 6-foot privacy fence",
            "params": {"length": 100, "height": 6, "style": "privacy"},
        },
    ]

    print(f"Testing dynamic planning for {len(projects)} different project types:")
    for i, project in enumerate(projects, 1):
        print(f"  {i}. {project['type']}: {project['description']}")
    print()

    input("Press ENTER to start testing...")
    print()

    contractor = GeneralContractorAgent()
    await contractor.initialize_mcp_clients()

    results = []

    for i, project in enumerate(projects, 1):
        print("=" * 80)
        print(f"TEST {i}/{len(projects)}: {project['type'].upper()}")
        print("=" * 80)
        print()

        try:
            result = await contractor.start_project(
                project_description=project["description"],
                project_type=project["type"],
                **project["params"],
            )

            print("✓ Planning successful")
            print(f"✓ Total tasks: {result['total_tasks']}")
            print(f"✓ Planning method: {result['project']['planning_method']}")

            results.append(
                {
                    "project_type": project["type"],
                    "status": "success",
                    "tasks": result["total_tasks"],
                }
            )

        except Exception as e:
            logger.error(f"Failed to plan {project['type']}: {e}")
            results.append({"project_type": project["type"], "status": "failed", "error": str(e)})

        # Reset for next project
        await contractor.reset()
        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print()

    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")

    print(f"✅ Successful: {successful}/{len(projects)}")
    print(f"❌ Failed: {failed}/{len(projects)}")
    print()

    for result in results:
        status_icon = "✓" if result["status"] == "success" else "✗"
        if result["status"] == "success":
            print(f"  {status_icon} {result['project_type']}: {result['tasks']} tasks")
        else:
            print(f"  {status_icon} {result['project_type']}: {result['error']}")

    print()

    await contractor.close_mcp_clients()


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("🧪 DYNAMIC PROJECT PLANNING TESTS")
    print("=" * 80)
    print()

    # Run dog house test
    asyncio.run(test_dog_house_planning())

    # Optionally run multiple project types test
    if "--all" in sys.argv:
        print()
        asyncio.run(test_multiple_project_types())
