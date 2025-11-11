"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, or ollama",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL for local LLM",
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="Model name to use",
    )

    # Directory Paths
    input_dir: Path = Field(
        default=Path("temp/input"),
        description="Input directory for resume files",
    )
    output_dir: Path = Field(
        default=Path("temp/output"),
        description="Output directory for generated files",
    )
    cache_dir: Path = Field(
        default=Path("temp/cache"),
        description="Cache directory for metadata",
    )

    # Generation Settings
    tone: str = Field(
        default="balanced",
        description="Generation tone: conservative, balanced, or aggressive",
    )
    max_keywords_per_section: int = Field(
        default=3,
        description="Maximum keywords to add per section",
    )
    preserve_facts: bool = Field(
        default=True,
        description="Preserve original facts (no hallucination)",
    )

    # Language Settings
    default_language: Optional[str] = Field(
        default=None,
        description="Default language (None = auto-detect)",
    )

    # Cleanup Settings
    output_cleanup_hours: int = Field(
        default=24,
        description="Delete output files older than this many hours",
    )

    # Test Settings
    test_job_url: Optional[str] = Field(
        default=None,
        description="Test job posting URL (for integration tests)",
    )

    def __init__(self, **kwargs):
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

