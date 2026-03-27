"""Shared testing helpers for scripted CLI input/output."""

from __future__ import annotations


class ScriptedIO:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0
        self.outputs: list[str] = []

    def input(self, _prompt: str = "") -> str:
        if self._index >= len(self._responses):
            raise AssertionError("ScriptedIO ran out of responses.")
        value = self._responses[self._index]
        self._index += 1
        return value

    def print(self, message: str) -> None:
        self.outputs.append(message)
