from __future__ import annotations

"""Pydantic models for API input and output."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000)
    quality: Literal["l", "m", "h"] = "l"
    provider: Optional[Literal["anthropic", "openai", "gemini", "ollama"]] = None


class GenerateResponse(BaseModel):
    success: bool
    video_url: Optional[str] = None
    manim_code: Optional[str] = None
    attempts: int
    error_message: Optional[str] = None
    render_time_seconds: float


class GenerateJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "generating", "rendering", "done", "failed"]


class StatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "generating", "rendering", "done", "failed"]
    success: bool = False
    attempts: int = 0
    video_url: Optional[str] = None
    manim_code: Optional[str] = None
    error_message: Optional[str] = None
    render_time_seconds: float = 0.0
