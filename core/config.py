from __future__ import annotations

"""Application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    llm_provider: Literal["anthropic", "openai", "gemini", "ollama"] = "anthropic"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5-coder:1.5b"
    max_retries: int = 3
    render_timeout_seconds: int = 60
    render_quality: Literal["l", "m", "h"] = "l"
    docker_image_name: str = "text-to-manim-sandbox"
    output_dir: str = "./sandbox/volumes"
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: str = "1.0"
    sandbox_tmpfs_size: str = "512m"
    max_cached_job_dirs: int = 20
    job_retention_seconds: int = 600
    log_level: str = "INFO"

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_retries must be at least 1")
        return value

    @field_validator("render_timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value < 1:
            raise ValueError("render_timeout_seconds must be at least 1")
        return value

    @field_validator("max_cached_job_dirs")
    @classmethod
    def validate_max_cached_jobs(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_cached_job_dirs must be at least 1")
        return value

    @field_validator("job_retention_seconds")
    @classmethod
    def validate_job_retention(cls, value: int) -> int:
        if value < 1:
            raise ValueError("job_retention_seconds must be at least 1")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""

    return Settings()
