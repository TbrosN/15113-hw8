"""Utility helpers for IO validation and question-bank loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from constants import NO_VALUES, YES_VALUES


class QuestionBankError(Exception):
    """Raised when question bank JSON is missing, malformed, or invalid."""


def normalize_answer(answer: str) -> str:
    return answer.strip().lower()


def parse_yes_no(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in YES_VALUES:
        return True
    if normalized in NO_VALUES:
        return False
    return None


def prompt_yes_no(
    prompt: str,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> bool:
    while True:
        value = input_func(prompt)
        parsed = parse_yes_no(value)
        if parsed is not None:
            return parsed
        output_func("Invalid input, expected yes/no. Please try again.")


def prompt_int(
    prompt: str,
    minimum: int,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> int:
    while True:
        value = input_func(prompt).strip()
        try:
            parsed = int(value)
        except ValueError:
            output_func("Invalid input, expected an integer. Please try again.")
            continue
        if parsed < minimum:
            output_func(f"Invalid input, expected an integer >= {minimum}. Please try again.")
            continue
        return parsed


def _validate_question(question: dict[str, Any]) -> None:
    required = {"id", "question", "answer", "difficulty", "topic"}
    missing = required - question.keys()
    if missing:
        missing_values = ", ".join(sorted(missing))
        raise QuestionBankError(
            f"Question is missing required field(s): {missing_values}"
        )
    difficulty = str(question["difficulty"]).strip().lower()
    if difficulty not in {"easy", "medium", "hard"}:
        raise QuestionBankError(
            f"Question has invalid difficulty '{question['difficulty']}'."
        )
    if not str(question["id"]).strip():
        raise QuestionBankError("Question id must be non-empty.")


def load_question_bank(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise QuestionBankError(f"Question bank file not found at '{file_path}'.")

    try:
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QuestionBankError(f"Question bank JSON is malformed: {exc}") from exc

    if not isinstance(raw_data, dict) or "questions" not in raw_data:
        raise QuestionBankError("Question bank JSON must contain a top-level 'questions' key.")

    questions = raw_data["questions"]
    if not isinstance(questions, list) or not questions:
        raise QuestionBankError("Question bank is empty or has an invalid 'questions' format.")

    seen_ids: set[str] = set()
    for question in questions:
        if not isinstance(question, dict):
            raise QuestionBankError("Each question entry must be an object.")
        _validate_question(question)
        question_id = str(question["id"]).strip()
        if question_id in seen_ids:
            raise QuestionBankError(f"Duplicate question id found: '{question_id}'.")
        seen_ids.add(question_id)
        question["id"] = question_id
        question["difficulty"] = str(question["difficulty"]).strip().lower()
        question["topic"] = str(question["topic"]).strip()
        question["answer"] = str(question["answer"]).strip()

    return questions
