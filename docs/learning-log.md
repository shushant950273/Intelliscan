# IntelliScan: Learning Log

This log chronicles the step-by-step progress, architectural rationale, simple explanations, and viva defense preparation for the **IntelliScan** project.

---

## Entry 1: Project Skeleton & Architecture Setup

### 1. What Was Built
- Established the official package repository layout under `src/intelliscan/` separated into three isolated layers: `core/`, `cli/`, and `dashboard/`.
- Authored the project constitution in [AGENTS.md](../AGENTS.md), codifying non-negotiable architectural constraints, coding standards, definition of done, and viva-focused engineering workflows.
- Set up standard project hygiene: `.gitignore`, `pyproject.toml`, and initial directory stubs (`docs/`, `tests/`, `scripts/`).

### 2. Why This Design
- **Strict Layer Decoupling**: Rule 1 of AGENTS.md enforces that `core/` must never import from `cli/` or `dashboard/`. Core holds pure DevSecOps domain logic (AST context, triage classification, patch validation). Decoupling UI ensures that interfaces can be completely swapped (e.g., adding a GitHub Action or VS Code extension) without touching core logic.
- **Viva Defensibility**: In a final-year viva, examiners probe architectural separation and modularity. An unentangled core prevents circular dependencies and enables clean unit testing.

### 3. How It Works (Simple Hinglish)
> Humne project ka basic structure banaya jisme teen alag-alag compartments hain: `core/` (jo asli kaam karta hai jaise code parse karna aur LLM se baat karna), `cli/` (terminal user interface), aur `dashboard/` (web visual UI). Rule yeh hai ki `core/` ko bilkul nahi pata hona chahiye ki bahar CLI chal raha hai ya Web UI. Core sirf plain data aur JSON me baat karta hai. Isse hamara code modular banta hai aur viva me explain karna super easy ho jata hai.

### 4. Likely Viva Questions & Answers
- **Q1: `core/` module ko `cli/` aur `dashboard/` se strictly isolated kyun rakha gaya hai?**  
  *Answer*: Separation of Concerns principle ke liye. Agar core UI par depend karega toh headless CI/CD pipelines me run nahi ho payega aur automated unit testing mushkil ho jayegi. Core sirf data process karta hai aur CLI/UI sirf presentation handle karte hain.
- **Q2: Circular dependency se bachne ke liye layout me kya rules hain?**  
  *Answer*: Dependency hierarchy hamesha top-down rehti hai: `cli/` $\rightarrow$ `core/` aur `dashboard/` $\rightarrow$ `core/`. Core kabhi reverse import nahi karta.
- **Q3: `pyproject.toml` ka role kya hai compared to requirements.txt?**  
  *Answer*: Modern Python packaging standards (PEP 517/518/621) ke anusaar `pyproject.toml` project metadata, build systems, dependency specifications, aur tools configuration (jaise `ruff`, `pytest`) ko ek single standard file me centralize karta hai.

---

## Entry 2: Development Environment Setup

### 1. What Was Built
- Initialized a Python virtual environment (`.venv`) on Windows running Python 3.14.
- Installed core dependencies: `typer` (CLI), `streamlit` (dashboard), `google-genai` (official Google GenAI SDK for Gemini), `pydantic` (data validation), `ruff` (linter/formatter), and `pytest` (test framework).
- Configured `.env` template (`.env.example`) for secure local secret management.

### 2. Why This Design
- **Isolated Hermetic Environment**: Isolates third-party packages from the global operating system, preventing version drift.
- **Zero Secrets in Code**: API keys and model configurations are injected strictly at runtime via environment variables (`.env`, which is gitignored).

### 3. How It Works (Simple Hinglish)
> Ek local `.venv` banaya gaya taaki hamare project ki libraries Windows ke main system se alag rahein. Sabhi libraries (`typer`, `google-genai`, `pytest`, `ruff`) install kiye gaye. Humne ek `.env.example` file banayi jo batati hai ki Gemini API key aur model ID kaise configure karni hai, jabki actual `.env` file git me ignore rehti hai taaki koi secret leak na ho.

