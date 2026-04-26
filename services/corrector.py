"""Self-correction loop for generated Manim code."""

from __future__ import annotations

from services.generator import correct_manim_code, generate_manim_code
from sandbox.runner import run_manim_in_sandbox


async def run_with_self_correction(
    prompt: str,
    provider: str,
    *,
    quality: str = "l",
    max_retries: int = 3,
    status_callback=None,
    attempt_callback=None,
) -> dict:
    """
    Orchestrate generate -> render -> correct retries.

    Returns a dictionary with success, code, attempts, error, and mp4_path.
    """

    if status_callback is not None:
        await status_callback("generating")

    code = await generate_manim_code(prompt, provider)
    last_stderr = ""

    for attempt in range(1, max_retries + 1):
        if attempt_callback is not None:
            await attempt_callback(attempt)
        if status_callback is not None:
            await status_callback("rendering")
        success, stdout, stderr, mp4_path = await run_manim_in_sandbox(code, quality=quality)
        last_stderr = stderr or stdout

        if success and mp4_path:
            return {
                "success": True,
                "code": code,
                "mp4_path": mp4_path,
                "attempts": attempt,
                "error": None,
            }

        if attempt < max_retries:
            if status_callback is not None:
                await status_callback("generating")
            code = await correct_manim_code(code, last_stderr, provider)

    return {
        "success": False,
        "code": code,
        "mp4_path": None,
        "attempts": max_retries,
        "error": f"Failed after {max_retries} attempts. Last error: {last_stderr[:500]}",
    }
