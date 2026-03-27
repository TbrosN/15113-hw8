from __future__ import annotations

from pathlib import Path

import db
from conftest import ScriptedIO
from main import filter_questions, run_app
from utils import load_question_bank


def test_question_filtering_respects_difficulty_and_topic() -> None:
    questions = load_question_bank(Path("tests/question_banks/valid_mixed.json"))
    filtered = filter_questions(
        questions=questions,
        selected_difficulties={"medium"},
        selected_topics={"Trees", "Graphs"},
        skipped_question_ids=set(),
    )
    assert {question["id"] for question in filtered} == {"q2", "q3"}


def test_create_account_and_play_quiz_end_to_end(tmp_path: Path) -> None:
    db_path = str(tmp_path / "end_to_end.sqlite")
    io = ScriptedIO(
        [
            "new-user",  # username (does not exist)
            "yes",  # create account
            "pw123",  # password
            "1",  # main menu -> start quiz
            "2",  # request two questions
            "easy",  # filter difficulties
            "Arrays",  # filter topics
            "hash map",  # answer for the only matching question
            "no",  # replay with same settings?
            "2",  # view scores
            "3",  # exit
        ]
    )

    exit_code = run_app(
        input_fn=io.input,
        output_fn=io.print,
        db_path=db_path,
        question_bank_path="tests/question_banks/valid_mixed.json",
        random_seed=3,
        password_input_fn=io.input,
    )
    assert exit_code == 0

    user_id = db.authenticate_user("new-user", "pw123", db_path=db_path)
    assert user_id is not None
    scores = db.get_scores_for_user(user_id, db_path=db_path)
    assert len(scores) >= 1
    assert any("Quiz complete! Score:" in line for line in io.outputs)
    assert any("Your past scores:" in line for line in io.outputs)