### 4. Likely Viva Questions & Answers
- **Q1: Virtual environment use karne ka technical benefit kya hai?**  
  *Answer*: Dependency isolation ensure karta hai. Agar system par multiple Python projects alag-alag library versions chahte hain, toh virtual environment ensure karta hai ki IntelliScan ke dependencies bina version conflict ke independently run karein.
- **Q2: Production me API keys manage karne ka standard best practice kya hai?**  
  *Answer*: Secrets ko kabhi git repository me commit nahi kiya jata. Unhe Twelve-Factor App methodology ke anusaar runtime environment variables ya cloud secrets manager se load kiya jata hai.
- **Q3: Ruff ko traditional linters (Flake8, Black, isort) ke upar kyun choose kiya gaya?**  
  *Answer*: Ruff Rust me likha gaya extremely fast linter/formatter hai jo Flake8, Black, aur isort ko replace karta hai, jisse CI aur local linting execution seconds ke fraction me complete ho jati hai.

---

## Entry 3: Smoke Tests (Gemini API & Semgrep SAST)

### 1. What Was Built
- Created `scripts/vuln_sample/app.py` containing sample Python patterns: SQL injection via string concatenation, dangerous `eval()`, and a test credential string.
- Created `scripts/smoke_llm.py` to test the official `google-genai` SDK and verify API connectivity with Gemini.
- Executed Semgrep CLI against the sample application with rule packs `--config p/python --config p/security-audit --config p/secrets --json` and captured the output in `scripts/semgrep_out.json`.

### 2. Why This Design
- **Fail-Fast Validation**: Before building complex pipeline wrappers, smoke tests prove that external components (Semgrep CLI and the LLM API) execute cleanly in the developer's local runtime.
- **Understanding Output Schemas**: Inspecting raw Semgrep output and LLM responses provided the concrete schema definitions required for our Pydantic parser.

### 3. How It Works (Simple Hinglish)
> Humne ek sample code (`app.py`) banaya jisme janboojhkar vulnerable patterns dale. Phir do smoke tests chalaye:
> 1. `smoke_llm.py`: Isne Gemini model ko ek simple prompt bheja aur check kiya ki API key aur SDK properly respond kar rahe hain ya nahi.
> 2. `semgrep scan`: Isne local machine par Semgrep chala kar JSON report (`semgrep_out.json`) produce ki.
> Jab humne `scripts/semgrep_out.json` ko inspect kiya, toh dekha ki us run me `results: []` me 0 findings record hui thi (jo specific prefiltering/ruleset flags ka outcome tha). Isse hume pata chala ki Semgrep ke rule packs aur matching behavior ko carefully specify karna zaroori hai.

### 4. Likely Viva Questions & Answers
- **Q1: Gemini API keys ka naya format kya hai aur authentication me kya common issue dekha gaya?**  
  *Answer*: Google AI Studio ke naye official API keys ka format `AQ.` prefix se shuru hota hai (yeh standard API key hai, OAuth token nahi). Shuru me kuch users ko `401 ACCESS_TOKEN_TYPE_UNSUPPORTED` error dekhne ko mila tha jab client libraries ne naye token headers ko galat parse kiya, aur `503` errors transient server overload ki wajah se aaye the.
- **Q2: Semgrep CLI ka exit code aur JSON structure kaisa hota hai?**  
  *Answer*: Semgrep findings ko top-level `results` array me deliver karta hai. Har finding me `check_id`, `path`, `start`, `end`, aur `extra` (message, severity, metavars) structured milte hain, jise directly parse kiya ja sakta hai.
- **Q3: Smoke testing ka automated pipelines me kya role hota hai?**  
  *Answer*: Smoke testing shallow integration check hoti hai jo ensure karti hai ki underlying environment (binary paths, network access, environment variables) functional hai, taaki downstream complex tests misleading false errors na dein.

---

## Entry 4: Research Phase & Literature Analysis

