"""
Main entry point for the General Contractor Agent Demo application.
Starts the FastAPI server using Uvicorn.

Usage: 
    uv run main.py

Author: Gary Stafford
Date: 2025-11-23
"""

import uvicorn

from backend.config import settings


def main():
    """Run the FastAPI application."""
    uvicorn.run(
        "backend.api.routes:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Enable auto-reload during development
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
