# Software Requirements Specification (SRS) for IntelliScan

**Version:** Draft v0.9 - pending owner review  
**Status:** Under Review  
**Target Date:** Phase 1 Presentation (1 Week)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for **IntelliScan**, an open-source, AI-assisted DevSecOps assistant that acts as an intelligent intermediary between a static application security testing (SAST) scanner (Semgrep) and developers to reduce false positive alerts, provide transparent reasoning, and synthesize verified remediation patches.

### 1.2 Scope
IntelliScan targets Python source code (MVP). It executes Semgrep scans, extracts AST-level code context, triages alerts into a 3-way verdict (`TRUE_POSITIVE`, `FALSE_POSITIVE`, `UNCERTAIN`), produces syntax-checked and re-scanned patches, and provides an interactive CLI and a read-only Streamlit dashboard.

### 1.3 Definitions and Acronyms
- **SAST**: Static Application Security Testing.
- **AST**: Abstract Syntax Tree.
- **TP (True Positive)**: A genuine, exploitable security weakness identified in code.
- **FP (False Positive)**: A static analysis alarm triggered on safe or unreachable code.
- **UNCERTAIN**: A borderline finding routed to human review; never silently discarded.
- **Closed-Loop Validation**: Automated syntax parsing followed by a SAST re-scan after patch application.
- **TBD**: To Be Determined (parameter pending empirical measurement).

### 1.4 References
- [AGENTS.md](../AGENTS.md) — Architectural Principles and Coding Standards for IntelliScan.
- [research-notes.md](research-notes.md) — Research synthesis, academic literature, and feasibility analysis.

---

## 2. Overall Description

### 2.1 User Profiles
- **Primary User**: Python software developers and DevSecOps engineers seeking to reduce alert fatigue while routing borderline cases to human review.
- **Secondary User**: Project examiners and academic evaluators auditing triage accuracy and safety mechanisms.

### 2.2 Operating Environment
- **Operating System**: Windows 11 / Windows 10.
- **Runtime Environment**: Python 3.14+ virtual environment (`.venv`).
- **External Tools**: Semgrep CLI (`semgrep`), Git CLI.

### 2.3 Constraints & Assumptions
- **Solo Project**: Development and manual ground-truth labeling are completed by a single developer.
- **LLM Rate Limits & Cost**: Uses free/low-cost tier Gemini API models; LLM responses must be cached to prevent quota exhaustion.
- **Local Execution First**: Scans execute locally; network access is required only for external LLM API calls and registry rule downloads.
- **Scanner Constraints**: Semgrep strictly scans git-tracked files when executing inside a git repository, using community rules only (no login required). Evaluation targets (e.g. PyGoat) are cloned into a separate target workspace outside the project repository (e.g. `C:\dev\targets\pygoat`).

### 2.4 Release Plan (Incremental Delivery)
To deliver a working, defensible project for the Phase 1 presentation within one week, development is phased across three incremental releases:
- **Release 1 (R1 - Core Triage & Evaluation MVP)**: Baseline scanning, AST context extraction, LLM provider interface with caching, 3-way triage, JSON reporting, and full ground-truth evaluation suite. Priority: **Must**.
- **Release 2 (R2 - Interactive Review & Verified Remediation)**: Interactive human review CLI for `UNCERTAIN` alerts, patch generation, two-step closed-loop patch validation (`ast.parse` + Semgrep re-scan), and safe branch-isolated patch application. Priority: **Should**.
- **Release 3 (R3 - Extensibility & Visual Dashboard)**: Remote Git URL adapter, standalone read-only Streamlit web dashboard, and platform portability checks. Priority: **Could**.

---

## 3. Functional Requirements (FR)

### Module 1: Scan Input
#### FR-01: Local Directory Scanning
- **Release**: R1
- **Statement**: The system shall accept a path to a local directory and scan all contained Python source files using the configured SAST rules.
- **Priority**: Must
- **Rationale**: Core MVP input requirement per AGENTS.md (Rule 4).
- **Acceptance Criterion**: Running `intelliscan scan ./path/to/project` completes without errors and returns finding records.

