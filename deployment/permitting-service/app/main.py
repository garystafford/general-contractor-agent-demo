"""
Entry point for the Permitting Service MCP Server.

Runs the MCP server with streamable HTTP transport for ECS deployment.
"""

import logging
import os

from app.server import get_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))


def main():
    """Run the server."""
    logger.info(f"Starting Permitting Service MCP Server on {HOST}:{PORT}")
    logger.info("MCP endpoint: /mcp")
    logger.info("Health check: /health")

    # Get MCP server and run with streamable HTTP transport
    # Note: host and port are already set in the FastMCP constructor in server.py
    mcp = get_mcp_server()

    # Use FastMCP's native run method for streamable HTTP
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
