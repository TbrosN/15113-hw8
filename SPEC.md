# Overview
We are building a CLI tool in python that is a quiz app. The goal is to help users learn and practice Leetcode by giving short problem descriptions and asking them to figure out the high-level approach (which data structures to use and high-level algorithmic strategy).

# App Behavior
The app behaves as follows:
1. User is prompted for a username and password-based login (or account creation).
  - If the user enters a username that doesnt exist, they are told it doesnt exist and are asked if they want to create an account. If they say yes, they are prompted for a password and the account is created. If they say no, the app just exits.
2. The user is asked some basic questions about the quiz (how many questions, difficulty ranges, topics)
3. App fetches a random subset of qualifying questions from the question bank, by loading the quesion bank JSON file and filtering based on the user's preferences.
4. As user answers questions, the app tracks their score. In the db, it is keeping track of user answers and metadata like question, answer, correct/incorrect, difficulty, topic
5. If user doesn't like the question (e.g. they have already seen it before), they can skip it by entering "skip". Then they will be asked if they want to always skip this question in the future.
6.
# Database Schema
## Users
- Each user has an id, a username, and an encrypted password. For the encryption, please use an appropriate python library rather than implementing it yourself.
## Question Skips
- We have a table that tracks which questions a user has chosen to permanently skip. This table has an id, a user id, and a question id.
## Questions (Not in DB)
- Important Note: Questions are stored in a JSON file in our project (see Data Format section below). In paricular, we do NOT store questions in the database.
## Scores
- We store each user's scores in the db. Critically, a user should be able to see their own scores, but not other users' scores. A score is just the performance on the quiz, number correct out of total questions. We also store an id and a user id for each score entry. We store a timestamp for when the score was achieved, so that we can query this table and see how scores have changed over time.

# Data Format
The question bank will be a JSON file following this format:
```
{
  "questions": [
    {
      "question": "What keyword is used to define a function in Python?",
      "type": "multiple_choice",
      "options": ["func", "define", "def", "function"],
      "answer": "def",
      "category": "Python Basics",
      "id": "1"
    },
    {
      "question": "A list in Python is immutable.",
      "type": "true_false",
      "answer": "false",
      "category": "Data Structures",
      "id": "2"
    },
    {
      "question": "What built-in function returns the number of items in a list?",
      "type": "short_answer",
      "answer": "len",
      "category": "Python Basics",
      "id": "3"
    }
  ]
}
```

# Error handling
- If user enters an invalid input, the app prints an error saying something like "Invalid input, expected <expected inputs>. Please try again."
- If the JSON file is missing or malformed or empty, this is a fatal error. The app should print an error message and exit.
- If a database error occurs, failure behavior depends on the error. IF we failed to login the user, the app should exit, this is fatal. But if we just failed to insert a question skip, the app should print an error message and continue.

# Acceptance Criteria
- Running the app with an invalid, empty, or missing question bank JSON file will print an error message and exit.
- Passwords are stored encrypted in the database and are not visible to anyone (unencrypted), not even our own app.
- Should be able to create a new account and play a quiz. If desired, I should be able to skip through all the questions.
- If I skip a question and then permanently choose to skip it, I should be able to stop and restart the cli tool, and then the question will never be asked again.
- If I skip a question and don't choose to permanently skip it, I should be able to stop and restart the cli tool, and then the question will be asked again.
- A user shuold not be able to view scores of other users, and someone should not be able to ascertain user scores just by looking at the codebase files.
- When the quiz is over, the app should print the user's score and ask if they want to play again. If they say yes, another quiz starts with the same settings as before. If not, they go back to the main menu. From there, they can start a new quiz with possible different settings, view their past scores, or exit the app.
- If I choose to filter on certain difficulties or topics, all questions in the quiz should be from that filtered set. For example, if I choose easy only, all questions should haev dificulty easy

# File structure
- questions.json: The question bank JSON file.
- db.py: The database module, responsible for all database operations.
- main.py: The main module, responsible for running the cli tool. The cli tool calls functions from db.py to interact with the database.
- sqlite.db: The sqlite database file to store user data and quiz scores and skip information
- constants.py: Contains constants used throughout the app to avoid magic numbers and hard-coded strings and other values
- utils.py: Contains utility functions used throughout the app. This keeps our other files clean and focused on their specific responsibilities.
- __init__.py: Empty file to make the directory a package.
- tests/*.py: Contains tests for the app. To the extent possible, this tests the acceptance criteria above, as well as any other edge cases we can think of. Tests are named clearly with what they are testing.
- tests/question_banks/*.json: Contains question banks for testing. Includes malformed, empty, and valid question banks of different sizes and with different difficulty and topic distributions.

# Tech Stack
- uv package manager, if any packages are needed
- sqlite3 for the database
- your choice of a reasonable python encryption library for the passwords. Use something standard and reliable
- pytest for testing