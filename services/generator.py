"""LLM-backed Manim code generation."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

import httpx

from core.config import get_settings
from prompts.correction_prompt import CORRECTION_PROMPT_TEMPLATE
from prompts.examples import get_examples
from prompts.system_prompt import SYSTEM_PROMPT
from services.planner import SceneSpec, plan_scene, scene_spec_to_prompt


def strip_markdown(code: str) -> str:
    """Remove common markdown fencing from model responses."""

    stripped = re.sub(r"^```python\s*", "", code.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"^```\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"```$", "", stripped).strip()
    return stripped


def ensure_required_structure(code: str) -> str:
    """Normalize generator output to the required import and class name."""

    normalized = strip_markdown(code)
    if "class GeneratedScene(Scene):" not in normalized:
        normalized += "\n\nclass GeneratedScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
    if not normalized.startswith("from manim import *"):
        normalized = f"from manim import *\n\n{normalized}"
    return normalized.strip()


def render_scene_spec(spec: SceneSpec) -> str | None:
    """Compile supported scene specs into deterministic Manim code."""

    if spec.render_strategy != "template":
        return None

    if spec.concept_type == "vector_addition":
        vectors = {obj.name: obj.properties for obj in spec.objects}
        a_end = vectors["a"]["end"]
        b_end = vectors["b"]["end"]
        sum_end = vectors["sum"]["end"]
        return ensure_required_structure(
            f"""
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1, 5, 1], y_range=[-1, 5, 1], background_line_style={{"stroke_opacity": 0.35}})
        title = Text("{spec.title}", font_size=30).to_edge(UP)
        vector_a = Arrow(plane.c2p(0, 0), plane.c2p({a_end[0]}, {a_end[1]}), buff=0, color=BLUE)
        vector_b = Arrow(plane.c2p({a_end[0]}, {a_end[1]}), plane.c2p({b_end[0]}, {b_end[1]}), buff=0, color=GREEN)
        vector_sum = Arrow(plane.c2p(0, 0), plane.c2p({sum_end[0]}, {sum_end[1]}), buff=0, color=YELLOW)
        label_a = MathTex("a").next_to(vector_a.get_center(), LEFT, buff=0.15)
        label_b = MathTex("b").next_to(vector_b.get_center(), RIGHT, buff=0.15)
        label_sum = MathTex("a+b").next_to(vector_sum.get_center(), UP, buff=0.15)
        self.play(Create(plane), Write(title))
        self.play(GrowArrow(vector_a), FadeIn(label_a))
        self.play(GrowArrow(vector_b), FadeIn(label_b))
        self.play(GrowArrow(vector_sum), FadeIn(label_sum))
        self.play(Indicate(vector_sum, color=YELLOW))
        self.wait(1)
"""
        )

    if spec.concept_type == "function_plot":
        curve = spec.objects[0].properties
        if curve["family"] == "sine":
            plot_expression = "lambda x: np.sin(x)"
        else:
            plot_expression = f"lambda x: {curve['scale']} * (x**2)"
        return ensure_required_structure(
            f"""
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[{curve['x_range'][0]}, {curve['x_range'][1]}, 1],
            y_range=[{curve['y_range'][0]}, {curve['y_range'][1]}, 1],
            x_length=6,
            y_length=3.5,
        )
        graph = axes.plot({plot_expression}, x_range=[{curve['x_range'][0]}, {curve['x_range'][1]}], color={curve['color']})
        equation = MathTex(r"{curve['equation']}").to_edge(UP)
        self.play(Create(axes))
        self.play(Create(graph), Write(equation))
        self.wait(1)
