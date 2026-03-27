from __future__ import annotations

from pathlib import Path

from conftest import ScriptedIO
from main import run_app
from utils import QuestionBankError, load_question_bank


def test_missing_question_bank_raises_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.json"
    try:
        load_question_bank(missing_path)
        assert False, "Expected QuestionBankError for missing file."
    except QuestionBankError:
        pass


def test_malformed_question_bank_raises_error() -> None:
    malformed = Path("tests/question_banks/malformed.json")
    try:
        load_question_bank(malformed)
        assert False, "Expected QuestionBankError for malformed file."
    except QuestionBankError:
        pass


def test_empty_question_bank_raises_error() -> None:
    empty_path = Path("tests/question_banks/empty.json")
    try:
        load_question_bank(empty_path)
        assert False, "Expected QuestionBankError for empty question set."
    except QuestionBankError:
        pass


def test_question_bank_read_oserror_raises_error(monkeypatch) -> None:
    test_path = Path("tests/question_banks/valid_mixed.json")

    def _raise_oserror(*_args, **_kwargs) -> str:
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "read_text", _raise_oserror)
    try:
        load_question_bank(test_path)
        assert False, "Expected QuestionBankError for unreadable file."
    except QuestionBankError:
        pass


def test_question_bank_read_unicode_error_raises_error(monkeypatch) -> None:
    test_path = Path("tests/question_banks/valid_mixed.json")

    def _raise_unicode_error(*_args, **_kwargs) -> str:
        raise UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte")

    monkeypatch.setattr(Path, "read_text", _raise_unicode_error)
    try:
        load_question_bank(test_path)
        assert False, "Expected QuestionBankError for non-UTF-8 file."
    except QuestionBankError:
        pass


def test_app_exits_with_fatal_error_for_bad_question_bank(tmp_path: Path) -> None:
    io = ScriptedIO([])
    exit_code = run_app(
        input_fn=io.input,
        output_fn=io.print,
        db_path=str(tmp_path / "test.sqlite"),
        question_bank_path=str(tmp_path / "missing.json"),
    )
    assert exit_code == 1
    assert any("Fatal error:" in line for line in io.outputs)
