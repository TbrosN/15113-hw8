"""Application-wide constants."""

DB_PATH = "sqlite.db"
QUESTION_BANK_PATH = "questions.json"

MAIN_MENU_OPTIONS = {"1", "2", "3"}
QUIZ_MENU_PROMPT = (
    "Main menu:\n"
    "1) Start a new quiz\n"
    "2) View my past scores\n"
    "3) Exit\n"
    "Choose an option: "
)

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
YES_VALUES = {"y", "yes"}
NO_VALUES = {"n", "no"}
SKIP_TOKEN = "skip"
