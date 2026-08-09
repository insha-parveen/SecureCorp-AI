"""LLM provider abstraction for answer generation.

This module ensures the application is decoupled from any specific LLM API (Ollama, Groq, OpenAI).
The generator only cares about sending a prompt and receiving a structured response.
"""

from typing import Protocol, runtime_checkable
from dataclasses import dataclass

import requests

@dataclass(frozen=True)
class GenerationResponse:
    """The raw output from an LLM provider."""
    text: str
    model: str
    usage: dict[str, int]  # e.g., {"prompt_tokens": 120, "completion_tokens": 45}

@runtime_checkable
class GenerationProvider(Protocol):
    """The contract every LLM backend must satisfy."""

    @property
    def model_name(self) -> str:
        """The identifier of the model being used."""
        ...

    def generate(self, prompt: str, system_prompt: str | None = None) -> GenerationResponse:
        """Generate a response based on the provided prompts."""
        ...

class LocalLLMProvider:
    """Ollama-based local LLM implementation."""

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434") -> None:
        self._model_name = model_name
        self._base_url = base_url

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str | None = None) -> GenerationResponse:
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        return GenerationResponse(
            text=data["response"],
            model=self._model_name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
        )

class GroqLLMProvider:
    """Groq-based hosted LLM implementation using the OpenAI-compatible API."""

    def __init__(self, model_name: str, api_key: str) -> None:
        self._model_name = model_name
        self._api_key = api_key
        self._url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str | None = None) -> GenerationResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "stream": False,
        }

        response = requests.post(self._url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            print(f"Groq API Error {response.status_code}: {response.text}")
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]

        return GenerationResponse(
            text=content,
            model=self._model_name,
            usage=data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0}),
        )

def get_generation_provider(settings) -> GenerationProvider:
    """Factory to get the configured LLM provider.

    Priority: Groq (if key exists) -> Ollama (fallback).
    """
    if settings.groq_api_key:
        return GroqLLMProvider(
            model_name=settings.llm_model,
            api_key=settings.groq_api_key
        )

    return LocalLLMProvider(
        model_name=settings.llm_model,
        base_url=settings.ollama_base_url
    )
