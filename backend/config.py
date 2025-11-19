"""
Configuration settings for the General Contractor Agent Demo.
"""

from pydantic_settings import BaseSettings
from typing import Optional


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

    # MCP Server configuration (reserved for future use)
    materials_mcp_url: Optional[str] = None
    permitting_mcp_url: Optional[str] = None

    # Project settings (reserved for future use)
    max_parallel_tasks: int = 3
    task_timeout_seconds: int = 300

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
