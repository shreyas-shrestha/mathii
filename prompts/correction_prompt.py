"""Prompt template for Manim correction retries."""

CORRECTION_PROMPT_TEMPLATE = """
The following Manim code failed to render. Fix the specific error shown in the traceback.

ORIGINAL CODE:
{code}

STDERR TRACEBACK:
{stderr}

Rules:
- Output ONLY the corrected raw Python code, no explanation
- The class must still be named GeneratedScene
- Fix only what the traceback indicates — do not rewrite the entire animation unless necessary
- from manim import * must remain the first line
""".strip()
