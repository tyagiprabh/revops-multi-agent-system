"""Thin wrapper around the Anthropic SDK.

Kept in one place so the agents never import `anthropic` directly: the whole
pipeline runs offline without the package installed, and live mode is a
single optional dependency (`pip install "revops[live]"`).
"""

import os
from typing import TypeVar

from pydantic import BaseModel

DEFAULT_MODEL = "claude-opus-5"

T = TypeVar("T", bound=BaseModel)


def api_key_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


class ClaudeClient:
    """Structured-output and prose calls against the Claude API."""

    def __init__(self, model: str = DEFAULT_MODEL):
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Live mode needs the anthropic package: pip install 'revops[live]'"
            ) from exc
        self._client = anthropic.Anthropic()
        self.model = model

    def parse(self, system: str, prompt: str, schema: type[T]) -> T:
        """Ask Claude and validate the answer against a pydantic schema."""
        response = self._client.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
        if response.parsed_output is None:  # pragma: no cover
            raise RuntimeError(f"Claude returned no parseable {schema.__name__}")
        return response.parsed_output

    def write(self, system: str, prompt: str) -> str:
        """Ask Claude for prose (used by the digest agent's narrative)."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "\n".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
