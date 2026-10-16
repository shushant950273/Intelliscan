# IntelliScan: Agent Instructions

## Project
IntelliScan is an open-source DevSecOps assistant. It sits between a SAST scanner (Semgrep) and the developer: it filters false positives using an LLM, explains its verdicts, and generates verified patches.

Pipeline: scan -> context extraction (AST) -> 3-way triage (TP/FP/Uncertain) -> patch generation -> validation (syntax check + re-scan) -> report/dashboard.

## Owner context (IMPORTANT)
This is a final-year college project. The owner must fully understand every line, because it will be examined in a viva. Therefore:
- Work on ONE module/task at a time. Never build the whole project in one go.
- Before writing code, state the plan in 5-8 lines and wait for my approval.
- After writing code, explain it in simple Hinglish: what it does, why this design, and 3 likely viva questions with answers.
- Use simple, readable code over clever code. No unnecessary abstractions.

## Tech stack
- Python 3.11+, package layout under src/intelliscan/
- Semgrep (SAST), Python `ast` module (context extraction)
- LLM access ONLY through the provider interface in core/llm/ (swappable)
- CLI: typer | Dashboard: Streamlit | Tests: pytest | Lint: ruff

## Architecture rules (non-negotiable)
1. core/ must NEVER import from cli/ or dashboard/. Core has no UI code.
2. cli/ and dashboard/ only call core/ and read its JSON output.
3. Every external dependency (Semgrep, LLM) sits behind an interface so it can be replaced later (extensibility is a project requirement).
4. Inputs: local folder (MVP), Git URL later via an adapter that clones to a temp folder and then uses the same local-path pipeline.
5. Patches are NEVER auto-applied. Only verified patches, only after explicit human approval via the CLI, on a separate git branch.
6. Uncertain verdicts go to human review. Never silently discard an alert.

## Engineering standards
- Type hints and short docstrings on all public functions.
- Every module ships with pytest tests in tests/ (happy path + edge case).
- No secrets in code. API keys come from environment variables (.env, gitignored).
- Small commits, conventional messages: feat:, fix:, docs:, test:, refactor:.
- Significant design choices get a short ADR in docs/adr/ (context, decision, alternatives, consequences).

## Documentation standards
- Keep docs/ updated in the same task as the code change.
- docs/learning-log.md: after every task add an entry: what was built, why, how it works (simple words), viva Q&A.
- Requirements use IDs (FR-1, NFR-1) so tests and design can trace back to them.

## Definition of Done (every task)
- [ ] Code runs and the owner has run it personally
- [ ] Tests pass (`pytest`) and `ruff check` is clean
- [ ] Docs + learning-log updated
- [ ] Changes committed

## Out of scope for MVP
Multi-language support, VS Code extension, hosted SaaS, auto-merge of patches. (These are documented as future scope.)
