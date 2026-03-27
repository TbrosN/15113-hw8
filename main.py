"""CLI entrypoint for the LeetCode strategy quiz app."""

from __future__ import annotations

import random
import sqlite3
from typing import Callable

import db
from constants import (
    DB_PATH,
    MAIN_MENU_OPTIONS,
    QUESTION_BANK_PATH,
    QUIZ_MENU_PROMPT,
    SKIP_TOKEN,
    VALID_DIFFICULTIES,
)
from utils import QuestionBankError, load_question_bank, normalize_answer, prompt_int, prompt_yes_no


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


def _parse_csv_choices(raw_value: str) -> set[str]:
    return {piece.strip().lower() for piece in raw_value.split(",") if piece.strip()}


def _prompt_difficulty_filters(input_fn: InputFn, output_fn: OutputFn) -> set[str]:
    prompt = (
        "Select difficulties (all or comma-separated easy,medium,hard): "
    )
    while True:
        raw_value = input_fn(prompt).strip().lower()
        if raw_value == "all":
            return set(VALID_DIFFICULTIES)
        selections = _parse_csv_choices(raw_value)
        if selections and selections.issubset(VALID_DIFFICULTIES):
            return selections
        output_fn(
            "Invalid input, expected all or comma-separated easy,medium,hard. Please try again."
        )


def _prompt_topic_filters(
    topics: set[str], input_fn: InputFn, output_fn: OutputFn
) -> set[str]:
    sorted_topics = sorted(topics)
    prompt = (
        "Select topics (all or comma-separated values from: "
        + ", ".join(sorted_topics)
        + "): "
    )
    normalized_lookup = {topic.lower(): topic for topic in sorted_topics}
    while True:
        raw_value = input_fn(prompt).strip().lower()
        if raw_value == "all":
            return set(sorted_topics)
        selections = _parse_csv_choices(raw_value)
        if selections and selections.issubset(set(normalized_lookup)):
            return {normalized_lookup[selection] for selection in selections}
        output_fn(
            "Invalid input, expected all or valid comma-separated topic names. Please try again."
        )


def filter_questions(
    questions: list[dict],
    selected_difficulties: set[str],
    selected_topics: set[str],
    skipped_question_ids: set[str],
) -> list[dict]:
    return [
        question
        for question in questions
        if question["difficulty"] in selected_difficulties
        and question["topic"] in selected_topics
        and question["id"] not in skipped_question_ids
    ]


def choose_quiz_questions(
    questions: list[dict], question_count: int, randomizer: random.Random
) -> list[dict]:
    if question_count >= len(questions):
        return randomizer.sample(questions, len(questions))
    return randomizer.sample(questions, question_count)


def prompt_quiz_settings(
    questions: list[dict], input_fn: InputFn, output_fn: OutputFn
) -> dict:
    question_count = prompt_int(
        "How many questions do you want in the quiz? (>=1): ",
        minimum=1,
        input_func=input_fn,
        output_func=output_fn,
    )
    difficulties = _prompt_difficulty_filters(input_fn, output_fn)
    all_topics = {question["topic"] for question in questions}
    topics = _prompt_topic_filters(all_topics, input_fn, output_fn)
    return {
        "question_count": question_count,
        "difficulties": difficulties,
        "topics": topics,
    }


def run_single_quiz(
    user_id: int,
    questions: list[dict],
    settings: dict,
    input_fn: InputFn,
    output_fn: OutputFn,
    randomizer: random.Random,
    db_path: str,
) -> tuple[int, int]:
    skipped_ids = db.get_permanently_skipped_question_ids(user_id, db_path=db_path)
    filtered_questions = filter_questions(
        questions=questions,
        selected_difficulties=settings["difficulties"],
        selected_topics=settings["topics"],
        skipped_question_ids=skipped_ids,
    )
    if not filtered_questions:
        output_fn("No questions matched your filters and skip settings.")
        return (0, 0)

    selected_count = min(settings["question_count"], len(filtered_questions))
    selected_questions = choose_quiz_questions(
        questions=filtered_questions,
        question_count=selected_count,
        randomizer=randomizer,
    )
    correct_answers = 0

    for index, question in enumerate(selected_questions, start=1):
        output_fn("")
        output_fn(
            f"[{index}/{selected_count}] ({question['difficulty']}, {question['topic']})"
        )
        output_fn(question["question"])
        response = input_fn(
            "Your high-level strategy answer (or 'skip' to skip this question): "
        ).strip()
        if normalize_answer(response) == SKIP_TOKEN:
            should_skip_forever = prompt_yes_no(
                "Always skip this question in the future? (yes/no): ",
                input_func=input_fn,
                output_func=output_fn,
            )
            if should_skip_forever:
                try:
                    db.add_permanent_skip(user_id, question["id"], db_path=db_path)
                    output_fn("Question will be permanently skipped in future quizzes.")
                except sqlite3.DatabaseError:
                    output_fn("Database error while saving skip; continuing quiz.")
            continue

        is_correct = normalize_answer(response) == normalize_answer(question["answer"])
        if is_correct:
            correct_answers += 1
            output_fn("Correct.")
        else:
            output_fn(f"Incorrect. Expected strategy: {question['answer']}")
        try:
            db.record_answer(
                user_id=user_id,
                question_id=question["id"],
                user_answer=response,
                is_correct=is_correct,
                difficulty=question["difficulty"],
                topic=question["topic"],
                db_path=db_path,
            )
        except sqlite3.DatabaseError:
            output_fn("Database error while saving answer metadata; continuing quiz.")

    try:
        db.record_score(user_id, correct_answers, selected_count, db_path=db_path)
    except sqlite3.DatabaseError:
        output_fn("Database error while saving score; continuing.")

    return (correct_answers, selected_count)


