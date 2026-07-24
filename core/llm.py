from __future__ import annotations

import json
import urllib.error
import urllib.request

from .config import LLMConfig
from .models import Generation, Usage


class OpenAIResponsesProvider:
    """Small Responses API adapter isolated behind LLMProvider."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @staticmethod
    def _supports_temperature(model: str) -> bool:
        # GPT-5-family models currently reject the temperature field on the
        # Responses API; sampling is controlled by the model/reasoning mode.
        return not model.lower().startswith("gpt-5")

    def generate(
        self, prompt: str, *, model: str | None = None, reasoning_effort: str | None = None
    ) -> Generation:
        if not self.config.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        selected_model = model or self.config.model
        payload = {
            "model": selected_model,
            "input": prompt,
        }
        if self._supports_temperature(selected_model):
            payload["temperature"] = self.config.temperature
        if reasoning_effort:
            payload["reasoning"] = {"effort": reasoning_effort}
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed ({exc.code}): {detail[:500]}") from exc
        text = result.get("output_text", "")
        if not text:
            text = "".join(
                part.get("text", "")
                for output in result.get("output", [])
                for part in output.get("content", [])
                if part.get("type") in {"output_text", "text"}
            )
        raw_usage = result.get("usage", {})
        usage = Usage(
            input_tokens=int(raw_usage.get("input_tokens", 0)),
            output_tokens=int(raw_usage.get("output_tokens", 0)),
            total_tokens=int(raw_usage.get("total_tokens", 0)),
        )
        return Generation(text.strip(), selected_model, usage)


class ExtractiveProvider:
    """Offline provider that preserves the grounded-answer contract."""

    def generate(
        self, prompt: str, *, model: str | None = None, reasoning_effort: str | None = None
    ) -> Generation:
        marker = "PDF evidence:\n"
        evidence = prompt.split(marker, 1)[-1].split("\n\nSQL evidence:", 1)[0].strip()
        if not evidence or evidence == "(none)":
            text = "Insufficient retrieved PDF evidence to answer this question."
        else:
            excerpt = evidence[:1800]
            text = f"Retrieved evidence (LLM disabled):\n{excerpt}"
        return Generation(text, model or "extractive")


def create_llm(config: LLMConfig):
    if config.provider == "extractive" or not config.api_key:
        return ExtractiveProvider()
    if config.provider == "openai":
        return OpenAIResponsesProvider(config)
    raise ValueError(f"Unsupported LLM provider: {config.provider}")
