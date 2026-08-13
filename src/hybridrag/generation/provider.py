"""LLM provider abstraction for answer generation.

This module ensures the application is decoupled from any specific LLM API (Ollama, Groq, OpenAI).
The generator only cares about sending a prompt and receiving a structured response.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

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

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_mode: bool = True,
    ) -> GenerationResponse:
        """Generate a response based on the provided prompts.

        ``json_mode`` (default True) requests a JSON-envelope response.
        Callers that want prose (e.g. the structured-SQL answer
        generator) should pass ``json_mode=False``. Hosts that cannot
        turn the envelope off (Groq's ``response_format=json_object``
        is provider-wide) should ignore the flag and let the caller
        parse the envelope.
        """
        ...

    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        """Yield incremental text tokens from the model.

        Unlike ``generate``, this method:
        - Does NOT request ``format: json_object`` (prose stream is desired).
        - Yields the model's own text fragments as they arrive.
        - The caller is responsible for assembling the full text and parsing
          it as JSON if needed (Phase 9 MVP: parse at the end of the stream).
        """
        ...


class LocalLLMProvider:
    """Ollama-based local LLM implementation."""

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434") -> None:
        self._model_name = model_name
        self._base_url = base_url

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_mode: bool = True,
    ) -> GenerationResponse:
        payload: dict[str, Any] = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"
        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(f"{self._base_url}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        return GenerationResponse(
            text=data["response"],
            model=self._model_name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        """Yield text tokens from the Ollama ``/api/generate`` streaming endpoint.

        Note: ``format: json`` is intentionally dropped here. The streaming
        path expects prose; the caller parses the assembled text as JSON at
        the end of the stream (Phase 9 MVP streaming design).
        """
        payload: dict[str, Any] = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        # ``stream=True`` on the requests side; we read line-delimited JSON.
        with requests.post(
            f"{self._base_url}/api/generate", json=payload, timeout=120, stream=True
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if chunk.get("done"):
                    return
                token = chunk.get("response", "")
                if token:
                    yield token


class GroqLLMProvider:
    """Groq-based hosted LLM implementation using the OpenAI-compatible API."""

    def __init__(self, model_name: str, api_key: str) -> None:
        self._model_name = model_name
        self._api_key = api_key
        self._url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_mode: bool = True,
    ) -> GenerationResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": 0,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

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

    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        """Yield text tokens from Groq's OpenAI-compatible SSE stream.

        Drops ``response_format=json_object`` so the model emits prose; the
        caller parses the assembled text as JSON at end of stream.
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": 0,
            "stream": True,
        }

        with requests.post(
            self._url, headers=headers, json=payload, timeout=120, stream=True
        ) as response:
            if response.status_code != 200:
                print(f"Groq API Error {response.status_code}: {response.text}")
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                # SSE: lines start with "data: " — the final frame is "data: [DONE]".
                if isinstance(line, bytes):
                    if not line.startswith(b"data: "):
                        continue
                    data_str = line[len(b"data: ") :].decode("utf-8").strip()
                else:
                    if not line.startswith("data: "):
                        continue
                    data_str = line[len("data: ") :].strip()
                if data_str == "[DONE]":
                    return
                try:
                    parsed = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = parsed.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                token = delta.get("content")
                if token:
                    yield token


def get_generation_provider(settings: Any) -> GenerationProvider:
    """Factory to get the configured LLM provider.

    Priority: Groq (if key exists) -> Ollama (fallback).
    """
    if settings.groq_api_key:
        return GroqLLMProvider(model_name=settings.llm_model, api_key=settings.groq_api_key)

    return LocalLLMProvider(model_name=settings.llm_model, base_url=settings.ollama_base_url)
