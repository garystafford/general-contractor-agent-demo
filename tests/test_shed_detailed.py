"""
Detailed shed construction test showing full task breakdown with optional execution.
"""

import asyncio
import sys
import json
from backend.agents.general_contractor import GeneralContractorAgent


async def test_detailed_shed_execution():
    """Test detailed shed construction with full execution and output."""

    print("=" * 80)
    print(" " * 15 + "STORAGE SHED CONSTRUCTION - FULL EXECUTION")
    print("=" * 80)
    print()

    # Initialize General Contractor
    print("🏗️  INITIALIZING GENERAL CONTRACTOR")
    print("-" * 80)
    gc = GeneralContractorAgent()
    print(f"✓ Initialized with {len(gc.agents)} specialized agents")
    print()

    # Define shed project
    print("📋 PROJECT SPECIFICATIONS")
    print("-" * 80)
    print("   • Dimensions: 10 ft x 12 ft x 8 ft")
    print("   • Foundation: Concrete slab")
    print("   • Electrical: Yes (1 outlet + 1 light)")
    print()

    # Start project
    print("📝 STARTING PROJECT PLANNING...")
    print("-" * 80)
    result = await gc.start_project(
        project_description="Build a 10x12 storage shed for garden tools",
        project_type="shed_construction",
        dimensions={"width": 10, "length": 12, "height": 8},
        has_foundation=True,
        has_electrical=True,
        has_plumbing=False,
    )

    print(f"✓ Status: {result['status'].upper()}")
    print(f"✓ Total Tasks: {result['total_tasks']}")
    print()

    # Execute project with detailed output
    print("=" * 80)
    print("🚀 EXECUTING PROJECT - WATCHING AGENT REASONING & TOOL CALLS")
    print("=" * 80)
    print()

    all_tasks = gc.get_all_tasks()
    task_num = 0

    # Execute each task one by one to show detailed output
    while True:
        # Get ready tasks
        ready_tasks = gc.task_manager.get_ready_tasks()

        if not ready_tasks:
            # Check if project is complete
            status = gc.task_manager.get_project_status()
            if status["pending"] == 0 and status["in_progress"] == 0:
                break
            else:
                print("⏳ Waiting for dependencies...")
                break

        # Execute each ready task
        for task in ready_tasks:
            task_num += 1
            print()
            print("┌" + "─" * 78 + "┐")
            print(f"│ TASK #{task.task_id}: {task.description[:60]}")
            print(f"│ Agent: {task.agent}")
            print(f"│ Phase: {task.phase.upper()}")
            print("└" + "─" * 78 + "┘")
            print()

            # Show task details
            if task.requirements:
                print(f"📊 Requirements: {json.dumps(task.requirements, indent=2)}")
            if task.materials:
                print(f"🔧 Materials: {', '.join(task.materials)}")
            print()

            print("🤖 Agent is thinking and using tools...")
            print("-" * 80)

            # Execute task with streaming to see real-time reasoning
            try:
                # Mark as in progress
                gc.task_manager.mark_in_progress(task.task_id)

                # Get the agent
                agent = gc.agents[task.agent]

                # Prepare task prompt
                task_prompt = f"""Task ID: {task.task_id}
Description: {task.description}

Requirements: {task.requirements}
Materials needed: {task.materials}

Please complete this task using your specialized tools."""

                # Stream the agent's response
                print()
                full_response = {}
                text_parts = []
                tool_calls = []
                tool_results = []

                async for event in agent.stream_async(task_prompt):
                    event_type = event.get("type", "")

                    if event_type == "text":
                        # Agent thinking/reasoning
                        text = event.get("text", "")
                        if text:
                            print(f"💭 {text}", flush=True)
                            text_parts.append(text)

                    elif event_type == "tool_use":
                        # Tool being called
                        tool_name = event.get("name", "unknown")
                        tool_input = event.get("input", {})
                        print(f"\n🔧 Calling tool: {tool_name}")
                        print(f"   Input: {json.dumps(tool_input, indent=3)}")
                        tool_calls.append({"name": tool_name, "input": tool_input})

                    elif event_type == "tool_result":
                        # Tool result
                        result_content = event.get("content", {})
                        print(f"✓ Tool completed successfully")
                        if isinstance(result_content, dict):
                            print(f"   Result: {json.dumps(result_content, indent=3)}")
                        tool_results.append(result_content)

                    elif event_type == "message":
                        # Full message response
                        full_response = event

                print()
                print("✅ TASK COMPLETED")
                print("-" * 80)

                # Show summary
                if text_parts:
                    print(f"📝 Agent Reasoning: {' '.join(text_parts)}")
                if tool_calls:
                    print(f"🔧 Tools Used: {', '.join([t['name'] for t in tool_calls])}")
                if tool_results:
                    print(f"✓ Results: {len(tool_results)} tool(s) executed successfully")

                # Mark as completed
                task_result = {
                    "status": "completed",
                    "task_id": task.task_id,
                    "agent": task.agent,
                    "result": full_response,
                    "tools_used": tool_calls,
                }
                gc.task_manager.mark_completed(task.task_id, task_result)

            except Exception as e:
                print(f"\n❌ TASK FAILED")
                print("-" * 80)
                print(f"Error: {e}")
                import traceback

                traceback.print_exc()

                # Mark as failed
                error_msg = f"Error executing task: {str(e)}"
                gc.task_manager.mark_failed(task.task_id, error_msg)

            print()

    # Final summary
    print()
    print("=" * 80)
    print("📊 PROJECT COMPLETION SUMMARY")
    print("=" * 80)
    final_status = gc.task_manager.get_project_status()
    print(f"✅ Completed: {final_status['completed']}/{final_status['total_tasks']}")
    print(f"❌ Failed: {final_status['failed']}")
    print(f"⏳ Pending: {final_status['pending']}")
    print()


