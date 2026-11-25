"""Talk to a language model. One small interface so the model can be swapped (Gemini today).

Set GEMINI_API_KEY (free at https://aistudio.google.com) and optionally GEMINI_MODEL.
"""
import os
import tomllib
from typing import Protocol

DEFAULT_MODEL = "gemini-flash-latest"  # Google's alias for the current free-tier Flash model


def read_secret(name: str, path: str = ".streamlit/secrets.toml") -> str | None:
    """Environment variable first, then the private (git-ignored) Streamlit secrets file."""
    if os.environ.get(name):
        return os.environ[name]
    try:
        with open(path, "rb") as f:
            return tomllib.load(f).get(name)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return None


class LLMUnavailable(Exception):
    """Quota used up (HTTP 429), bad key, or network trouble: the app shows a friendly message."""


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


class GeminiLLM:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        from google import genai

        key = api_key or read_secret("GEMINI_API_KEY")
        if not key or key == "paste-your-key-here":
            raise LLMUnavailable("GEMINI_API_KEY is not set")
        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self._client = genai.Client(api_key=key)

    def complete(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(model=self.model, contents=prompt)
        except Exception as e:  # quota, auth, network: all mean "can't answer right now"
            raise LLMUnavailable(str(e)) from e
        return response.text or ""


class FakeLLM:
    """For tests: returns (or raises) the given responses in order and records every prompt."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
