---
description: After finishing a task, run tests and lint, update the learning log and docs, and suggest a commit message
---

# finish-task
Run this after completing any task:
1. Run `pytest` and `ruff check`. Report results honestly, including failures.
2. Append an entry to docs/learning-log.md: what was built, why this design, how it works in simple Hinglish, and 3 viva questions with answers.
3. Update any affected docs (SRS.md, design.md, README.md).
4. Show me the `git status` and suggest a conventional commit message. Do NOT commit; wait for my approval.
5. Accuracy rule for viva answers: never claim zero false negatives or 100% guarantees, and never state a number without a source or without marking it as an estimate.