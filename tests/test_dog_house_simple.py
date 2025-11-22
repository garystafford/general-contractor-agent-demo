"""
Simple non-interactive test for dog house planning.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.general_contractor import GeneralContractorAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_dog_house():
    """Simple test for dog house planning."""

    print("=" * 80)
    print("Testing Dog House Dynamic Planning")
    print("=" * 80)
    print()

    contractor = GeneralContractorAgent()

    try:
        # Initialize MCP clients
        await contractor.initialize_mcp_clients()

        # Start project
        print("Starting dog house project with dynamic planning...")
        result = await contractor.start_project(
            project_description="Build a medium dog house with weatherproof roof",
            project_type="dog_house",
            dog_size="medium",
            weatherproof=True,
        )

        print(f"\n✓ Status: {result['status']}")
        print(f"✓ Planning method: {result['project']['planning_method']}")
        print(f"✓ Total tasks: {result['total_tasks']}")

        if result["total_tasks"] > 0:
            print("\n✓ Tasks generated successfully!")

            # Show task breakdown
            breakdown = result["task_breakdown"]
            print(f"\nPhases: {list(breakdown['by_phase'].keys())}")
            print(f"Agents: {list(breakdown['by_agent'].keys())}")

            # Show first few tasks
            all_tasks = contractor.get_all_tasks()
            print("\nFirst 3 tasks:")
            for i, task in enumerate(all_tasks[:3], 1):
                print(f"  {i}. {task.agent}: {task.description}")
        else:
            print("\n✗ No tasks generated!")
            return False

        await contractor.close_mcp_clients()

        print("\n" + "=" * 80)
        print("✅ TEST PASSED")
        print("=" * 80)
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_dog_house())
    sys.exit(0 if success else 1)
