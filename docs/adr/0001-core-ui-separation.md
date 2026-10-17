# ADR 0001: Strict Separation of Core Domain and Presentation Layers

## Context
IntelliScan requires both a developer CLI interface (built with Typer) and a visual web dashboard (built with Streamlit) to display security findings and triage results. In educational and production systems alike, domain logic frequently becomes coupled to UI frameworks (e.g., embedding CLI `typer.echo` or `streamlit.write` calls directly inside analysis functions). This coupling prevents automated headless testing, blocks CI/CD integration, and complicates viva code examinations.

## Decision
We enforce a strict one-way architectural dependency:
1. `src/intelliscan/core/` contains pure domain models and pipeline logic. It must **never** import from `src/intelliscan/cli/` or `src/intelliscan/dashboard/`.
2. `core/` communicates with consumers exclusively via standard Python dataclasses/Pydantic models and structured JSON artifacts.
3. An automated AST linter test (`test_no_core_ui_imports`) runs in CI and `pytest` to guarantee zero presentation imports inside core.

## Alternatives Considered
- **Direct CLI Calls in Core**: Having core functions print progress bars and prompt for inputs directly. *Rejected* because it breaks headless execution, prevents programmatic library usage, and pollutes unit testing output.
- **Shared UI Helper Layer**: Placing a generic UI adapter inside core. *Rejected* because it introduces unnecessary abstractions when returning plain data models already solves the problem cleanly.

## Consequences
- **Positive**: Clean unit testability; core can be imported into CLI, web dashboard, or future CI/CD actions without refactoring; zero circular imports.
- **Negative**: Presentation layers must handle formatting and rendering of returned data models explicitly, requiring slightly more boilerplate in CLI handlers.