### 1. What Was Built
- Authored a comprehensive research report in [docs/research-notes.md](research-notes.md) evaluating benchmarks, commercial tools, academic papers, feasibility, and triage metrics.
- Evaluated benchmarks: Confirmed that **OWASP Benchmark Java** is strictly Java-only; **OWASP Benchmark Python** (`BenchmarkPython`) is in early v0.1 stage; and **OWASP PyGoat** contains challenges but lacks per-finding SAST ground-truth labels.
- Analyzed 5 recent academic papers (2024–2026): Xiong & Zhang (arXiv:2601.22952 on LLM agents for SAST FPs), Tencent's study on `BkCheck` (arXiv:2601.18844, accepted to ICSE-SEIP), ZeroFalse (arXiv:2510.02534 on flow contracts), IRIS (arXiv:2405.17238), and APPATCH (arXiv:2408.13597, USENIX Security 2025 on automated patch generation).

### 2. Why This Design
- **Grounded Evidence**: Grounding project requirements in empirical literature avoids unscientific assumptions.
- **Safety Calibration**: Replaced absolute claims like "zero false negatives" with a scientifically accurate **high-recall target, measured and reported; not guaranteed**. The literature clearly shows "suppression bias" as a measured failure mode in LLM triage.
- **D1 Evaluation Fallback**: Because no off-the-shelf Python benchmark maps Semgrep finding IDs to TP/FP labels, we designed a ground-truth fallback using ~50–80 Semgrep findings from PyGoat, labeled blind to AI outputs under pre-written guidelines.

### 3. How It Works (Simple Hinglish)
> Humne internet aur academic research papers me pata kiya ki kya Python ke liye ready-made SAST ground truth dataset available hai. Pata chala ki OWASP Benchmark Java mature hai, par Python benchmark abhi adhoora hai. PyGoat vulnerable app hai par usme Semgrep ke per-finding labels nahi hain. Isliye humne decide kiya ki hum PyGoat ko Semgrep se scan karke ek manual ground truth JSON khud prepare karenge. Academic papers (Tencent BkCheck aur ZeroFalse) se confirm hua ki LLMs 90%+ false positives reduce kar sakte hain, par agar safety bounds na ho toh real vulnerability suppress hone ka risk rehta hai.

### 4. Likely Viva Questions & Answers
- **Q1: Triage filter ke liye Precision aur Recall ka kya formula hai aur trade-off kya hota hai?**  
  *Answer*: Precision $= TP / (TP + FP)$ (retained alerts me kitne real bugs hain) aur Recall $= TP / (TP + FN)$ (real bugs me se kitne preserve hue). Security me Recall sabse critical hota hai kyunki False Negative ($FN$) ka matlab hai ki system ne ek real vulnerability ko safe samajh kar drop kar diya.
- **Q2: Tencent ke industrial study (`BkCheck`) ka main finding kya tha?**  
  *Answer*: Tencent ke 433 real alarms ke empirical study me dekha gaya ki hybrid static analysis + LLM approach ne 94% se 98% false positives eliminate kiye, aur developer ka manual review time (10–20 mins per alarm) kam karke negligible token cost ($0.0011–$0.12) me execute hua.
- **Q3: IntelliScan me 3-way triage (`TRUE_POSITIVE`, `FALSE_POSITIVE`, `UNCERTAIN`) binary triage se superior kyun hai?**  
  *Answer*: Binary classifiers borderline findings par guess karte hain, jisse real vulnerabilities suppress ho sakti hain. IntelliScan ambiguity detect hote hi `UNCERTAIN` mark karta hai aur alert ko human triage queue me bhej deta hai, jisse safety preserve rehti hai.

---

## Entry 5: Lean Software Requirements Specification (SRS)

### 1. What Was Built
- Authored the formal Software Requirements Specification in [docs/SRS.md](SRS.md) (Draft v0.9).
- Kept strictly lean for the Phase 1 presentation: 15 Functional Requirements (FR-01 to FR-15), 8 Non-Functional Requirements (NFR-01 to NFR-08), and 5 Evaluation Requirements (EV-01 to EV-05).
- Designed an incremental release plan:
  - **Release 1 (R1 - Must)**: Core triage engine, AST extractor, caching, reporting, and ground-truth evaluation.
  - **Release 2 (R2 - Should)**: Interactive review CLI (`intelliscan review`), patch synthesis, closed-loop re-scan, and safe git branch patch management.
  - **Release 3 (R3 - Could)**: Remote Git URL adapter, Streamlit dashboard, and cross-platform verification.