def run_quiz_with_replay(
    user_id: int,
    questions: list[dict],
    settings: dict,
    input_fn: InputFn,
    output_fn: OutputFn,
    randomizer: random.Random,
    db_path: str,
) -> None:
    while True:
        correct, total = run_single_quiz(
            user_id=user_id,
            questions=questions,
            settings=settings,
            input_fn=input_fn,
            output_fn=output_fn,
            randomizer=randomizer,
            db_path=db_path,
        )
        output_fn(f"Quiz complete! Score: {correct}/{total}")
        should_replay = prompt_yes_no(
            "Play again with the same settings? (yes/no): ",
            input_func=input_fn,
            output_func=output_fn,
        )
        if not should_replay:
            return


def show_user_scores(user_id: int, output_fn: OutputFn, db_path: str) -> None:
    scores = db.get_scores_for_user(user_id, db_path=db_path)
    if not scores:
        output_fn("No scores recorded yet.")
        return
    output_fn("Your past scores:")
    for score in scores:
        output_fn(
            f"- {score['created_at']}: {score['correct_count']}/{score['total_count']}"
        )


def login_or_create_account(input_fn: InputFn, output_fn: OutputFn, db_path: str) -> int | None:
    username = input_fn("Username: ").strip()
    if not username:
        output_fn("Invalid input, expected a non-empty username. Please try again.")
        return None

    user = db.get_user_by_username(username, db_path=db_path)
    if user is None:
        output_fn(f"Username '{username}' does not exist.")
        should_create = prompt_yes_no(
            "Do you want to create an account? (yes/no): ",
            input_func=input_fn,
            output_func=output_fn,
        )
        if not should_create:
            return None
        password = input_fn("Create a password: ")
        if not password:
            output_fn("Invalid input, expected a non-empty password. Please try again.")
            return None
        return db.create_user(username, password, db_path=db_path)

    password = input_fn("Password: ")
    user_id = db.authenticate_user(username, password, db_path=db_path)
    if user_id is None:
        output_fn("Invalid credentials. Exiting.")
        return None
    return user_id


def run_app(
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
    db_path: str = DB_PATH,
    question_bank_path: str = QUESTION_BANK_PATH,
    random_seed: int | None = None,
) -> int:
    randomizer = random.Random(random_seed)

    try:
        questions = load_question_bank(question_bank_path)
    except QuestionBankError as exc:
        output_fn(f"Fatal error: {exc}")
        return 1

    try:
        db.ensure_db_file(db_path=db_path)
        db.init_db(db_path=db_path)
    except sqlite3.DatabaseError as exc:
        output_fn(f"Fatal database error during initialization: {exc}")
        return 1

    try:
        user_id = login_or_create_account(input_fn, output_fn, db_path)
    except sqlite3.DatabaseError as exc:
        output_fn(f"Fatal database error during login: {exc}")
        return 1
    if user_id is None:
        return 0

    while True:
        choice = input_fn(QUIZ_MENU_PROMPT).strip()
        if choice not in MAIN_MENU_OPTIONS:
            output_fn("Invalid input, expected one of: 1, 2, 3. Please try again.")
            continue
        if choice == "1":
            settings = prompt_quiz_settings(questions, input_fn, output_fn)
            run_quiz_with_replay(
                user_id=user_id,
                questions=questions,
                settings=settings,
                input_fn=input_fn,
                output_fn=output_fn,
                randomizer=randomizer,
                db_path=db_path,
            )
        elif choice == "2":
            show_user_scores(user_id, output_fn, db_path=db_path)
        else:
            output_fn("Goodbye.")
            return 0


if __name__ == "__main__":
    raise SystemExit(run_app())
