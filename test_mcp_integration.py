#!/usr/bin/env python3
"""
Test script for MCP integration with General Contractor Agent.

This script tests the MCP servers and their integration with the General Contractor.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.agents.general_contractor import GeneralContractorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_materials_mcp():
    """Test Materials Supplier MCP server."""
    logger.info("=" * 60)
    logger.info("Testing Materials Supplier MCP Server")
    logger.info("=" * 60)

    contractor = GeneralContractorAgent()

    try:
        # Initialize MCP clients
        await contractor.initialize_mcp_clients()
        logger.info("✓ MCP clients initialized")

        # Test 1: Get catalog
        logger.info("\n[Test 1] Getting materials catalog...")
        catalog = await contractor.get_materials_catalog()
        logger.info(f"✓ Retrieved catalog with {len(catalog.get('catalog', {}))} items")

        # Test 2: Get catalog by category
        logger.info("\n[Test 2] Getting lumber catalog...")
        lumber_catalog = await contractor.get_materials_catalog(category="lumber")
        logger.info(f"✓ Retrieved {len(lumber_catalog.get('catalog', {}))} lumber items")

        # Test 3: Check availability
        logger.info("\n[Test 3] Checking availability of materials...")
        availability = await contractor.check_materials_availability(
            ["2x4_studs", "plywood_sheets", "electrical_wire"]
        )
        logger.info(f"✓ Checked availability: {availability}")

        # Test 4: Order materials
        logger.info("\n[Test 4] Ordering materials...")
        order_result = await contractor.order_materials(
            [
                {"material_id": "2x4_studs", "quantity": 50},
                {"material_id": "plywood_sheets", "quantity": 20},
            ]
        )
        logger.info(f"✓ Order placed: {order_result.get('order_id')}")
        logger.info(f"  Total cost: ${order_result.get('total_cost', 0):.2f}")

        logger.info("\n✅ All Materials Supplier tests passed!")

    except Exception as e:
        logger.error(f"❌ Materials Supplier test failed: {e}")
        raise
    finally:
        await contractor.close_mcp_clients()


async def test_permitting_mcp():
    """Test Permitting Service MCP server."""
    logger.info("=" * 60)
    logger.info("Testing Permitting Service MCP Server")
    logger.info("=" * 60)

    contractor = GeneralContractorAgent()

    try:
        # Initialize MCP clients
        await contractor.initialize_mcp_clients()
        logger.info("✓ MCP clients initialized")

        # Test 1: Get required permits
        logger.info("\n[Test 1] Getting required permits for a project...")
        required = await contractor.get_required_permits(
            project_type="new_construction",
            work_items=["foundation", "framing", "electrical", "plumbing", "roofing"],
        )
        logger.info(f"✓ Required permits: {required.get('required_permits')}")
        logger.info(f"  Estimated fees: ${required.get('estimated_total_fees'):.2f}")

        # Test 2: Apply for permit
        logger.info("\n[Test 2] Applying for building permit...")
        permit_result = await contractor.apply_for_permit(
            permit_type="building",
            project_address="123 Test St, Test City, TS 12345",
            project_description="New residential construction",
            applicant="Test Contractor LLC",
        )
        permit_id = permit_result.get("permit", {}).get("permit_id")
        logger.info(f"✓ Permit applied: {permit_id}")
        logger.info(
            f"  Estimated approval: {permit_result.get('permit', {}).get('estimated_approval')}"
        )

        # Test 3: Check permit status
        logger.info("\n[Test 3] Checking permit status...")
        status = await contractor.check_permit_status(permit_id)
        logger.info(f"✓ Permit status: {status.get('permit', {}).get('status')}")

        # Test 4: Schedule inspection
        logger.info("\n[Test 4] Scheduling inspection...")
        inspection_result = await contractor.schedule_inspection(
            permit_id=permit_id, inspection_type="framing"
        )
        inspection_id = inspection_result.get("inspection", {}).get("inspection_id")
        logger.info(f"✓ Inspection scheduled: {inspection_id}")
        logger.info(
            f"  Scheduled date: {inspection_result.get('inspection', {}).get('scheduled_date')}"
        )

        logger.info("\n✅ All Permitting Service tests passed!")

    except Exception as e:
        logger.error(f"❌ Permitting Service test failed: {e}")
        raise
    finally:
        await contractor.close_mcp_clients()


async def test_full_integration():
    """Test full integration - combining both MCP services."""
    logger.info("=" * 60)
    logger.info("Testing Full MCP Integration")
    logger.info("=" * 60)

    contractor = GeneralContractorAgent()

    try:
        # Initialize MCP clients
        await contractor.initialize_mcp_clients()
        logger.info("✓ MCP clients initialized")

        # Scenario: New shed construction project
        logger.info("\n[Scenario] Building a shed - coordinating permits and materials")

        # Step 1: Check required permits
        logger.info("\n[Step 1] Determining required permits...")
        required = await contractor.get_required_permits(
            project_type="new_construction", work_items=["foundation", "framing", "roofing"]
        )
        logger.info(f"✓ Need permits: {required.get('required_permits')}")

        # Step 2: Apply for building permit
        logger.info("\n[Step 2] Applying for building permit...")
        permit_result = await contractor.apply_for_permit(
            permit_type="building",
            project_address="456 Backyard Ave, Suburbia, ST 54321",
            project_description="10x12 storage shed construction",
            applicant="DIY Builder",
        )
        permit_id = permit_result.get("permit", {}).get("permit_id")
        logger.info(f"✓ Permit obtained: {permit_id}")

        # Step 3: Check materials availability
        logger.info("\n[Step 3] Checking materials availability...")
        materials_needed = [
            "2x4_studs",
            "plywood_sheets",
            "concrete_bags",
            "shingles",
            "underlayment",
        ]
        availability = await contractor.check_materials_availability(materials_needed)
        all_available = all(item.get("available", False) for item in availability.values())
        logger.info(f"✓ All materials available: {all_available}")

        # Step 4: Order materials
        logger.info("\n[Step 4] Ordering materials...")
        order_result = await contractor.order_materials(
            [
                {"material_id": "2x4_studs", "quantity": 100},
                {"material_id": "plywood_sheets", "quantity": 15},
                {"material_id": "concrete_bags", "quantity": 20},
                {"material_id": "shingles", "quantity": 5},
                {"material_id": "underlayment", "quantity": 2},
            ]
        )
        logger.info(f"✓ Materials ordered: {order_result.get('order_id')}")
        logger.info(f"  Total cost: ${order_result.get('total_cost', 0):.2f}")
        logger.info(f"  Estimated delivery: {order_result.get('estimated_delivery')}")

        # Step 5: Schedule framing inspection
        logger.info("\n[Step 5] Scheduling framing inspection...")
        inspection_result = await contractor.schedule_inspection(
            permit_id=permit_id, inspection_type="framing"
        )
        logger.info(
            f"✓ Inspection scheduled: {inspection_result.get('inspection', {}).get('inspection_id')}"
        )

        logger.info("\n✅ Full integration test completed successfully!")
        logger.info(
            "\nSummary: Successfully coordinated permits and materials for shed construction"
        )

    except Exception as e:
        logger.error(f"❌ Full integration test failed: {e}")
        raise
    finally:
        await contractor.close_mcp_clients()


async def main():
    """Run all tests."""
    logger.info("Starting MCP Integration Tests")
    logger.info("=" * 60)

    try:
        # Test Materials Supplier
        await test_materials_mcp()
        await asyncio.sleep(1)

        # Test Permitting Service
        await test_permitting_mcp()
        await asyncio.sleep(1)

        # Test Full Integration
        await test_full_integration()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ Tests failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