async def test_detailed_shed_planning():
    """Test detailed shed construction planning."""

    print("=" * 80)
    print(" " * 20 + "STORAGE SHED CONSTRUCTION PROJECT")
    print("=" * 80)
    print()

    # Initialize General Contractor
    print("1. INITIALIZING GENERAL CONTRACTOR")
    print("-" * 80)
    gc = GeneralContractorAgent()
    print(f"   ✓ Initialized with {len(gc.agents)} specialized agents")
    print()

    # Show available agents and their capabilities
    print("2. AVAILABLE SPECIALIZED AGENTS")
    print("-" * 80)
    agent_status = gc.get_all_agents_status()
    for name, info in agent_status.items():
        print(f"   • {name:15} - {len(info['tools'])} tools")
        print(f"     Tools: {', '.join(info['tools'])}")
    print()

    # Define shed project
    print("3. PROJECT SPECIFICATIONS")
    print("-" * 80)
    print("   Customer Request:")
    print("   'I need a storage shed in my backyard for garden tools and equipment.'")
    print()
    print("   Specifications:")
    print("   • Dimensions: 10 ft x 12 ft x 8 ft (height)")
    print("   • Foundation: Concrete slab")
    print("   • Structure: Wood frame")
    print("   • Roof: Asphalt shingles")
    print("   • Door: 1 entry door")
    print("   • Windows: 1 window for ventilation")
    print("   • Electrical: 1 outlet + 1 overhead light")
    print("   • Finish: Exterior paint")
    print()

    # Start project planning
    print("4. PROJECT PLANNING")
    print("-" * 80)

    result = await gc.start_project(
        project_description="Build a 10x12 storage shed for garden tools and equipment",
        project_type="shed_construction",
        dimensions={"width": 10, "length": 12, "height": 8},
        has_foundation=True,
        has_electrical=True,
        has_plumbing=False,
    )

    print(f"   Status: {result['status'].upper()}")
    print(f"   Total Tasks: {result['total_tasks']}")
    print()

    # Get detailed task list
    all_tasks = gc.get_all_tasks()

    print("5. DETAILED TASK BREAKDOWN")
    print("-" * 80)
    print()

    # Group tasks by phase
    tasks_by_phase = {}
    for task in all_tasks:
        if task.phase not in tasks_by_phase:
            tasks_by_phase[task.phase] = []
        tasks_by_phase[task.phase].append(task)

    # Display tasks in phase order
    phase_order = [
        "planning",
        "foundation",
        "framing",
        "rough_in",
        "finishing",
        "final_inspection",
    ]

    for phase in phase_order:
        if phase in tasks_by_phase:
            print(f"   PHASE: {phase.upper()}")
            print(f"   {'-' * 76}")

            for task in tasks_by_phase[phase]:
                print(f"   Task #{task.task_id}")
                print(f"   Agent:        {task.agent}")
                print(f"   Description:  {task.description}")

                if task.dependencies:
                    print(f"   Dependencies: Task(s) {', '.join(task.dependencies)}")
                else:
                    print(f"   Dependencies: None (can start immediately)")

                if task.materials:
                    print(f"   Materials:    {', '.join(task.materials)}")

                if task.requirements:
                    req_str = ", ".join([f"{k}={v}" for k, v in task.requirements.items()])
                    print(f"   Requirements: {req_str}")

                print()

    # Show task dependencies visualization
    print("6. TASK DEPENDENCY FLOW")
    print("-" * 80)
    print()
    print("   Task 1 (Architect: Design)")
    print("       ↓")
    print("   Task 2 (Mason: Foundation)")
    print("       ↓")
    print("   Task 3 (Carpenter: Frame walls)")
    print("       ↓")
    print("   Task 4 (Carpenter: Roof trusses)")
    print("       ↓")
    print("   Task 5 (Roofer: Install roofing)")
    print("       ↓")
    print("   Task 6 (Electrician: Wiring) ──┐")
    print("       ↓                            │")
    print("   Task 7 (Carpenter: Siding) ←────┘")
    print("       ↓")
    print("   Task 8 (Carpenter: Door/Window)")
    print("       ↓")
    print("   Task 9 (Painter: Exterior paint)")
    print("       ↓")
    print("   Task 10 (Carpenter: Final walkthrough)")
    print()

    # Project statistics
    print("7. PROJECT STATISTICS")
    print("-" * 80)

    agent_workload = {}
    for task in all_tasks:
        agent_workload[task.agent] = agent_workload.get(task.agent, 0) + 1

    print("   Tasks per Agent:")
    for agent, count in sorted(agent_workload.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * count
        print(f"   {agent:15} {bar} {count}")

    print()
    print(f"   Total Project Tasks: {len(all_tasks)}")
    print(f"   Estimated Project Phases: {len(tasks_by_phase)}")
    print(f"   Agents Involved: {len(agent_workload)}")
    print()

    # Summary
    print("=" * 80)
    print("✅ SHED CONSTRUCTION PROJECT PLANNING COMPLETED")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("  • Review and approve the project plan")
    print("  • Configure AWS Bedrock model ID in .env")
    print("  • Run 'python test_shed_detailed.py execute' to execute with AI agents")
    print()


if __name__ == "__main__":
    print()
    if len(sys.argv) > 1 and sys.argv[1] in ["execute", "exec", "run", "full"]:
        print("=" * 80)
        print("🚀 EXECUTION MODE - AI agents will execute all tasks")
        print("=" * 80)
        print()
        print("⚠️  NOTE: Requires valid AWS Bedrock model ID in .env")
        print("   Current model: Check your .env file")
        print()
        input("Press ENTER to start execution (or Ctrl+C to cancel)...")
        print()
        asyncio.run(test_detailed_shed_execution())
    else:
        print("=" * 80)
        print("📋 PLANNING MODE - Showing task breakdown only")
        print("=" * 80)
        print()
        print("   Use 'python test_shed_detailed.py execute' for full AI execution")
        print()
        asyncio.run(test_detailed_shed_planning())
