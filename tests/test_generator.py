from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from services import generator


def test_strip_markdown_removes_backticks() -> None:
    raw = "```python\nfrom manim import *\n```"
    assert generator.strip_markdown(raw) == "from manim import *"


def test_generate_returns_valid_python_string(monkeypatch) -> None:
    strategy = AsyncMock()
    strategy.complete.return_value = "```python\nfrom manim import *\n\nclass GeneratedScene(Scene):\n    def construct(self):\n        self.wait(1)\n```"
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(generator.generate_manim_code("Animate vector addition", "anthropic", examples=[]))

    assert isinstance(code, str)
    assert code.startswith("from manim import *")


def test_generated_code_contains_required_imports(monkeypatch) -> None:
    strategy = AsyncMock()
    strategy.complete.return_value = "class GeneratedScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(generator.generate_manim_code("Show a parabola", "anthropic", examples=[]))

    assert "from manim import *" in code


def test_generated_code_has_correct_class_name(monkeypatch) -> None:
    strategy = AsyncMock()
    strategy.complete.return_value = "from manim import *\n\nclass OtherScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(generator.generate_manim_code("Explain gcd", "anthropic", examples=[]))

    assert "class GeneratedScene(Scene):" in code


def test_configured_providers_includes_ollama(monkeypatch) -> None:
    monkeypatch.setattr(generator, "get_settings", lambda: type("Settings", (), {
        "anthropic_api_key": None,
        "openai_api_key": None,
        "gemini_api_key": None,
        "ollama_model": "qwen2.5-coder:1.5b",
        "ollama_base_url": "http://host.docker.internal:11434",
    })())

    assert "ollama" in generator.configured_providers()
