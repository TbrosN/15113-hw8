# LeetCode Strategy Quiz CLI

A small Python CLI for practicing LeetCode the way you would talk through an interview: by naming the right high-level approach, data structure, or pattern instead of writing full code.

Built for `15-113` at CMU.

## What It Does

- quizzes you on LeetCode-style problems from a local question bank
- lets you filter by difficulty and topic
- supports login, saved scores, and permanent skips
- focuses on strategy-level thinking rather than full implementations

## Project Story

This project was built with a multi-agent workflow: I wrote the spec manually, Agent 1 implemented it, Agent 2 reviewed it, and then I iterated with a mix of manual fixes and AI-assisted improvements.

## Run It

```bash
uv sync
uv run python main.py
```

## Run Tests

```bash
uv run pytest
```
