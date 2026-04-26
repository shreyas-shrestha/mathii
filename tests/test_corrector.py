from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from services import corrector
from services import renderer


def test_corrector_retries_on_failure(monkeypatch) -> None:
    monkeypatch.setattr(corrector, "generate_manim_code", AsyncMock(return_value="initial"))
    monkeypatch.setattr(corrector, "correct_manim_code", AsyncMock(side_effect=["fixed-1", "fixed-2"]))
    monkeypatch.setattr(
        corrector,
        "run_manim_in_sandbox",
        AsyncMock(side_effect=[
            (False, "", "first error", None),
            (False, "", "second error", None),
            (True, "", "", "/tmp/render/output/final.mp4"),
        ]),
    )

    result = asyncio.run(corrector.run_with_self_correction("Animate sorting", "anthropic", max_retries=3))

    assert result["success"] is True
    assert result["attempts"] == 3
    assert result["mp4_path"] == "/tmp/render/output/final.mp4"


def test_corrector_stops_after_max_retries(monkeypatch) -> None:
    monkeypatch.setattr(corrector, "generate_manim_code", AsyncMock(return_value="initial"))
    monkeypatch.setattr(corrector, "correct_manim_code", AsyncMock(return_value="fixed"))
    monkeypatch.setattr(
        corrector,
        "run_manim_in_sandbox",
        AsyncMock(return_value=(False, "", "persistent error", None)),
    )

    result = asyncio.run(corrector.run_with_self_correction("Animate a tree", "anthropic", max_retries=2))

    assert result["success"] is False
    assert result["attempts"] == 2
    assert "persistent error" in result["error"]


def test_corrector_returns_success_on_first_try(monkeypatch) -> None:
    monkeypatch.setattr(corrector, "generate_manim_code", AsyncMock(return_value="initial"))
    monkeypatch.setattr(corrector, "run_manim_in_sandbox", AsyncMock(return_value=(True, "", "", "/tmp/render/output/final.mp4")))

    result = asyncio.run(corrector.run_with_self_correction("Animate vectors", "anthropic", max_retries=3))

    assert result["success"] is True
    assert result["attempts"] == 1


def test_renderer_uses_job_directory_for_video_url(monkeypatch) -> None:
    monkeypatch.setattr(renderer, "get_settings", lambda: type("Settings", (), {
        "max_retries": 3,
        "output_dir": "/tmp/jobs",
    })())
    monkeypatch.setattr(renderer, "resolve_provider", lambda provider: provider or "gemini")
    monkeypatch.setattr(
        renderer,
        "run_with_self_correction",
        AsyncMock(
            return_value={
                "success": True,
                "code": "from manim import *",
                "mp4_path": "/tmp/jobs/abc123/output/videos/generated_script/480p15/GeneratedScene.mp4",
                "attempts": 1,
                "error": None,
            }
        ),
    )

    result = asyncio.run(renderer.render_prompt_to_video("Animate a dot", "gemini", quality="l"))

    assert result["job_id"] == "abc123"
    assert result["video_url"] == "/api/video/abc123"
