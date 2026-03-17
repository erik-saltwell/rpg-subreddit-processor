from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ollama import Client, ResponseError

_OLLAMA_HOST = "http://localhost:11434"


class OllamaModel(StrEnum):
    RedditRpgQuestionClassifier = "reddit-rpg-rules-classifier:latest"


@dataclass
class OllamaHelper:
    model_reference: OllamaModel
    _client = Client(_OLLAMA_HOST)

    def call_model(self, input: str) -> str:
        try:
            response = self._client.generate(
                model=self.model_reference,
                prompt=input,
                keep_alive="30m",
            )
        except ResponseError as exc:
            raise RuntimeError(f"Ollama request failed (status={exc.status_code}): {exc.error}") from exc

        label: str = response["response"].strip()
        return label


def labels_match(
    actual: str,
    expected: str,
    case_invariant_comparison: bool = True,
    search_length: int = -1,
    search_from_end: bool = False,
) -> bool:
    if case_invariant_comparison:
        actual = actual.lower()
        expected = expected.lower()

    if search_length >= 0:
        return expected in (actual[-search_length:] if search_from_end else actual[:search_length])
    else:
        return expected in actual
