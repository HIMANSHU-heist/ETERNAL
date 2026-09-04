"""
Pluggable LLM provider layer.

Why this exists: every part of the app (chat router, future planner/analyst
agents) should call `get_llm_provider().chat(...)` and never import Groq/
OpenAI/Anthropic directly. That means switching providers later (or running
multiple providers side by side, e.g. Groq for speed + Claude for planning)
is a config change, not a rewrite.

Env vars:
    LLM_PROVIDER   -> "groq" (default). Add "openai" / "anthropic" / "ollama"
                      later by writing a new class below.
    GROQ_API_KEY   -> required if LLM_PROVIDER=groq
    GROQ_MODEL     -> optional, defaults to llama-3.3-70b-versatile
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional


class LLMProvider(ABC):
    @abstractmethod
    def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[dict]] = None,
    ) -> str:
        """Return the assistant's text reply."""
        raise NotImplementedError


class GroqProvider(LLMProvider):
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq  # imported lazily so app boots even if groq isn't installed

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your environment or .env file."
            )
        self.client = Groq(api_key=api_key)
        self.model = model

    def chat(self, system_prompt, user_message, history=None):
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content


# --- Future providers (not wired up yet, shown so the pattern is clear) ---
#
# class OpenAIProvider(LLMProvider):
#     ...
#
# class AnthropicProvider(LLMProvider):
#     ...
#
# class OllamaProvider(LLMProvider):
#     ...


_PROVIDER_REGISTRY = {
    "groq": lambda: GroqProvider(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")),
}


def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "groq").lower()
    factory = _PROVIDER_REGISTRY.get(provider_name)
    if not factory:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Available: {list(_PROVIDER_REGISTRY.keys())}"
        )
    return factory()