- Embedded Owner Decisions (D1: written labeling guidelines + indicative sample; D2: fixed model ID from `.env` + caching; D3: $\pm 15$ line module fallback; D4: non-blocking scan with separate review CLI).

### 2. Why This Design
- **Presentation Defensibility**: Dividing requirements into R1/R2/R3 gives clear milestones and prevents over-promising before the one-week presentation deadline.
- **Dual-View Evaluation Metrics**: Primary metrics treat `UNCERTAIN` conservatively as "kept" (no automated reduction credit, ensuring safety), while a secondary view reports metrics excluding `UNCERTAIN` to analyze pure classifier precision.
- **Traceability**: Every requirement links back to AGENTS.md, Research Notes, or Decisions D1–D4 with a concrete test verification method.

### 3. How It Works (Simple Hinglish)
> Humne SRS document likha jo define karta hai ki system kya karega. Time constraint ko dhyan me rakhte hue humne 15 functional requirements banaye aur unhe teen releases me baanta. R1 hamara main MVP hai jo scan karke triage aur metrics nikalega. R2 me patch generation aur closed-loop Semgrep re-scan aayega. R3 me web dashboard aur Git URL support aayega. Requirements me humne explicitly likha ki agar LLM output corrupt ho toh verdict automatically `UNCERTAIN` ban jayega, aur patch tabhi apply hoga jab woh `ast.parse` syntax check aur Semgrep re-scan dono pass kar le.

### 4. Likely Viva Questions & Answers
- **Q1: Requirement FR-11 (Closed-Loop Validation) patch application me kaise safety ensure karta hai?**  
  *Answer*: Yeh two-step verification gate hai: Pehle `ast.parse` check karta hai ki patch ne koi syntax error introduce toh nahi kiya. Phir Semgrep re-scan run hota hai yeh verify karne ke liye ki original security alert genuinely resolve hua hai aur koi naya SAST finding create nahi hua. Jo patch dono pass nahi karta, use CLI reject kar deta hai.
- **Q2: Evaluation me dual-view metrics (EV-02/EV-03) kyun report kiye jate hain?**  
  *Answer*: Primary view `UNCERTAIN` ko "kept" manta hai taaki developer workload ka realistic assessment mile aur false negative suppression risk na ho. Secondary view `UNCERTAIN` ko exclude karke model ke pure True Positive vs False Positive discrimination power ko isolate karke measure karta hai.
- **Q3: Ground-truth labeling me bias rokne ke liye EV-01 me kya deliverable mandatory banaya gaya?**  
  *Answer*: `docs/labeling-guidelines.md` ek pre-written standard document hai jisme explicit criteria define hote hain ki kaunse patterns TP honge aur kaunse FP. Labeling AI ka output dekhe bina (blind evaluation) ki jati hai taaki human confirmation bias reduce ho sake.

---

## Entry 6: System Design & Architecture Decision Records (ADRs)

### 1. What Was Built
- Authored [docs/design.md](design.md) detailing the Release 1 (R1) architecture, Mermaid sequence flows, module breakdown under `src/intelliscan/`, data models (`Finding`, `CodeContext`, `TriageResult`, `ScanReport`), abstract interface signatures, and requirements coverage.
- Authored four formal Architecture Decision Records in `docs/adr/`:
  - [ADR 0001](adr/0001-core-ui-separation.md): Strict separation of core domain logic from UI presentation layers.
  - [ADR 0002](adr/0002-sast-scanner-interface.md): Encapsulation of Semgrep behind an abstract `SastScanner` interface.
  - [ADR 0003](adr/0003-llm-provider-interface-cache-retry.md): `LLMProvider` interface with composite-key disk caching, exponential retry backoff, model fallback, and never-cache-failures policy.
  - [ADR 0004](adr/0004-three-way-triage-uncertain-handling.md): 3-Way triage classification with conservative `UNCERTAIN` fallback handling.

