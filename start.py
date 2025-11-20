#!/usr/bin/env python3
"""
Startup script for General Contractor Agent Demo.

This script manages the lifecycle of:
- MCP servers (materials supplier, permitting service)
- FastAPI backend server

Usage:
    python start.py
    python start.py --port 8000
    python start.py --host 0.0.0.0 --port 8000
"""

import argparse
import asyncio
import logging
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Note: MCP servers are now managed by the MCPClient in general_contractor.py
# They are launched on-demand via stdio when the client connects


class ApplicationManager:
    """Manager for the entire application lifecycle."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.api_process: Optional[subprocess.Popen] = None
        self.shutdown_event = asyncio.Event()

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_api_server(self, project_root: Path) -> None:
        """Start the FastAPI server."""
        logger.info(f"Starting FastAPI server on {self.host}:{self.port}...")

        try:
            # Use 'uv run' to ensure we use the correct Python environment
            self.api_process = subprocess.Popen(
                [
                    "uv",
                    "run",
                    "uvicorn",
                    "backend.api.routes:app",
                    "--host",
                    self.host,
                    "--port",
                    str(self.port),
                ],
                cwd=str(project_root),
                stdout=sys.stdout,
                stderr=sys.stderr,
            )

            logger.info(f"FastAPI server started (PID: {self.api_process.pid})")
            logger.info(f"API available at: http://{self.host}:{self.port}")
            logger.info(f"API docs available at: http://{self.host}:{self.port}/docs")

        except Exception as e:
            logger.error(f"Error starting FastAPI server: {e}")
            raise

    def stop_api_server(self) -> None:
        """Stop the FastAPI server."""
        if self.api_process and self.api_process.poll() is None:
            logger.info("Stopping FastAPI server...")
            self.api_process.terminate()

            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("FastAPI server did not terminate gracefully, killing...")
                self.api_process.kill()
                self.api_process.wait()

            logger.info("FastAPI server stopped")

    async def run(self) -> None:
        """Run the application."""
        project_root = Path.cwd()

        try:
            # Setup signal handlers
            self.setup_signal_handlers()

            logger.info("=" * 60)
            logger.info("Starting General Contractor Agent Demo")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Note: MCP servers will be started automatically by the")
            logger.info("General Contractor agent when needed (stdio mode)")
            logger.info("")

            # Start API server
            self.start_api_server(project_root)

            logger.info("=" * 60)
            logger.info("API server started successfully!")
            logger.info("=" * 60)

            # Monitor API server
            while not self.shutdown_event.is_set():
                await asyncio.sleep(5)

                # Check API server health
                if self.api_process and self.api_process.poll() is not None:
                    logger.error("API server has died, shutting down...")
                    break

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error during execution: {e}")
        finally:
            # Cleanup
            logger.info("=" * 60)
            logger.info("Shutting down...")
            logger.info("=" * 60)

            self.stop_api_server()

            logger.info("Shutdown complete")
            logger.info("Note: MCP server processes are managed by the General Contractor")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start the General Contractor Agent Demo with MCP servers"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the API server (default: 8000)",
    )
    args = parser.parse_args()

    # Create and run the application
    app_manager = ApplicationManager(host=args.host, port=args.port)

    try:
        asyncio.run(app_manager.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
