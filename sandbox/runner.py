"""Utilities for executing generated Manim code inside Docker."""

from __future__ import annotations

import asyncio
import time
import shutil
import uuid
from pathlib import Path

from core.config import get_settings


def build_docker_command(job_dir: Path, quality: str) -> list[str]:
    """Build the Docker command used to run Manim safely."""

    settings = get_settings()
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        settings.sandbox_memory_limit,
        "--cpus",
        settings.sandbox_cpu_limit,
        "--pids-limit",
        "256",
        "--tmpfs",
        f"/tmp:rw,noexec,nosuid,size={settings.sandbox_tmpfs_size}",
        "-v",
        f"{job_dir.resolve()}:/manim",
        settings.docker_image_name,
        "generated_script.py",
        "GeneratedScene",
        f"-q{quality}",
        "--media_dir",
        "/manim/output",
    ]


async def _write_script(script_path: Path, code: str) -> None:
    await asyncio.to_thread(script_path.write_text, code, "utf-8")


async def remove_job_dir(job_dir: Path) -> None:
    """Delete a render job directory if it exists."""

    if job_dir.exists():
        await asyncio.to_thread(shutil.rmtree, job_dir, True)


def _list_job_dirs(base_output_dir: Path) -> list[Path]:
    return [path for path in base_output_dir.iterdir() if path.is_dir()]


async def prune_job_dirs() -> None:
    """Delete stale or excess job directories to bound storage usage."""

    settings = get_settings()
    base_output_dir = Path(settings.output_dir)
    await asyncio.to_thread(base_output_dir.mkdir, parents=True, exist_ok=True)
    now = time.time()
    job_dirs = await asyncio.to_thread(_list_job_dirs, base_output_dir)

    stale_jobs = []
    for job_dir in job_dirs:
        try:
            modified_at = job_dir.stat().st_mtime
        except FileNotFoundError:
            continue
        if now - modified_at > settings.job_retention_seconds:
            stale_jobs.append(job_dir)

    for job_dir in stale_jobs:
        await remove_job_dir(job_dir)

    remaining = await asyncio.to_thread(_list_job_dirs, base_output_dir)
    if len(remaining) <= settings.max_cached_job_dirs:
        return

    remaining.sort(key=lambda path: path.stat().st_mtime)
    excess = len(remaining) - settings.max_cached_job_dirs
    for job_dir in remaining[:excess]:
        await remove_job_dir(job_dir)


async def run_manim_in_sandbox(code: str, quality: str | None = None) -> tuple[bool, str, str, str | None]:
    """
    Execute Manim code inside a Docker container.

    Returns:
        (success, stdout, stderr, output_mp4_path)
    """

    settings = get_settings()
    selected_quality = quality or settings.render_quality
    job_id = uuid.uuid4().hex
    base_output_dir = Path(settings.output_dir)
    await prune_job_dirs()
    job_dir = base_output_dir / job_id
    await asyncio.to_thread(job_dir.mkdir, parents=True, exist_ok=True)

    script_path = job_dir / "generated_script.py"
    await _write_script(script_path, code)
    cmd = build_docker_command(job_dir, selected_quality)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.render_timeout_seconds,
        )
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        success = proc.returncode == 0

        mp4_path = None
        if success:
            output_dir = job_dir / "output"
            mp4_files = await asyncio.to_thread(lambda: list(output_dir.rglob("*.mp4")))
            if mp4_files:
                mp4_path = str(mp4_files[0])
            else:
                await remove_job_dir(job_dir)
        else:
            await remove_job_dir(job_dir)

        return success, stdout, stderr, mp4_path
    except asyncio.TimeoutError:
        await remove_job_dir(job_dir)
        return (
            False,
            "",
            f"Execution timed out after {settings.render_timeout_seconds}s",
            None,
        )
    except Exception as exc:  # pragma: no cover - defensive surface
        await remove_job_dir(job_dir)
        return False, "", str(exc), None


async def docker_available() -> bool:
    """Check whether Docker is installed and reachable."""

    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()
        return proc.returncode == 0
    except FileNotFoundError:
        return False
