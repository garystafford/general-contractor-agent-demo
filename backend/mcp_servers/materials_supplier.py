"""
Building Materials Supplier MCP Server.

This MCP server provides tools for managing building materials inventory,
checking availability, ordering materials, and retrieving catalog information.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Pydantic models for input validation
class CheckAvailabilityInput(BaseModel):
    """Input for checking material availability."""

    material_ids: List[str] = Field(..., description="List of material IDs to check")


class OrderItem(BaseModel):
    """Single order item."""

    material_id: str = Field(..., description="Material ID to order")
    quantity: int = Field(..., gt=0, description="Quantity to order (must be positive)")


class OrderMaterialsInput(BaseModel):
    """Input for ordering materials."""

    orders: List[OrderItem] = Field(..., description="List of materials to order")


class GetCatalogInput(BaseModel):
    """Input for getting materials catalog."""

    category: Optional[str] = Field(None, description="Category to filter by (optional)")


class GetOrderInput(BaseModel):
    """Input for retrieving order details."""

    order_id: str = Field(..., description="Order ID to retrieve")


class BuildingMaterialsSupplier:
    """Service for building materials supply and ordering."""

    def __init__(self):
        self.inventory = self._initialize_inventory()
        self.orders = {}
        self.order_counter = 0
        logger.info("Building Materials Supplier initialized")

    def _initialize_inventory(self) -> Dict[str, Dict[str, Any]]:
        """Initialize material inventory with prices and availability."""
        return {
            # Lumber
            "2x4_studs": {
                "name": "2x4 Studs",
                "category": "lumber",
                "price": 5.99,
                "unit": "each",
                "stock": 1000,
            },
            "plywood_sheets": {
                "name": "Plywood Sheets",
                "category": "lumber",
                "price": 45.99,
                "unit": "sheet",
                "stock": 500,
            },
            # Electrical
            "electrical_wire": {
                "name": "Electrical Wire",
                "category": "electrical",
                "price": 89.99,
                "unit": "250ft roll",
                "stock": 100,
            },
            "outlets": {
                "name": "Electrical Outlets",
                "category": "electrical",
                "price": 2.99,
                "unit": "each",
                "stock": 500,
            },
            "light_fixtures": {
                "name": "Light Fixtures",
                "category": "electrical",
                "price": 49.99,
                "unit": "each",
                "stock": 200,
            },
            # Plumbing
            "pvc_pipes": {
                "name": "PVC Pipes",
                "category": "plumbing",
                "price": 12.99,
                "unit": "10ft",
                "stock": 300,
            },
            "copper_pipes": {
                "name": "Copper Pipes",
                "category": "plumbing",
                "price": 35.99,
                "unit": "10ft",
                "stock": 200,
            },
            "sink": {
                "name": "Kitchen Sink",
                "category": "plumbing",
                "price": 299.99,
                "unit": "each",
                "stock": 50,
            },
            # Masonry
            "concrete_bags": {
                "name": "Concrete Mix",
                "category": "masonry",
                "price": 8.99,
                "unit": "80lb bag",
                "stock": 500,
            },
            "bricks": {
                "name": "Red Bricks",
                "category": "masonry",
                "price": 0.89,
                "unit": "each",
                "stock": 10000,
            },
            # Paint
            "interior_paint": {
                "name": "Interior Paint",
                "category": "paint",
                "price": 34.99,
                "unit": "gallon",
                "stock": 200,
            },
            "primer": {
                "name": "Primer",
                "category": "paint",
                "price": 24.99,
                "unit": "gallon",
                "stock": 150,
            },
            # HVAC
            "hvac_unit": {
                "name": "Central AC Unit",
                "category": "hvac",
                "price": 2499.99,
                "unit": "each",
                "stock": 10,
            },
            "ductwork": {
                "name": "HVAC Ductwork",
                "category": "hvac",
                "price": 8.99,
                "unit": "per foot",
                "stock": 1000,
            },
            # Roofing
            "shingles": {
                "name": "Asphalt Shingles",
                "category": "roofing",
                "price": 89.99,
                "unit": "bundle",
                "stock": 300,
            },
            "underlayment": {
                "name": "Roof Underlayment",
                "category": "roofing",
                "price": 45.99,
                "unit": "roll",
                "stock": 100,
            },
        }

    def check_availability(self, material_ids: List[str]) -> Dict[str, Any]:
        """Check if materials are available in inventory."""
        results = {}
        for material_id in material_ids:
            if material_id in self.inventory:
                material = self.inventory[material_id]
                results[material_id] = {
                    "available": material["stock"] > 0,
                    "stock": material["stock"],
                    "price": material["price"],
                    "unit": material["unit"],
                    "name": material["name"],
                }
            else:
                results[material_id] = {
                    "available": False,
                    "error": "Material not found",
                }

        return results

    def order_materials(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Order materials from supplier.

        Args:
            orders: List of dicts with 'material_id' and 'quantity'

        Returns:
            Order confirmation dictionary
        """
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter}"

        total_cost = 0.0
        order_items = []

        for order in orders:
            material_id = order["material_id"]
            quantity = order["quantity"]

            if material_id in self.inventory:
                material = self.inventory[material_id]
                if material["stock"] >= quantity:
                    cost = material["price"] * quantity
                    total_cost += cost
                    material["stock"] -= quantity

                    order_items.append(
                        {
                            "material_id": material_id,
                            "material": material["name"],
                            "quantity": quantity,
                            "unit": material["unit"],
                            "unit_price": material["price"],
                            "total_cost": cost,
                        }
                    )
                else:
                    return {
                        "status": "failed",
                        "error": f"Insufficient stock for {material['name']}",
                    }
            else:
                return {
                    "status": "failed",
                    "error": f"Material {material_id} not found",
                }

        # Store order
        self.orders[order_id] = {
            "order_id": order_id,
            "items": order_items,
            "total_cost": total_cost,
            "status": "confirmed",
        }

        logger.info(f"Order {order_id} placed: ${total_cost:.2f}")

        return {
            "status": "success",
            "order_id": order_id,
            "items": order_items,
            "total_cost": total_cost,
            "estimated_delivery": "2-3 business days",
        }

    def get_catalog(self, category: str = None) -> Dict[str, Any]:
        """Get catalog of available materials, optionally filtered by category."""
        if category:
            catalog = {k: v for k, v in self.inventory.items() if v["category"] == category}
        else:
            catalog = self.inventory

        categories = list(set(m["category"] for m in self.inventory.values()))

        return {"catalog": catalog, "categories": categories}

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details by ID."""
        if order_id in self.orders:
            return self.orders[order_id]
        else:
            return {"error": "Order not found"}


# Initialize the supplier service
supplier = BuildingMaterialsSupplier()

# Create MCP server
server = Server("building-materials-supplier")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="check_availability",
            description="Check availability, pricing, and stock levels for building materials",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of material IDs to check (e.g., '2x4_studs', "
                        "'plywood_sheets', 'electrical_wire')",
                    }
                },
                "required": ["material_ids"],
            },
        ),
        Tool(
            name="order_materials",
            description="Place an order for building materials. Returns order confirmation with "
            "total cost and estimated delivery",
            inputSchema={
                "type": "object",
                "properties": {
                    "orders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "material_id": {
                                    "type": "string",
                                    "description": "Material ID to order",
                                },
                                "quantity": {
                                    "type": "integer",
                                    "description": "Quantity to order",
                                    "minimum": 1,
                                },
                            },
                            "required": ["material_id", "quantity"],
                        },
                        "description": "List of materials to order with quantities",
                    }
                },
                "required": ["orders"],
            },
        ),
        Tool(
            name="get_catalog",
            description="Retrieve the materials catalog, optionally filtered by category. "
            "Categories include: lumber, electrical, plumbing, masonry, paint, hvac, roofing",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter by (lumber, electrical, "
                        "plumbing, masonry, paint, hvac, roofing)",
                    }
                },
            },
        ),
        Tool(
            name="get_order",
            description="Retrieve details of a previous order by order ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to retrieve (e.g., 'ORDER_1')",
                    }
                },
                "required": ["order_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "check_availability":
            validated_input = CheckAvailabilityInput(**arguments)
            result = supplier.check_availability(validated_input.material_ids)
            return [TextContent(type="text", text=str(result))]

        elif name == "order_materials":
            validated_input = OrderMaterialsInput(**arguments)
            orders_dict = [order.model_dump() for order in validated_input.orders]
            result = supplier.order_materials(orders_dict)
            return [TextContent(type="text", text=str(result))]

        elif name == "get_catalog":
            validated_input = GetCatalogInput(**arguments)
            result = supplier.get_catalog(validated_input.category)
            return [TextContent(type="text", text=str(result))]

        elif name == "get_order":
            validated_input = GetOrderInput(**arguments)
            result = supplier.get_order(validated_input.order_id)
            return [TextContent(type="text", text=str(result))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error in tool '{name}': {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Building Materials Supplier MCP server starting...")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
