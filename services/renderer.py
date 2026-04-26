"""High-level rendering orchestration helpers."""

from __future__ import annotations

import time
from pathlib import Path

from core.config import get_settings
from services.corrector import run_with_self_correction
from services.generator import resolve_provider


async def render_prompt_to_video(
    prompt: str,
    provider: str | None,
    *,
    quality: str,
    status_callback=None,
    attempt_callback=None,
) -> dict:
    """Render a prompt into a video and return response-ready metadata."""

    settings = get_settings()
    selected_provider = resolve_provider(provider)

    started = time.perf_counter()

    result = await run_with_self_correction(
        prompt,
        selected_provider,
        quality=quality,
        max_retries=settings.max_retries,
        status_callback=status_callback,
        attempt_callback=attempt_callback,
    )
    elapsed = time.perf_counter() - started

    video_url = None
    job_id = None
    if result["success"] and result["mp4_path"]:
        mp4_path = Path(result["mp4_path"]).resolve()
        output_dir = Path(settings.output_dir).resolve()
        try:
            job_id = mp4_path.relative_to(output_dir).parts[0]
        except ValueError:
            job_id = mp4_path.parents[4].name if len(mp4_path.parents) >= 5 else mp4_path.parent.name
        video_url = f"/api/video/{job_id}"

    if status_callback is not None:
        await status_callback("done" if result["success"] else "failed")

    return {
        "success": result["success"],
        "video_url": video_url,
        "manim_code": result["code"],
        "attempts": result["attempts"],
        "error_message": result["error"],
        "render_time_seconds": round(elapsed, 3),
        "provider": selected_provider,
        "job_id": job_id,
    }