#### FR-02: Git Repository URL Ingestion
- **Release**: R3
- **Statement**: The system shall accept a remote Git repository URL, clone it to a secure temporary directory, and execute the scan pipeline over that directory.
- **Priority**: Could
- **Rationale**: Extensibility adapter requirement per AGENTS.md (Rule 4).
- **Acceptance Criterion**: Running `intelliscan scan https://github.com/org/repo.git` clones to a temp directory and produces identical scan results to a local scan.

---

### Module 2: SAST Adapter
#### FR-03: Semgrep Ingestion & Rule Execution
- **Release**: R1
- **Statement**: The system shall execute Semgrep CLI using rule packs `--config p/python --config p/security-audit --config p/secrets --json` and parse the standard `results` list into internal models.
- **Priority**: Must
- **Rationale**: [research-notes.md Section 4.1](research-notes.md#41-semgrep-json-output-fields).
- **Acceptance Criterion**: Valid JSON is parsed into `check_id`, `path`, line range (`start`, `end`), and `message` attributes.

---

### Module 3: AST Context Extractor
#### FR-04: Function-Level Enclosing AST Extraction
- **Release**: R1
- **Statement**: The system shall parse the target file using Python's standard `ast` module and extract the full source text of the innermost enclosing function containing the alert line.
- **Priority**: Must
- **Rationale**: Literature shows scoped context reduces hallucinations ([research-notes.md Section 3: APPATCH](research-notes.md#paper-5-appatch-automated-adaptive-prompting-large-language-models-for-real-world-software-vulnerability-patching)).
- **Acceptance Criterion**: Given a line inside a `def` or `async def`, the extracted segment matches `ast.get_source_segment` for that node.

#### FR-05: Module-Level Window Fallback (D3)
- **Release**: R1
- **Statement**: The system shall extract a configurable window of $\pm 15$ lines, plus module import statements and file classification (test vs. production), when an alert occurs outside any function.
- **Priority**: Must
- **Rationale**: Owner Decision D3 for global script/config alerts.
- **Acceptance Criterion**: An alert on line 5 of a flat script extracts lines 1 to 20 plus top-level imports with a `test` or `prod` marker.

---

### Module 4: LLM Provider Interface
#### FR-06: Swappable LLM Provider & Caching (D2)
- **Release**: R1
- **Statement**: The system shall interact with LLMs exclusively via an abstract provider interface, record the exact model ID from `.env` in outputs, and cache responses locally.
- **Priority**: Must
- **Rationale**: Owner Decision D2 and AGENTS.md architecture rules.
- **Acceptance Criterion**: Switching provider implementations does not modify core code; repeated identical requests return cached JSON instantly.

---

### Module 5: Triage Engine
#### FR-07: 3-Way Structured Triage Classification
- **Release**: R1
- **Statement**: The system shall prompt the LLM to classify each finding into `TRUE_POSITIVE`, `FALSE_POSITIVE`, or `UNCERTAIN`; if the output is invalid or unparseable, the verdict shall default to `UNCERTAIN`.
- **Priority**: Must
- **Rationale**: Core safety architecture; borderline and unparseable outputs route safely to human review ([research-notes.md Section 2.2](research-notes.md#22-intelliscans-unique-value-proposition)).
- **Acceptance Criterion**: Output parses strictly into a Pydantic schema containing `verdict`, `confidence` (0.0–1.0), and `explanation`, falling back to `UNCERTAIN` on schema failure.

#### FR-08: Transparent Reasoning Generation
- **Release**: R1
- **Statement**: The system shall generate a concise, human-readable step-by-step rationale for why an alert was classified as true, false, or uncertain.
- **Priority**: Must
- **Rationale**: Viva examination and developer auditability requirement (AGENTS.md).
- **Acceptance Criterion**: Every triaged finding contains an explanation string non-empty and accessible in CLI and reports.

---

### Module 6: Review CLI
#### FR-09: Dedicated Interactive Review Command (D4)
- **Release**: R2
- **Statement**: The system shall not prompt interactively during scan runs, but provide an `intelliscan review` command to step through `UNCERTAIN` alerts one by one with context.
- **Priority**: Should
- **Rationale**: Owner Decision D4 to prevent CI blocking while maintaining human review.
- **Acceptance Criterion**: `intelliscan review` displays each uncertain finding, its context, and the LLM rationale, allowing human triage (`TP`/`FP`).

---

### Module 7: Patch Generation & Validation
#### FR-10: Context-Aware Patch Synthesis
- **Release**: R2
- **Statement**: The system shall generate unified diff patches targeting only verified `TRUE_POSITIVE` findings intended to remove the root cause while preserving existing behavior.
- **Priority**: Should
- **Rationale**: Core product pipeline per AGENTS.md.
- **Acceptance Criterion**: Patch text is produced formatted as a valid unified diff applicable via git.

#### FR-11: Two-Step Closed-Loop Patch Validation
- **Release**: R2
- **Statement**: The system shall validate patches via `ast.parse` and Semgrep re-scan; unverified patches failing validation cannot be applied through the patch apply command.
- **Priority**: Should
- **Rationale**: Literature shows unverified LLM patches cause regressions ([research-notes.md Section 6, Finding 4](research-notes.md#6-top-5-findings-that-should-shape-our-requirements)).
- **Acceptance Criterion**: Patches failing syntax check or failing to clear the Semgrep rule are marked `UNVERIFIED` and rejected by `intelliscan patch apply`.

---

### Module 8: Safe Patch Management CLI
#### FR-12: Interactive Patch Review & Approval
- **Release**: R2
- **Statement**: The system shall provide CLI commands (`intelliscan patch list|show|apply|reject`) requiring explicit developer confirmation (`[y/N]`) before applying any patch.
- **Priority**: Should
- **Rationale**: AGENTS.md non-negotiable rule: patches are NEVER auto-applied without human approval.
- **Acceptance Criterion**: No file changes occur without an affirmative interactive user input.

#### FR-13: Dedicated Git Branch Isolation & Undo
- **Release**: R2
- **Statement**: The system shall apply verified patches only on a dedicated new git branch (e.g., `intelliscan/patch-<id>`) and provide an `intelliscan patch undo` command.
- **Priority**: Should
- **Rationale**: AGENTS.md Rule 5 for non-destructive repository operations.
- **Acceptance Criterion**: Applying a patch creates a git branch, commits the change, and `undo` reverts cleanly to the prior HEAD.

---

### Module 9: Reporting & Dashboard
#### FR-14: Comprehensive Machine-Readable JSON Export
- **Release**: R1
- **Statement**: The system shall export full scan and triage outputs to a standardized JSON file including metadata, findings, verdicts, model ID, and execution timestamps.
- **Priority**: Must
- **Rationale**: CLI/Dashboard decoupling rule per AGENTS.md.
- **Acceptance Criterion**: Output JSON validates against the internal `ScanReport` schema.

#### FR-15: Read-Only Streamlit Web Dashboard
- **Release**: R3
- **Statement**: The system shall provide a standalone Streamlit web interface that reads generated JSON reports and visualizes metrics, findings, explanations, and diffs.
- **Priority**: Could
- **Rationale**: Visual auditability for project presentation without coupling to core logic.
- **Acceptance Criterion**: `streamlit run` launches a browser UI displaying report data without importing from `core`.

---

## 4. Non-Functional Requirements (NFR)

#### NFR-01: Reliability & Fault Tolerance
- **Release**: R1
- **Statement**: The system shall retry on API 429/503 errors with exponential backoff and switch to a configured fallback model on repeated failure before falling back to `UNCERTAIN`.
- **Priority**: Must
- **Rationale**: Public LLM APIs experience transient outages and quota bursts ([research-notes.md Section 4.4](research-notes.md#44-operational--security-risks)).
- **Acceptance Criterion**: Repeated mock network failures trigger retries, attempt the fallback model, and safely output `UNCERTAIN` without crashing.

#### NFR-02: Credential Security
- **Release**: R1
- **Statement**: The system shall retrieve all API credentials strictly from environment variables or a gitignored `.env` file, with zero hardcoded secrets.
- **Priority**: Must
- **Rationale**: Standard DevSecOps engineering practice and AGENTS.md standard.
- **Acceptance Criterion**: Automated test fails if API key strings are detected in git-tracked source files.

#### NFR-03: Prompt Injection Mitigation
- **Release**: R1
- **Statement**: The system shall isolate untrusted source code inside explicit structural XML delimiters (`<untrusted_code>`) in prompts to reduce prompt-injection risk (not a guarantee).
- **Priority**: Must
- **Rationale**: Mitigate OWASP LLM01 indirect prompt injection attacks ([research-notes.md Section 4.4](research-notes.md#44-operational--security-risks)).
- **Acceptance Criterion**: Prompt templates enclose code within designated tags accompanied by overriding system instructions.

#### NFR-04: Auditability & Reproducibility
- **Release**: R1
- **Statement**: The system shall record the exact LLM model name, rule configurations, prompt hash, and execution timestamp in every generated result artifact.
- **Priority**: Must
- **Rationale**: Owner Decision D2 and scientific benchmarking reproducibility.
- **Acceptance Criterion**: Every JSON output file contains an intact `metadata` object populated with execution parameters.

#### NFR-05: Architectural Core Isolation
- **Release**: R1
- **Statement**: The system `core/` module shall never import from `cli/` or `dashboard/`, communicating solely via plain data models and JSON serializable structures.
- **Priority**: Must
- **Rationale**: AGENTS.md non-negotiable architectural rule 1.
- **Acceptance Criterion**: Static import linting verifies zero references to `cli` or `dashboard` inside `src/intelliscan/core/`.

#### NFR-06: Maintainability & Code Quality
- **Release**: R1
- **Statement**: The codebase shall maintain type hints on public interfaces, clean linting under `ruff check`, and unit/integration test suites under `pytest`.
- **Priority**: Must
- **Rationale**: Engineering standard for college viva defense (AGENTS.md).
- **Acceptance Criterion**: Running `ruff check` returns zero violations and `pytest` runs cleanly in CI/local terminal.

#### NFR-07: Cost & Quota Management
- **Release**: R1
- **Statement**: The system shall maintain an on-disk cache of LLM responses keyed by code hash and prompt parameters to eliminate duplicate API requests.
- **Priority**: Must
- **Rationale**: Free-tier rate limits and cost control (Owner Decision D2).
- **Acceptance Criterion**: Running a second scan on an unchanged file generates 0 external LLM HTTP calls.

#### NFR-08: Execution Platform Compatibility
- **Release**: R3
- **Statement**: The system shall execute reliably on Windows 10/11 platforms with Python 3.14+ using standard Windows path semantics.
- **Priority**: Could
- **Rationale**: Owner's local operating system and viva environment.
- **Acceptance Criterion**: All test cases pass on Windows without POSIX-only path syntax errors during local test runs.

---

## 5. Evaluation Requirements (EV)

#### EV-01: Ground-Truth Evaluation Corpus (D1)
- **Release**: R1
- **Statement**: The system shall be evaluated against ~50–80 PyGoat alerts labeled using a written guidelines document (`docs/labeling-guidelines.md`) created before labeling, plus test FPs.
- **Priority**: Must
- **Rationale**: Owner Decision D1; lack of pre-existing Python SAST benchmark ([research-notes.md Section 1.2](research-notes.md#12-evaluation-fallback-strategy-recommended-for-intelliscan-mvp)).
- **Acceptance Criterion**: `docs/labeling-guidelines.md` and an evaluation manifest exist with human justifications written before AI testing.

#### EV-02: Core Classification Metrics
- **Release**: R1
- **Statement**: The evaluation suite shall compute Precision, Recall, and F1 treating `UNCERTAIN` as kept in primary metrics, and report a secondary view with `UNCERTAIN` excluded.
- **Priority**: Must
- **Rationale**: High recall is a measured target, not a guarantee; dual-view reporting provides complete transparency ([research-notes.md Section 5.2](research-notes.md#52-mathematical-formulas)).
- **Acceptance Criterion**: `intelliscan evaluate` outputs both primary (UNCERTAIN kept) and secondary (UNCERTAIN excluded) metric tables.

#### EV-03: Noise Reduction Quantification
- **Release**: R1
- **Statement**: The evaluation suite shall compute the False Positive Reduction Rate (FPRR = $TN / (TN + FP)$) with `UNCERTAIN` counted as kept, and report a secondary view excluding `UNCERTAIN`.
- **Priority**: Must
- **Rationale**: Measuring DevSecOps alert filtering value with safety conservatism ([research-notes.md Section 5.2](research-notes.md#52-mathematical-formulas)).
- **Acceptance Criterion**: Evaluation output reports both primary and secondary FPRR percentages.

#### EV-04: Triage Transparency & Uncertain Rate
- **Release**: R1
- **Statement**: The evaluation suite shall report the `UNCERTAIN` classification rate separately, measuring the human review workload required.
- **Priority**: Must
- **Rationale**: Ensuring safety transparency; uncertain findings are preserved for human audit ([research-notes.md Section 5.2](research-notes.md#52-mathematical-formulas)).
- **Acceptance Criterion**: Evaluation reports the exact count and percentage of findings categorized as `UNCERTAIN`.

#### EV-05: Baseline Scanner Comparison
- **Release**: R1
- **Statement**: The evaluation suite shall produce a side-by-side comparison of Semgrep alone versus IntelliScan on the identical benchmark corpus to quantify improvement.
- **Priority**: Must
- **Rationale**: Academic viva requirement to demonstrate net benefit over baseline tool ([research-notes.md Section 5](research-notes.md#5-evaluation-metrics-for-sast-triage)).
- **Acceptance Criterion**: `intelliscan evaluate` prints a comparative table showing raw Semgrep metrics versus IntelliScan triaged metrics.

> **Scope of Recall Note:**
> Recall is strictly evaluated relative to the population of alerts reported by Semgrep (triage-level recall). Vulnerabilities present in the target application that Semgrep misses entirely (scanner false negatives) are outside the scope of IntelliScan's triage engine and listed as an inherent baseline scanner limitation.

---

## 6. Out of Scope / Future Scope

The following capabilities are deliberately excluded from the Phase 1 MVP and documented as future scope:
1. **Multi-Language Support**: Analysis is strictly restricted to Python source code; JavaScript/C/Java are future scope.
2. **Automated Pull Request Merging**: Patches are staged on local git branches; automatic merge into `main` is out of scope.
3. **IDE Plugins**: No VS Code or JetBrains extensions; interaction is confined to CLI and Streamlit dashboard.
4. **Hosted Cloud SaaS**: No multi-tenant cloud service, authentication servers, or external databases.

---

## 7. Traceability Matrix

| Requirement ID | Release | Priority | Source / Basis | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | R1 | Must | AGENTS.md (Rule 4) | Integration Test (`test_cli_scan`) |
| **FR-02** | R3 | Could | AGENTS.md (Rule 4) | Unit Test (`test_git_adapter`) |
| **FR-03** | R1 | Must | Research Notes 4.1 | Unit Test (`test_semgrep_parser`) |
| **FR-04** | R1 | Must | Research Notes 4.2 | Unit Test (`test_ast_enclosing_func`) |
| **FR-05** | R1 | Must | Owner Decision D3 | Unit Test (`test_ast_module_window`) |
| **FR-06** | R1 | Must | Owner Decision D2 | Unit Test (`test_llm_caching`) |
| **FR-07** | R1 | Must | Research Notes 2.2 | Unit Test (`test_triage_verdict_schema`) |
| **FR-08** | R1 | Must | AGENTS.md Standards | Unit Test (`test_triage_explanation`) |
| **FR-09** | R2 | Should | Owner Decision D4 | Integration Test (`test_cli_review`) |
| **FR-10** | R2 | Should | AGENTS.md Pipeline | Unit Test (`test_patch_generation`) |
| **FR-11** | R2 | Should | Research Notes 6 (Finding 4) | Integration Test (`test_closed_loop_rescan`) |
| **FR-12** | R2 | Should | AGENTS.md (Rule 5) | CLI Test (`test_patch_apply_prompt`) |
| **FR-13** | R2 | Should | AGENTS.md (Rule 5) | Integration Test (`test_patch_git_branch`) |
| **FR-14** | R1 | Must | AGENTS.md (Rule 2) | Schema Validation Test (`test_json_report`) |
| **FR-15** | R3 | Could | AGENTS.md Tech Stack | Smoke Test (`test_streamlit_render`) |
| **NFR-01** | R1 | Must | Research Notes 4.4 | Mock Fault Test (`test_llm_retry_backoff`) |
| **NFR-02** | R1 | Must | AGENTS.md Standards | Security Scan / Test (`test_no_hardcoded_keys`) |
| **NFR-03** | R1 | Must | Research Notes 4.4 | Prompt Inspection Test (`test_prompt_delimiters`) |
| **NFR-04** | R1 | Must | Owner Decision D2 | Artifact Inspection Test (`test_report_metadata`) |
| **NFR-05** | R1 | Must | AGENTS.md (Rule 1) | AST Linter Test (`test_no_core_ui_imports`) |
| **NFR-06** | R1 | Must | AGENTS.md Standards | Tool Execution (`pytest`, `ruff check`) |
| **NFR-07** | R1 | Must | Owner Decision D2 | Unit Test (`test_cache_hit_prevents_http`) |
| **NFR-08** | R3 | Could | Operating Environment | Local test run (`test_windows_paths`) |
| **EV-01** | R1 | Must | Owner Decision D1 | Dataset Validation (`test_eval_manifest`) |
| **EV-02** | R1 | Must | Research Notes 5.2 | Evaluation Run (`test_metric_calculations`) |
| **EV-03** | R1 | Must | Research Notes 5.2 | Evaluation Run (`test_fprr_calculation`) |
| **EV-04** | R1 | Must | Research Notes 5.2 | Evaluation Run (`test_uncertain_rate`) |
| **EV-05** | R1 | Must | Research Notes 5 | Evaluation Run (`test_baseline_comparison`) |

---

## 8. Risks and Mitigations

| Risk Description | Severity | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Suppression Bias (Accidental False Negative)** | High | Medium | Prompt calibrated for a high-recall target; borderline and unparseable findings default to `UNCERTAIN` for human review (FR-07). |
| **LLM Quota Exceeded (HTTP 429)** | High | Medium | Enforce disk caching (NFR-07), request throttling, and exponential backoff retry with model fallback (NFR-01). |
| **LLM Service Availability (Outages / HTTP 503)** | High | Medium | Implement retry with backoff, secondary fallback model, and fail-safe `UNCERTAIN` classification (NFR-01). |
| **Labeling Bias (Single Human Labeler)** | Medium | High | Author explicit written guidelines (`docs/labeling-guidelines.md`) prior to labeling, label blind to AI outputs, and document results as indicative (D1, EV-01). |
| **Semgrep Registry Network Dependency** | Medium | Medium | Cache Semgrep rule definitions locally in offline-compatible rule sets to avoid runtime download failures during scans (FR-03). |
| **Hallucinated or Breaking Patches** | High | Medium | Enforce two-step closed-loop verification (`ast.parse` + Semgrep re-scan) before offering any patch (FR-11). |
| **Indirect Prompt Injection in Comments** | Medium | Low | Wrap untrusted code in XML tags (`<untrusted_code>`) with strict system prompt authority instructions (NFR-03). |
| **Small Evaluation Sample Size (~50–80 alerts)** | Medium | High | Explicitly document results as indicative and preliminary in academic viva presentation (D1 / EV-01). |
