"""
Configuration settings for the General Contractor Agent Demo.
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Bedrock configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    aws_profile: Optional[str] = None

    # Model configuration (Bedrock model IDs)
    # Use regional inference profile format (e.g., us.anthropic.claude-sonnet-4-5-20250929-v1:0)
    default_model: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # MCP Server configuration
    # Paths to MCP server Python scripts (for stdio communication)
    materials_mcp_path: str = "backend/mcp_servers/materials_supplier.py"
    permitting_mcp_path: str = "backend/mcp_servers/permitting.py"

    # Python executable to use for MCP servers (defaults to current interpreter)
    mcp_python_executable: str = "python"

    # Project settings
    max_parallel_tasks: int = 3
    # Task timeout in seconds - agent execution will be terminated after this time
    # Recommended: 60 for testing to catch loops quickly, 300 for production
    # This is the PRIMARY protection against infinite loops
    task_timeout_seconds: int = 60

    # Loop Detection Settings
    # Maximum consecutive identical tool calls before failing the task
    max_consecutive_tool_calls: int = 3
    # Maximum total tool calls for a single task
    max_total_tool_calls: int = 20
    # Maximum identical calls with same parameters
    max_identical_calls: int = 2
    # Enable loop detection (if False, only timeout protection is used)
    enable_loop_detection: bool = True

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env (e.g., frontend settings)


settings = Settings()