### 2. Why This Design
- **Separation of Concerns**: Core domain code remains 100% free of CLI/dashboard imports, making it independently testable and headless-compatible.
- **Fail-Safe Robustness**: Caching composite keys (`SHA256(context_hash + template_version + model_id + rule_id)`) prevents stale responses, while the never-cache-failures rule prevents transient 429/503 errors from permanently freezing findings into `UNCERTAIN`.
- **Defensible Viva Design**: ADRs document alternatives considered and technical trade-offs, providing ready-made rationale for academic examination.

### 3. How It Works (Simple Hinglish)
> Humne system ka complete blueprint banaya. `core/` bilkul alag rahega aur CLI ya Streamlit se direct dependency nahi rakhega. Semgrep ko direct chalane ke bajaye humne ek `SastScanner` interface banaya taaki tests me hum mock scanner chala sakein. LLM ke aage ek `CachedLLMProvider` lagaya jo prompt aur model ka hash banakar disk par store karta hai—par agar network fail ho ya output corrupt ho, toh use cache nahi karta taaki agle run me retry ho sake. Agar koi bhi failure aaye, toh system crash nahi hota, seedha safe `UNCERTAIN` de deta hai.

### 4. Likely Viva Questions & Answers
- **Q1: Composite cache key me prompt template version aur rule ID include karne ka kya specific reason hai?**  
  *Answer*: Cache consistency guarantee karne ke liye. Agar hum prompt template me system instructions improve karte hain ya rule definition change hoti hai, toh purana cached response invalid ho jana chahiye. Composite hash ensure karta hai ki template ya model badalte hi automatically fresh API response fetch ho.
- **Q2: Transient errors (jaise HTTP 503 ya unparseable responses) ko cache me store kyun nahi kiya jata?**  
  *Answer*: Failures are never cached rule ke tahat. Agar server busy hone par aaye 503 error ya partial JSON response ko hum disk par `UNCERTAIN` cache kar lenge, toh agle run me network theek hone ke bawajood system live API call nahi karega aur finding hamesha ke liye `UNCERTAIN` freeze ho jayegi.
- **Q3: Design me structured outputs ke sath Pydantic model enforce karne ka kya benefit hai?**  
  *Answer*: Structured JSON mode format adherence guarantee karta hai (valid JSON with correct keys), jisse string regex parsing ki zaroorat khatam ho jati hai aur parser crashes eliminate hote hain. Note: yeh format guarantee karta hai, verdict ki logical security correctness guarantee nahi karta.

---

## Entry 7: OWASP PyGoat Baseline Semgrep Scan & Analysis

