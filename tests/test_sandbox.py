from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from sandbox import runner


def test_runner_timeout_returns_failure(monkeypatch, tmp_path: Path) -> None:
    class HangingProcess:
        returncode = 0

        async def communicate(self):
            await asyncio.sleep(1)
            return b"", b""

    monkeypatch.setattr(runner, "get_settings", lambda: type("Settings", (), {
        "render_timeout_seconds": 0.01,
        "render_quality": "l",
        "docker_image_name": "text-to-manim-sandbox",
        "output_dir": str(tmp_path),
        "job_retention_seconds": 600,
        "max_cached_job_dirs": 20,
        "sandbox_memory_limit": "512m",
        "sandbox_cpu_limit": "1.0",
        "sandbox_tmpfs_size": "512m",
    })())
    monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock(return_value=HangingProcess()))

    success, _, stderr, mp4_path = asyncio.run(runner.run_manim_in_sandbox("from manim import *"))

    assert success is False
    assert "timed out" in stderr
    assert mp4_path is None


def test_runner_returns_mp4_path_on_success(tmp_path: Path, monkeypatch) -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker is not installed")

    image_check = subprocess.run(
        ["docker", "image", "inspect", "text-to-manim-sandbox"],
        capture_output=True,
        text=True,
        check=False,
    )
    if image_check.returncode != 0:
        pytest.skip("Sandbox image is not available")

    monkeypatch.setattr(runner, "get_settings", lambda: type("Settings", (), {
        "render_timeout_seconds": 60,
        "render_quality": "l",
        "docker_image_name": "text-to-manim-sandbox",
        "output_dir": str(tmp_path),
    })())

    code = """
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        dot = Dot()
        self.play(FadeIn(dot))
        self.wait(0.2)
""".strip()

    success, _, stderr, mp4_path = asyncio.run(runner.run_manim_in_sandbox(code))

    assert success is True, stderr
    assert mp4_path is not None
    assert mp4_path.endswith(".mp4")


def test_network_none_flag_present_in_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "get_settings", lambda: type("Settings", (), {
        "docker_image_name": "text-to-manim-sandbox",
        "sandbox_memory_limit": "512m",
        "sandbox_cpu_limit": "1.0",
        "sandbox_tmpfs_size": "512m",
    })())
    command = runner.build_docker_command(tmp_path, "l")

    assert "--network" in command
    assert "none" in command


def test_prune_job_dirs_removes_old_directories(tmp_path: Path, monkeypatch) -> None:
    old_dir = tmp_path / "old-job"
    new_dir = tmp_path / "new-job"
    old_dir.mkdir()
    new_dir.mkdir()

    old_timestamp = old_dir.stat().st_mtime - 3600
    new_timestamp = new_dir.stat().st_mtime
    old_dir.touch()
    new_dir.touch()
    import os
    os.utime(old_dir, (old_timestamp, old_timestamp))
    os.utime(new_dir, (new_timestamp, new_timestamp))

    monkeypatch.setattr(runner, "get_settings", lambda: type("Settings", (), {
        "output_dir": str(tmp_path),
        "job_retention_seconds": 10,
        "max_cached_job_dirs": 10,
    })())

    asyncio.run(runner.prune_job_dirs())

    assert not old_dir.exists()
    assert new_dir.exists()
