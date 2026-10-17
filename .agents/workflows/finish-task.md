---
description: 
---

# finish-task
Run this after completing any task:
1. Run `pytest` and `ruff check`. Report results honestly, including failures.
2. Append an entry to docs/learning-log.md: what was built, why this design, how it works in simple Hinglish, and 3 viva questions with answers.
3. Update any affected docs (SRS.md, design.md, README.md).
4. Show me the `git status` and suggest a conventional commit message. Do NOT commit; wait for my approval.

/finish-task
In the learning-log entry, correct these claims: 
(1) Uncertain reduces but does not eliminate false negatives; 
(2) the 94-98% FP reduction is from a Tencent industrial study and is not generalizable to our setup; (3) structured JSON output guarantees format, not correctness.