### 1. What Was Built
- Cloned the target evaluation repository [OWASP PyGoat](https://github.com/adeyosemanputra/pygoat) into an external workspace folder (`C:\dev\targets\pygoat`) outside IntelliScan's own repository.
- Executed Semgrep CLI across PyGoat using the three standard rule packs:
  `semgrep scan --config p/python --config p/security-audit --config p/secrets --json --output results/pygoat_3packs.json C:\dev\targets\pygoat`
- Inspected and verified the resulting baseline findings in `results/pygoat_3packs.json`:
  - **Total Scanned Files**: 267 files across the PyGoat repository.
  - **Total Findings**: Exactly **84 findings** identified.
  - **File Type Distribution**: 75 findings in `.py` source files, 9 findings in `.html` template files.
  - **Top File Locations**: `views.py` (45 findings), `mitre.py` (10 findings), `apis.py` (8 findings), `app.py` (5 findings), `main.py` (5 findings).
  - **Top Rule Families**: `@csrf_exempt` (25 findings), `secure-cookies` (12 findings across Django & Flask), `template-unescaped-with-safe` (7 findings), `avoid-pickle` & deserialization (6 findings), `request-data-write` & SQLi (6 findings), MD5 hashing (6 findings), `eval()` & command execution (8 findings).

### 2. Why This Design
- **External Evaluation Workspace**: Targets must never be cloned inside the assistant's own repository to prevent external vulnerable files from contaminating project linting, testing, or repository indexing.
- **Understanding Baseline Scanner Distribution**: Analyzing the 84 findings reveals that `@csrf_exempt` represents ~30% (25/84) of all alerts, proving that stratified per-rule-family evaluation is necessary to avoid metric skew.
- **Critical Scanner Lesson**: In our earlier smoke test on `scripts/vuln_sample`, Semgrep produced only 1 finding because Semgrep OSS strictly scans files tracked by Git when run inside a repository and misses patterns outside its active rule definitions.

### 3. How It Works (Simple Hinglish)
> Humne OWASP PyGoat ko ek alag folder (`C:\dev\targets\pygoat`) me clone kiya aur uspar Semgrep ke teeno rule packs chalaye. Semgrep ne 267 files scan karke total 84 findings report kiye. Isme se 75 findings Python files me the aur 9 findings HTML templates me the. Sabse zyada findings `views.py` (45) me mile. Sabse common alert `@csrf_exempt` (25 findings) ka tha. Is scan se hume pata chala ki Semgrep git-tracked files hi scan karta hai aur rulesets ke pattern par heavily depend karta hai.

### 4. Likely Viva Questions & Answers
- **Q1: Semgrep scan me target repository ko alag folder me kyun clone kiya gaya?**  
  *Answer*: Hermetic project workspace maintain karne ke liye. Agar hum vulnerable app (PyGoat) ko IntelliScan ke apne repo me clone karte, toh hamare local linting (`ruff check`) aur testing (`pytest`) me vulnerable test files mix ho jate.
- **Q2: PyGoat scan me `@csrf_exempt` itna dominant (25 of 84) kyun hai aur iska evaluation par kya asar padta hai?**  
  *Answer*: PyGoat educational tool hai jisme multiple lab exercises me testing ko simple banane ke liye views par `@csrf_exempt` lagaya gaya hai. Evaluation me agar hum sirf aggregate precision dikhayenge, toh yeh akela rule 30% weight rakhega, isliye per-rule family breakdown dikhana zaroori hai.
- **Q3: Semgrep execution me git tracking ka kya impact dekha gaya?**  
  *Answer*: Semgrep CLI jab kisi git repository ke andar run hota hai, toh by default sirf git-tracked files scan karta hai. Untracked files skip ho jati hain. Isliye accurate benchmarking ke liye target repository clean aur committed git state me hona chahiye.

---

## Entry 8: Ground-Truth Labeling Guidelines (EV-01)

### 1. What Was Built
- Authored the formal labeling guidelines in [docs/labeling-guidelines.md](labeling-guidelines.md) satisfying requirement **EV-01**.
- Established core evaluation definitions: `TRUE_POSITIVE`, `FALSE_POSITIVE`, and `AMBIGUOUS`.
- Designed a generic 5-step decision checklist: Locate & Scope $\rightarrow$ Taint Trace $\rightarrow$ Verify Sanitizers $\rightarrow$ Environment Inspection $\rightarrow$ Final Adjudication.
- Detailed specific check criteria, TP triggers, and FP triggers for the top rule families extracted from `results/pygoat_3packs.json`.
- Established bias controls: written protocol pre-dating manual triage, blind evaluation without viewing AI output, and temporal consistency re-labeling of 15 samples after $\ge 3$ days.

### 2. Why This Design
- **Reducing Confirmation Bias**: Assigning labels before and without seeing model verdicts ensures that the human ground truth is not swayed by the LLM's persuasive explanations.
- **Grounded in Actual Code Context**: Exploit walkthroughs in `Solutions/solution.md` serve only as an exploratory hint; an alert is labeled `TRUE_POSITIVE` only if the vulnerability is demonstrably present in that specific line/code block.
- **Transparent Handling of Ambiguity**: `AMBIGUOUS` findings are tracked and reported by count; an `UNCERTAIN` verdict from IntelliScan on an `AMBIGUOUS` finding is treated as an acceptable, aligned outcome.

### 3. How It Works (Simple Hinglish)
> Humne 84 Semgrep findings ko manually label karne ke liye ek standard checklist (`labeling-guidelines.md`) banayi. Rule yeh hai ki hum AI ka output dekhe bina blind labeling karenge. PyGoat ke `solution.md` ko sirf hint ki tarah use karenge, par actual label code verify karke hi denge. Agar code me weakness genuinely exploitable hai toh `TRUE_POSITIVE`, agar input constant/safe hai toh `FALSE_POSITIVE`, aur agar context adhoora ho toh `AMBIGUOUS`. Agar AI bhi kisi `AMBIGUOUS` alert par `UNCERTAIN` bolega, toh use aligned maana jayega.

### 4. Likely Viva Questions & Answers
- **Q1: Ground truth create karte waqt 'Blind Labeling' kyun zaroori hai?**  
  *Answer*: Confirmation bias reduce karne ke liye. LLMs bohot convincing aur persuasive explanations generate karte hain. Agar evaluator pehle AI ka verdict dekh lega, toh subconscious bias ki wajah se woh AI ke answer se agree karne lagega, jisse independent evaluation invalid ho jayegi.
- **Q2: PyGoat ke `solution.md` ko absolute ground truth ki jagah sirf 'hint' kyun consider kiya gaya?**  
  *Answer*: PyGoat challenges pure application-level vulnerabilities describe karte hain, jabki Semgrep alerts specific lines of code par trigger hote hain. Ek vulnerable view ke andar bhi kuch specific alerts (jaise harmless debug setting ya non-sensitive cookie) safe ho sakte hain. Isliye specific finding ka code context verify karna mandatory hai.
- **Q3: Single-labeler study me Inter-Rater Reliability ko approximate karne ke liye kya protocol banaya gaya?**  
  *Answer*: Temporal consistency test. Initial labeling ke 3 din baad, evaluator 15 random findings ko dobara blind re-label karega aur dono passes ke beech percentage agreement calculate karega. High agreement rate consistent technical decision-making ko demonstrate karta hai.

---

## Mistakes & Engineering Lessons Learned

1. **Accidental API Key Exposure in Screenshots (Rotated)**:
   - *What Happened*: During early environment setup, an API key was inadvertently visible in a terminal capture screenshot.
   - *Lesson & Fix*: The compromised API key was immediately deleted and rotated in Google AI Studio. Moving forward, sensitive `.env` files are strictly gitignored, and terminal outputs are cleared of secrets before logging.
2. **PowerShell vs. Bash Environment Syntax on Windows**:
   - *What Happened*: Initial command invocations assumed Bash POSIX syntax (e.g. `export VAR=...`, `grep`), which failed or behaved unexpectedly in Windows PowerShell.
   - *Lesson & Fix*: Standardized on native PowerShell commands (e.g. `$env:VAR=...`, `Select-String`, Windows path backslashes vs. forward slashes) and ensured Python code normalizes paths using `pathlib.Path`.
3. **Agent Fact-Checking & Citation Verification**:
   - *What Happened*: During research, an unverified tool (`sast-triage`) was initially proposed but its GitHub URL returned a 404 HTTP error. Similarly, unsourced claims (e.g. "40% patch regression rate" and "zero FN tolerance") were initially suggested.
   - *Lesson & Fix*: Instituted a strict verification discipline: every claim must be cited with a live URL, unverified URLs are purged immediately, and probabilistic AI behavior is calibrated as a measured target rather than an impossible guarantee.
4. **Semgrep Git-Tracking Constraint on Uncommitted/Untracked Files**:
   - *What Happened*: During early smoke testing on `scripts/vuln_sample`, Semgrep reported only 1 finding because Semgrep OSS strictly scans files tracked by Git when executed inside a Git repository.
   - *Lesson & Fix*: Evaluation target repositories (like PyGoat) must be cloned as complete git repositories and kept in a clean committed state, and external test directories must be explicitly git-tracked or scanned with appropriate path arguments.
5. **Class Imbalance in Benchmark Repositories**:
   - *What Happened*: Running the 3 rule packs on PyGoat revealed that 25 of 84 findings (~30%) belong to a single rule (`@csrf_exempt`), while critical vulnerabilities like command injection have only 2 findings.
   - *Lesson & Fix*: Metrics cannot be evaluated solely on aggregate F1; the evaluation framework must report both aggregate and stratified per-rule-family performance.
