[FAIL] The score-privacy acceptance criterion is only half-met. The CLI and query layer do scope score lookup to the current user in main.py and db.py, but the default database location is the project-root file sqlite.db in constants.py. That means once the app is actually used, user scores and password hashes are stored in a codebase file that a local onlooker can inspect with standard SQLite tools. I checked the current sqlite.db; it is empty right now, but the default design still violates the "someone should not be able to ascertain user scores just by looking at the codebase files" part of the spec.

[WARN] Password entry is visible on screen. In login_or_create_account() in main.py, both account creation and login use normal text input for passwords, so passwords will be echoed to the terminal. That is a security and UX issue even though the stored value is hashed.

[WARN] Question-bank I/O errors are only partially handled. In utils.py, load_question_bank() catches json.JSONDecodeError, but it does not catch OSError or UnicodeDecodeError from read_text(). A permission problem or non-UTF-8 file would likely crash with a traceback instead of producing the intended fatal error message.

[WARN] The "no eligible questions" path has confusing UX. run_single_quiz() in main.py prints "No questions matched your filters and skip settings." and returns (0, 0), but run_quiz_with_replay() still prints Quiz complete! Score: 0/0 and asks whether to replay. That is technically consistent with the return value, but confusing for users.

[WARN] Database read failures are not handled consistently. main.py catches database errors when saving skips, answers, and scores, but not when reading permanently skipped IDs or reading past scores. If db.get_permanently_skipped_question_ids() or db.get_scores_for_user() fails, the app can terminate unexpectedly.

[PASS] Invalid, empty, missing, and malformed question-bank files are handled correctly for the covered acceptance cases. run_app() in main.py catches QuestionBankError and exits with a fatal message, and load_question_bank() in utils.py rejects missing files, malformed JSON, empty question lists, invalid schema, duplicate IDs, and invalid difficulties. tests/test_question_bank_errors.py covers the missing/malformed/empty paths.

[PASS] Passwords are not stored in plaintext. db.py hashes them with bcrypt.hashpw() and verifies them with bcrypt.checkpw(). The spec says "encrypted," but hashing is the better practice for passwords, and the implementation is correct on that point.

[PASS] Creating a new account and then playing a quiz works. login_or_create_account() in main.py supports the create-account flow, and tests/test_filters_and_cli_flow.py exercises create account -> start quiz -> answer questions -> view scores successfully.

[PASS] A user can skip through all questions. In run_single_quiz() in main.py, entering skip simply branches to the optional permanent-skip prompt and then continues to the next question, so nothing blocks a user from skipping every question in a session.

[PASS] Permanent skips persist across restarts. db.add_permanent_skip() stores the skip in question_skips in db.py, and run_single_quiz() reloads permanently skipped IDs before filtering questions in main.py. tests/test_skip_persistence.py verifies that a permanently skipped question does not reappear later.

[PASS] Non-permanent skips do not persist. In main.py, the only path that writes a skip is the if should_skip_forever: branch. If the user answers no, nothing is saved. tests/test_skip_persistence.py confirms that the question is asked again on a later run.

[PASS] The replay flow, main menu flow, and question filtering all match the spec. After each quiz, run_quiz_with_replay() in main.py prints the score and asks whether to replay with the same settings; answering no returns to the main menu loop, where the user can start another quiz, view scores, or exit. Filtering is enforced before question sampling by filter_questions(), and tests/test_filters_and_cli_flow.py confirms difficulty/topic filtering works as intended.