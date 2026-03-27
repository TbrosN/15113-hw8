from __future__ import annotations

from pathlib import Path

import db


def test_password_is_stored_hashed_and_not_plaintext(tmp_path: Path) -> None:
    db_path = str(tmp_path / "auth.sqlite")
    db.init_db(db_path=db_path)
    db.create_user("alice", "super-secret-password", db_path=db_path)
    stored_hash = db.get_stored_password_hash("alice", db_path=db_path)
    assert stored_hash is not None
    assert stored_hash != "super-secret-password"
    assert db.authenticate_user("alice", "super-secret-password", db_path=db_path) is not None
    assert db.authenticate_user("alice", "wrong-password", db_path=db_path) is None


def test_score_queries_are_scoped_to_requesting_user(tmp_path: Path) -> None:
    db_path = str(tmp_path / "scores.sqlite")
    db.init_db(db_path=db_path)
    alice_id = db.create_user("alice", "pw1", db_path=db_path)
    bob_id = db.create_user("bob", "pw2", db_path=db_path)
    db.record_score(alice_id, 3, 5, db_path=db_path)
    db.record_score(bob_id, 1, 5, db_path=db_path)

    alice_scores = db.get_scores_for_user(alice_id, db_path=db_path)
    bob_scores = db.get_scores_for_user(bob_id, db_path=db_path)

    assert len(alice_scores) == 1
    assert len(bob_scores) == 1
    assert alice_scores[0]["user_id"] == alice_id
    assert bob_scores[0]["user_id"] == bob_id
