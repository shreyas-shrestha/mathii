"""FastAPI router definitions."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from api.models import GenerateJobResponse, GenerateRequest, GenerateResponse, StatusResponse
from core.config import get_settings
from sandbox.runner import docker_available, remove_job_dir
from services.generator import configured_providers, resolve_provider
from services.renderer import render_prompt_to_video

router = APIRouter()


@dataclass
class JobRecord:
    job_id: str
    status: str = "queued"
    success: bool = False
    attempts: int = 0
    video_url: str | None = None
    manim_code: str | None = None
    error_message: str | None = None
    render_time_seconds: float = 0.0
    task: asyncio.Task | None = field(default=None, repr=False)


JOB_STORE: dict[str, JobRecord] = {}


async def _cleanup_job_later(job_id: str, delay_seconds: int = 600) -> None:
    await asyncio.sleep(delay_seconds)
    settings = get_settings()
    await remove_job_dir(Path(settings.output_dir) / job_id)
    JOB_STORE.pop(job_id, None)


async def _run_job(job_id: str, request: GenerateRequest) -> None:
    record = JOB_STORE[job_id]

    async def status_callback(status: str) -> None:
        record.status = status

    async def attempt_callback(attempt: int) -> None:
        record.attempts = attempt

    try:
        result = await render_prompt_to_video(
            request.prompt,
            request.provider,
            quality=request.quality,
            status_callback=status_callback,
            attempt_callback=attempt_callback,
        )
        record.status = "done" if result["success"] else "failed"
        record.success = result["success"]
        record.attempts = result["attempts"]
        record.video_url = result["video_url"]
        record.manim_code = result["manim_code"]
        record.error_message = result["error_message"]
        record.render_time_seconds = result["render_time_seconds"]
    except Exception as exc:  # pragma: no cover - defensive job guard
        record.status = "failed"
        record.error_message = str(exc)
    finally:
        if not record.success:
            asyncio.create_task(_cleanup_job_later(job_id, delay_seconds=min(get_settings().job_retention_seconds, 60)))


@router.get("/health")
async def healthcheck() -> dict[str, bool | str]:
    return {"status": "ok", "docker": await docker_available()}


@router.get("/providers")
async def providers() -> dict[str, list[str]]:
    return {"providers": configured_providers()}


@router.post("/generate", response_model=GenerateResponse)
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks) -> GenerateResponse:
    try:
        result = await render_prompt_to_video(
            request.prompt,
            request.provider,
            quality=request.quality,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result["job_id"]:
        background_tasks.add_task(_cleanup_job_later, result["job_id"], get_settings().job_retention_seconds)

    return GenerateResponse(
        success=result["success"],
        video_url=result["video_url"],
        manim_code=result["manim_code"],
        attempts=result["attempts"],
        error_message=result["error_message"],
        render_time_seconds=result["render_time_seconds"],
    )


@router.post("/generate-async", response_model=GenerateJobResponse)
async def generate_video_async(request: GenerateRequest) -> GenerateJobResponse:
    try:
        resolve_provider(request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job_id = uuid.uuid4().hex
    record = JobRecord(job_id=job_id)
    JOB_STORE[job_id] = record
    record.task = asyncio.create_task(_run_job(job_id, request))
    return GenerateJobResponse(job_id=job_id, status=record.status)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    record = JOB_STORE.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return StatusResponse(
        job_id=record.job_id,
        status=record.status,
        success=record.success,
        attempts=record.attempts,
        video_url=record.video_url,
        manim_code=record.manim_code,
        error_message=record.error_message,
        render_time_seconds=record.render_time_seconds,
    )


@router.get("/video/{job_id}")
async def get_video(job_id: str, background_tasks: BackgroundTasks) -> FileResponse:
    settings = get_settings()
    job_dir = Path(settings.output_dir) / job_id
    mp4_files = await asyncio.to_thread(lambda: list((job_dir / "output").rglob("*.mp4")))
    if not mp4_files:
        raise HTTPException(status_code=404, detail="Video not found")

    background_tasks.add_task(remove_job_dir, job_dir)
    JOB_STORE.pop(job_id, None)
    return FileResponse(path=mp4_files[0], media_type="video/mp4", filename=f"{job_id}.mp4")
