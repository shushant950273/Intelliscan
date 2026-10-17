# ADR 0002: Encapsulation of Semgrep Behind a SastScanner Interface

## Context
IntelliScan relies on Semgrep CLI to execute static analysis over Python source code. However, hardcoding direct `subprocess.run(["semgrep", ...])` calls across the pipeline tightly couples the system to a single tool. Software engineering standards and project requirements demand that external dependencies sit behind an interface so alternative analyzers (e.g., Bandit, CodeQL, or custom rule engines) can be integrated in future releases or mocked during testing.

## Decision
We define an abstract base interface `SastScanner` in `core/scanner/base.py` defining:
```python
def scan(target_path: Path, rule_packs: list[str]) -> list[Finding]: ...
def is_available() -> bool: ...
```
The concrete implementation `SemgrepScanner` invokes the Semgrep binary with rule packs `--config p/python --config p/security-audit --config p/secrets --json`, parses raw output into normalized `Finding` objects, and handles execution errors. All pipeline modules depend strictly on `SastScanner`.

## Alternatives Considered
- **Direct Subprocess Invocations in Triage Engine**: Calling `semgrep` inline whenever a scan is needed. *Rejected* because it eliminates test mockability and tightly couples domain logic to Semgrep's JSON format.
- **Using Semgrep Python Library Directly**: Importing `semgrep` as an internal Python module. *Rejected* because the Semgrep Python API is internal, unstable across releases, and officially superseded by the CLI JSON interface.

## Consequences
- **Positive**: Enables zero-subprocess mock testing via `MockScanner` in pytest; allows future multi-scanner aggregation without touching the triage engine.
- **Negative**: Requires mapping Semgrep-specific metadata fields to an internal normalized `Finding` model.
