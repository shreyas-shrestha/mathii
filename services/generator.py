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

    selected_examples = list(examples) if examples is not None else select_examples(prompt, get_examples())
    if provider == "ollama":
        selected_examples = selected_examples[:1]
    return await _request_completion(
        prompt=prompt,
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
