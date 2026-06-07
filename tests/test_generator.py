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


def test_generate_uses_template_pipeline_for_vector_addition(monkeypatch) -> None:
    strategy = AsyncMock()
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(generator.generate_manim_code("Show vector addition for vectors (2, 1) and (1, 3).", "anthropic"))

    assert "plane.c2p(3.0, 4.0)" in code
    assert strategy.complete.await_count == 0


def test_generate_uses_template_pipeline_for_matrix_multiplication(monkeypatch) -> None:
    strategy = AsyncMock()
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(
        generator.generate_manim_code(
            "Show matrix multiplication for [[1, 2], [3, 4]] times [[2], [1]].",
            "anthropic",
        )
    )

    assert "Matrix([[4], [10]])" in code
    assert strategy.complete.await_count == 0


def test_generate_uses_template_pipeline_for_gradient_descent(monkeypatch) -> None:
    strategy = AsyncMock()
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(
        generator.generate_manim_code(
            "Animate gradient descent moving downhill on a loss curve.",
            "anthropic",
        )
    )

    assert 'Text("Gradient descent"' in code
    assert "minimum = Dot" in code
    assert strategy.complete.await_count == 0


def test_generate_uses_template_pipeline_for_bst(monkeypatch) -> None:
    strategy = AsyncMock()
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(
        generator.generate_manim_code(
            "Show binary search tree insertion for values 8, 4, and 10.",
            "anthropic",
        )
    )

    assert 'root_text = Text("8"' in code
    assert 'left_text = Text("4"' in code
    assert 'right_text = Text("10"' in code
    assert strategy.complete.await_count == 0


def test_generate_falls_back_to_llm_for_generic_prompt(monkeypatch) -> None:
    strategy = AsyncMock()
    strategy.complete.return_value = "from manim import *\n\nclass GeneratedScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
    monkeypatch.setattr(generator, "get_provider_strategy", lambda provider: strategy)

    code = asyncio.run(
        generator.generate_manim_code(
            "Explain why hash tables have amortized O(1) lookup with a custom visual metaphor.",
            "anthropic",
            examples=[],
        )
    )

    assert code.startswith("from manim import *")
    assert strategy.complete.await_count == 1