"""
        )

    if spec.concept_type == "euclidean_algorithm":
        step_lines = ",\n            ".join(f'MathTex(r"{step}")' for step in spec.annotations)
        return ensure_required_structure(
            f"""
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        steps = VGroup(
            {step_lines}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        for index, step in enumerate(steps):
            if index == len(steps) - 1:
                self.play(step.animate.set_color(GREEN), Write(step))
            else:
                self.play(Write(step))
        self.wait(1)
"""
        )

    if spec.concept_type == "matrix_multiplication":
        matrices = {obj.name: obj.properties["values"] for obj in spec.objects if obj.kind == "matrix"}
        left = matrices["left"]
        right = matrices["right"]
        result = matrices["result"]
        return ensure_required_structure(
            f"""
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        left = Matrix({left})
        right = Matrix({right})
        equals = MathTex("=")
        result = Matrix({result})
        row_highlight = SurroundingRectangle(left.get_rows()[0], color=YELLOW, buff=0.05)
        col_highlight = SurroundingRectangle(right.get_columns()[0], color=GREEN, buff=0.05)
        group = VGroup(left, right, equals, result).arrange(RIGHT, buff=0.45)
        self.play(Write(group))
        self.play(Create(row_highlight), Create(col_highlight))
        self.play(Indicate(result.get_entries()[0], color=BLUE))
        self.wait(1)
"""
        )

    if spec.concept_type == "gradient_descent":
        curve = next(obj.properties for obj in spec.objects if obj.name == "loss")
        points = spec.metadata["points"]
        minimum = spec.metadata["minimum"]
        return ensure_required_structure(
            f"""
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        axes = Axes(x_range=[-3, 3, 1], y_range=[0, 5, 1], x_length=6, y_length=3.5)
        curve = axes.plot(lambda x: {curve['a']} * ((x - {curve['h']}) ** 2) + {curve['k']}, x_range=[-2.5, 2.5], color=BLUE)
        dot = Dot(axes.c2p({points[0][0]}, {points[0][1]}), color=YELLOW)
        minimum = Dot(axes.c2p({minimum[0]}, {minimum[1]}), color=GREEN)
        trail = TracedPath(dot.get_center, stroke_color=YELLOW)
        label = Text("Gradient descent", font_size=32).to_edge(UP)
        self.play(Create(axes), Create(curve), FadeIn(dot), Write(label))
        self.add(trail)
        self.play(dot.animate.move_to(axes.c2p({points[1][0]}, {points[1][1]})), run_time=0.9)
        self.play(dot.animate.move_to(axes.c2p({points[2][0]}, {points[2][1]})), run_time=0.9)
        self.play(dot.animate.move_to(axes.c2p({points[3][0]}, {points[3][1]})), run_time=0.9)
        self.play(FadeIn(minimum), Indicate(minimum, color=GREEN))
        self.wait(1)
"""
        )

    if spec.concept_type == "bst_insertion":
        nodes = {obj.name: obj.properties for obj in spec.objects if obj.kind == "node"}
        root = nodes["root"]
        left = nodes["left"]
        right = nodes["right"]
        return ensure_required_structure(
            f"""
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        root_circle = Circle(radius=0.35).set_stroke(BLUE, 2).move_to(UP * 1.2)
        left_circle = Circle(radius=0.35).set_stroke(BLUE, 2).move_to(LEFT * 2 + DOWN * 0.3)
        right_circle = Circle(radius=0.35).set_stroke(BLUE, 2).move_to(RIGHT * 2 + DOWN * 0.3)
        root_text = Text("{root['value']}", font_size=28).move_to(root_circle)
        left_text = Text("{left['value']}", font_size=28).move_to(left_circle)
        right_text = Text("{right['value']}", font_size=28).move_to(right_circle)
        left_edge = Line(root_circle.get_bottom(), left_circle.get_top())
        right_edge = Line(root_circle.get_bottom(), right_circle.get_top())
        title = Text("{spec.title}", font_size=30).to_edge(UP)
        self.play(Write(title), Create(root_circle), Write(root_text))
        self.play(Create(left_circle), Create(left_edge), Write(left_text))
        self.play(Create(right_circle), Create(right_edge), Write(right_text))
        self.wait(1)
"""
        )

    return None


def select_examples(prompt: str, examples: Sequence[tuple[str, str]], limit: int = 4) -> list[tuple[str, str]]:
    """Choose a small set of relevant few-shot examples using keyword overlap."""

    prompt_words = {word for word in re.findall(r"[a-zA-Z0-9]+", prompt.lower()) if len(word) > 2}
    scored: list[tuple[int, tuple[str, str]]] = []
    for example in examples:
        example_words = {word for word in re.findall(r"[a-zA-Z0-9]+", example[0].lower()) if len(word) > 2}
        score = len(prompt_words & example_words)
        scored.append((score, example))
    scored.sort(key=lambda item: item[0], reverse=True)
    chosen = [example for score, example in scored if score > 0][:limit]
    return chosen or list(examples[:limit])


class ProviderStrategy(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        """Return the raw text completion from the provider."""


class AnthropicStrategy(ProviderStrategy):
    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        from anthropic import AsyncAnthropic

        settings = get_settings()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )
        return "".join(block.text for block in response.content if getattr(block, "type", "") == "text")


class OpenAIStrategy(ProviderStrategy):
    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        from openai import AsyncOpenAI

        settings = get_settings()
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
        return response.choices[0].message.content or ""


class GeminiStrategy(ProviderStrategy):
    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        import google.generativeai as genai

        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model, system_instruction=system_prompt)

        prompt_parts: list[str] = []
        for message in messages:
            prompt_parts.append(f"{message['role'].upper()}:\n{message['content']}")
        response = await model.generate_content_async("\n\n".join(prompt_parts))
        return response.text or ""


class OllamaStrategy(ProviderStrategy):
    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        settings = get_settings()
        payload = {
            "model": settings.ollama_model,
            "stream": False,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "options": {
                "num_ctx": 1024,
            },
        }
        timeout = httpx.Timeout(settings.render_timeout_seconds + 30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{settings.ollama_base_url.rstrip('/')}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        message = data.get("message", {})
        return message.get("content", "")


def get_provider_strategy(provider: str) -> ProviderStrategy:
    """Resolve a provider implementation."""

    strategies: dict[str, ProviderStrategy] = {
        "anthropic": AnthropicStrategy(),
        "openai": OpenAIStrategy(),
        "gemini": GeminiStrategy(),
        "ollama": OllamaStrategy(),
    }
    if provider not in strategies:
        raise ValueError(f"Unsupported provider: {provider}")
    return strategies[provider]


def configured_providers() -> list[str]:
    """Return providers with configured API keys."""

    settings = get_settings()
    providers: list[str] = []
    if settings.anthropic_api_key:
        providers.append("anthropic")
    if settings.openai_api_key:
        providers.append("openai")
    if settings.gemini_api_key:
        providers.append("gemini")
    if settings.ollama_model and settings.ollama_base_url:
        providers.append("ollama")
    return providers


def resolve_provider(provider: str | None) -> str:
    """Pick the request override or the configured default provider."""

    selected = provider or get_settings().llm_provider
    available = configured_providers()
    if selected not in {"anthropic", "openai", "gemini", "ollama"}:
        raise ValueError(f"Unsupported provider: {selected}")
    if selected not in available:
        raise ValueError(f"Provider '{selected}' is not configured")
    return selected


def build_generation_messages(prompt: str, examples: Sequence[tuple[str, str]] | None = None) -> list[dict[str, str]]:
    """Construct a chat transcript with optional few-shot pairs."""

    messages: list[dict[str, str]] = []
    for example_prompt, example_code in examples or []:
        messages.append({"role": "user", "content": example_prompt})
        messages.append({"role": "assistant", "content": example_code})
    messages.append({"role": "user", "content": prompt})
    return messages


async def _request_completion(
    *,
    prompt: str,
    provider: str,
    system_prompt: str,
    examples: Sequence[tuple[str, str]] | None = None,
) -> str:
    strategy = get_provider_strategy(provider)
    messages = build_generation_messages(prompt, examples)
    response = await strategy.complete(system_prompt, messages)
    return ensure_required_structure(response)


async def generate_manim_code(
    prompt: str,
    provider: str,
    examples: Sequence[tuple[str, str]] | None = None,
) -> str:
    """Generate Manim code for a natural-language prompt."""

    spec = plan_scene(prompt)
    template_code = render_scene_spec(spec)
    if template_code is not None:
        return template_code

    selected_examples = list(examples) if examples is not None else select_examples(prompt, get_examples())
    if provider == "ollama":
        selected_examples = selected_examples[:1]
    return await _request_completion(
        prompt=scene_spec_to_prompt(spec),
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
        examples=selected_examples,
    )


async def correct_manim_code(code: str, stderr: str, provider: str) -> str:
    """Request a corrected version of the failed Manim script."""

    correction_prompt = CORRECTION_PROMPT_TEMPLATE.format(code=code, stderr=stderr[:4000])
    return await _request_completion(
        prompt=correction_prompt,
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
        examples=None,
    )
