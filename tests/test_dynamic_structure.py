"""
Quick verification test for dynamic planning structure (no AWS required).

This test verifies:
1. Planning agent is lazy-loaded
2. System recognizes unsupported project types
3. TaskManager has the new methods
4. GeneralContractor has the new start_project signature
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.general_contractor import GeneralContractorAgent
from backend.orchestration.task_manager import TaskManager


def test_structure():
    """Test that all the new structure is in place."""

    print("=" * 80)
    print(" " * 20 + "DYNAMIC PLANNING STRUCTURE TEST")
    print("=" * 80)
    print()

    # Test 1: TaskManager has supported types list
    print("Test 1: TaskManager.SUPPORTED_PROJECT_TYPES")
    print("-" * 80)
    tm = TaskManager()
    assert hasattr(tm, "SUPPORTED_PROJECT_TYPES"), "TaskManager missing SUPPORTED_PROJECT_TYPES"
    print(f"✓ Supported types: {tm.SUPPORTED_PROJECT_TYPES}")
    print()

    # Test 2: TaskManager has create_tasks_from_plan method
    print("Test 2: TaskManager.create_tasks_from_plan()")
    print("-" * 80)
    assert hasattr(tm, "create_tasks_from_plan"), "TaskManager missing create_tasks_from_plan"
    print("✓ Method exists")
    print()

    # Test 3: Test create_tasks_from_plan with sample data
    print("Test 3: Create tasks from plan (sample data)")
    print("-" * 80)
    sample_plan = [
        {
            "task_id": "1",
            "agent": "Architect",
            "description": "Design dog house structure",
            "dependencies": [],
            "phase": "planning",
            "requirements": "Create scaled drawings",
            "materials": ["paper", "pencils"],
        },
        {
            "task_id": "2",
            "agent": "Carpenter",
            "description": "Build base frame",
            "dependencies": ["1"],
            "phase": "framing",
            "requirements": {"lumber_type": "pressure-treated"},
            "materials": ["2x4 lumber", "screws"],
        },
    ]

    tasks = tm.create_tasks_from_plan(sample_plan)
    assert len(tasks) == 2, f"Expected 2 tasks, got {len(tasks)}"
    assert tasks[0].task_id == "1", "Task 1 ID mismatch"
    assert tasks[0].agent == "Architect", "Task 1 agent mismatch"
    assert tasks[1].dependencies == ["1"], "Task 2 dependencies mismatch"
    print(f"✓ Created {len(tasks)} tasks from plan")
    print(f"  - Task 1: {tasks[0].description} (Agent: {tasks[0].agent})")
    print(
        f"  - Task 2: {tasks[1].description} (Agent: {tasks[1].agent}, Dependencies: {tasks[1].dependencies})"
    )
    print()

    # Test 4: GeneralContractor has planning_agent property
    print("Test 4: GeneralContractor.planning_agent (lazy-loaded)")
    print("-" * 80)
    contractor = GeneralContractorAgent()
    assert hasattr(contractor, "_planning_agent"), "GeneralContractor missing _planning_agent"
    assert contractor._planning_agent is None, "Planning agent should start as None (lazy-loaded)"
    print("✓ Planning agent is lazy-loaded (initially None)")
    print()

    # Test 5: GeneralContractor.start_project has new signature
    print("Test 5: GeneralContractor.start_project signature")
    print("-" * 80)
    import inspect

    sig = inspect.signature(contractor.start_project)
    params = list(sig.parameters.keys())
    assert "use_dynamic_planning" in params, "start_project missing use_dynamic_planning parameter"
    print(f"✓ Parameters: {params}")
    print()

    # Test 6: Verify project type detection
    print("Test 6: Project type detection")
    print("-" * 80)
    supported = "kitchen_remodel"
    unsupported = "dog_house"

    is_supported = supported in tm.SUPPORTED_PROJECT_TYPES
    is_unsupported = unsupported not in tm.SUPPORTED_PROJECT_TYPES

    assert is_supported, f"{supported} should be supported"
    assert is_unsupported, f"{unsupported} should not be in supported list"

    print(f"✓ '{supported}' is in supported types: {is_supported}")
    print(f"✓ '{unsupported}' requires dynamic planning: {is_unsupported}")
    print()

    # Test 7: Verify new methods exist
    print("Test 7: GeneralContractor helper methods")
    print("-" * 80)
    assert hasattr(
        contractor, "_create_dynamic_project_plan"
    ), "Missing _create_dynamic_project_plan"
    assert hasattr(contractor, "_parse_planning_result"), "Missing _parse_planning_result"
    print("✓ _create_dynamic_project_plan exists")
    print("✓ _parse_planning_result exists")
    print()

    # Summary
    print("=" * 80)
    print("✅ ALL STRUCTURE TESTS PASSED")
    print("=" * 80)
    print()
    print("The dynamic planning system is properly integrated!")
    print()
    print("Next steps:")
    print("  1. Test with AWS credentials: uv run tests/test_dynamic_planning.py")
    print("  2. Execute full project: uv run tests/test_dynamic_planning.py execute")
    print()


if __name__ == "__main__":
    test_structure()
