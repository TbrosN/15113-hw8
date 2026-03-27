from __future__ import annotations

import random
from pathlib import Path

import db
from conftest import ScriptedIO
from main import run_quiz_with_replay, run_single_quiz
from utils import load_question_bank


def _quiz_settings() -> dict:
    return {
        "question_count": 1,
        "difficulties": {"easy", "medium", "hard"},
        "topics": {"Arrays"},
    }


def test_permanent_skip_persists_between_quizzes(tmp_path: Path) -> None:
    db_path = str(tmp_path / "skip.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = load_question_bank(Path("tests/question_banks/valid_single.json"))

    io = ScriptedIO(["skip", "yes"])
    run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert db.is_permanently_skipped(user_id, "single1", db_path=db_path)

    io_second = ScriptedIO([])
    result = run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io_second.input,
        output_fn=io_second.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert result == (0, 0)
    assert any("No questions matched" in line for line in io_second.outputs)


def test_non_permanent_skip_does_not_persist(tmp_path: Path) -> None:
    db_path = str(tmp_path / "skip-temp.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = load_question_bank(Path("tests/question_banks/valid_single.json"))

    io = ScriptedIO(["skip", "no"])
    run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert not db.is_permanently_skipped(user_id, "single1", db_path=db_path)

    io_second = ScriptedIO(["hash map"])
    result = run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io_second.input,
        output_fn=io_second.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )
    assert result == (1, 1)


def test_replay_loop_exits_when_no_questions_available(tmp_path: Path) -> None:
    db_path = str(tmp_path / "skip-replay.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = load_question_bank(Path("tests/question_banks/valid_single.json"))
    db.add_permanent_skip(user_id, "single1", db_path=db_path)

    io = ScriptedIO([])
    run_quiz_with_replay(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert any("No questions matched" in line for line in io.outputs)
    assert not any("Quiz complete! Score:" in line for line in io.outputs)


def test_multiple_choice_accepts_letter_input(tmp_path: Path) -> None:
    db_path = str(tmp_path / "multi-choice.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = [
        {
            "id": "mc1",
            "question": "Two Sum O(n) strategy?",
            "type": "multiple_choice",
            "options": [
                "Nested loops",
                "Single-pass hash map",
                "Sort then binary search",
                "Prefix sums",
            ],
            "answer": "Single-pass hash map",
            "topic": "Arrays",
            "difficulty": "easy",
        }
    ]

    io = ScriptedIO(["B"])
    result = run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert result == (1, 1)
    assert any("Correct." in line for line in io.outputs)


def test_multiple_choice_accepts_multiple_letters(tmp_path: Path) -> None:
    db_path = str(tmp_path / "multi-choice-multi.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = [
        {
            "id": "mc-multi",
            "question": "Efficient structures for island counting?",
            "type": "multiple_choice",
            "options": [
                "Stack",
                "Queue",
                "Heap",
                "Linked list",
            ],
            "answer": ["Stack", "Queue"],
            "topic": "Arrays",
            "difficulty": "easy",
        }
    ]

    io = ScriptedIO(["A,B"])
    result = run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert result == (1, 1)
    assert any("Correct." in line for line in io.outputs)


def test_multiple_choice_partial_selection_counts_as_correct(tmp_path: Path) -> None:
    db_path = str(tmp_path / "multi-choice-partial.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = [
        {
            "id": "mc-partial",
            "question": "Efficient structures for island counting?",
            "type": "multiple_choice",
            "options": [
                "Stack",
                "Queue",
                "Heap",
                "Linked list",
            ],
            "answer": ["Stack", "Queue"],
            "topic": "Arrays",
            "difficulty": "easy",
        }
    ]

    io = ScriptedIO(["A"])
    result = run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    assert result == (1, 1)
    assert any("Correct." in line for line in io.outputs)


def test_all_skipped_questions_do_not_record_score(tmp_path: Path) -> None:
    db_path = str(tmp_path / "all-skipped.sqlite")
    db.init_db(db_path=db_path)
    user_id = db.create_user("alice", "password", db_path=db_path)
    questions = [
        {
            "id": "mc-skip",
            "question": "Efficient structures for island counting?",
            "type": "multiple_choice",
            "options": [
                "Stack",
                "Queue",
                "Heap",
                "Linked list",
            ],
            "answer": ["Stack", "Queue"],
            "topic": "Arrays",
            "difficulty": "easy",
        }
    ]

    io = ScriptedIO(["skip", "no"])
    result = run_single_quiz(
        user_id=user_id,
        questions=questions,
        settings=_quiz_settings(),
        input_fn=io.input,
        output_fn=io.print,
        randomizer=random.Random(0),
        db_path=db_path,
    )

    scores = db.get_scores_for_user(user_id, db_path=db_path)
    assert result == (0, 0)
    assert scores == []
    assert any("No scored questions this round" in line for line in io.outputs)
