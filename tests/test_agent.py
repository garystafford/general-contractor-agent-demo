"""
Simple test script to verify Strands Agents with AWS Bedrock integration.
"""

import asyncio
from backend.agents import create_carpenter_agent


async def test_carpenter_agent():
    """Test the Carpenter agent with a simple task."""
    print("Initializing Carpenter agent with AWS Bedrock...")

    # Create the agent
    carpenter = create_carpenter_agent()

    print(f"Agent created: {carpenter.name if carpenter.name else 'Strands Agent'}")
    print(f"Available tools: {carpenter.tool_names}")

    # Test a simple task
    print("\nTesting frame_walls tool...")
    response = await carpenter.invoke_async(
        "Frame 4 walls, each 10 feet long, with 16 inch stud spacing"
    )

    print("\nAgent Response:")
    print(response)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Strands Agents with AWS Bedrock")
    print("=" * 60)
    print()

    try:
        asyncio.run(test_carpenter_agent())
        print("\n✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
