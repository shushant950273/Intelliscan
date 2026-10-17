# IntelliScan Ground-Truth Labeling Guidelines

**Document Version:** 1.0  
**Requirement Reference:** [SRS EV-01](SRS.md#ev-01-ground-truth-evaluation-corpus-d1)  
**Target Dataset:** 84 Semgrep findings generated from OWASP PyGoat (`results/pygoat_3packs.json`)  
**Status:** Pre-Labeling Protocol (Must be finalized *before* executing manual triage)

---

## 1. Purpose & Core Protocol Rule

This document defines the operational criteria and decision tree for manually labeling static analysis findings into ground-truth classifications (`TRUE_POSITIVE`, `FALSE_POSITIVE`, `AMBIGUOUS`).

> **Cardinal Rule (Blind Evaluation):**
> All ground-truth labels must be assigned **BEFORE** and **WITHOUT** viewing any LLM triage output, AI confidence score, or patch proposal. This protocol reduces confirmation bias (though cannot eliminate all subjectivity). The human evaluator reviews primarily the target source code and Semgrep rule definition. PyGoat exploit walkthroughs (`Solutions/solution.md`) may be consulted **only as an exploratory hint**; a finding is labeled `TRUE_POSITIVE` only if the security weakness is demonstrably present in that specific code, not merely because the application documentation lists it.

---

## 2. Standard Classification Definitions

### 2.1 `TRUE_POSITIVE` (Real Weakness Present)
- The specific weakness, vulnerable pattern, or insecure configuration described by the Semgrep rule is genuinely present and exploitable (or introduces verifiable security risk) in the context of the application.
- **Rule for Deliberately Vulnerable Apps:** Code residing in a deliberately vulnerable training lab (like PyGoat) **still counts as `TRUE_POSITIVE`** when the security flaw described by the rule actually exists in that code. The presence of a challenge in `Solutions/solution.md` is strictly a hint; the evaluator must independently verify that the vulnerability is genuinely present in the scanned code snippet itself.

### 2.2 `FALSE_POSITIVE` (Spurious SAST Alert)
- The static syntactic pattern matched, but the weakness is not genuinely present due to code context.
- Common FP indicators:
  1. The input parameter is hardcoded, constant, or originates strictly from a trusted server-side authority.
  2. The input undergoes effective sanitization, validation, or type casting (e.g., `int()`) prior to entering the sink.
  3. The code is dead, unreachable, or in an isolated test fixture/mock where real exploitation is structurally impossible.
  4. The rule matched an insecure default API signature (e.g., cookie setting), but the application explicitly configures protection globally in middleware or application settings.

### 2.3 `AMBIGUOUS` (Undecidable from Context Alone)
- The finding cannot be confirmed as exploitable or safe without inspecting external database states, undocumented third-party libraries, or complex network configurations not present in the repository.
- **Evaluation Impact & Reporting:**
  1. `AMBIGUOUS` entries are excluded from primary binary metric calculations (Precision, Recall, F1).
  2. The total count and percentage of `AMBIGUOUS` findings must be explicitly reported in the evaluation summary.
  3. **Evaluation of IntelliScan on Ambiguous Cases**: If IntelliScan classifies an `AMBIGUOUS` finding as `UNCERTAIN`, this is considered an **aligned/acceptable outcome** (both human and model recognize context limitations). If IntelliScan asserts `TRUE_POSITIVE` or `FALSE_POSITIVE` on an ambiguous case, it is flagged in the report for manual audit.

---

## 3. Generic 5-Step Triage Decision Procedure

Follow this systematic checklist for each finding in sequence:

```
[Step 1: Locate & Scope]
  └─ Read target file and extract the enclosing function/method.
  └─ Read Semgrep rule message and CWE definition from JSON metadata.

[Step 2: Source-to-Sink Taint Trace]
  └─ Identify the matched sink (e.g., cursor.execute, eval, set_cookie, subprocess.Popen).
  └─ Trace the variable entering the sink upstream to its origin (request.GET, request.POST, constant).

[Step 3: Verification of Sanitizers & Framework Guards]
  └─ Check if data passes through validation, casting (int, float), allowlists, or escaping.
  └─ Check if framework-level middleware provides automatic protection (e.g., CSRF middleware).

[Step 4: Contextual Environment Inspection]
  └─ Is the file production code (views.py, apis.py) or a test file/mock fixture?
  └─ Is the endpoint an intentionally unprotected demonstration challenge?

[Step 5: Final Adjudication]
  └─ If source is untrusted and reaches sink unmitigated -> TRUE_POSITIVE.
  └─ If input is safe, unreachable, or mitigated -> FALSE_POSITIVE.
  └─ If missing critical external context -> AMBIGUOUS.
```

---

## 4. Per-Rule-Family Guidance (Based on PyGoat Findings)

The 84 findings in `results/pygoat_3packs.json` fall into the following core rule families:

> **Stratified Reporting Requirement:**
> Because rule frequencies are heavily skewed (e.g., `@csrf_exempt` accounts for 25 of the 84 findings, or ~30% of the entire dataset), evaluation metrics must be reported **both in aggregate and stratified per rule family**. This prevents one dominant rule from masking model performance on rarer, higher-severity categories (e.g. command injection or deserialization).

### 4.1 `@csrf_exempt` Decorator Usage (25 Findings)
- **Rule ID:** `python.django.security.audit.csrf-exempt.no-csrf-exempt` (CWE-352)
- **Semgrep Message:** *"Detected usage of @csrf_exempt, which indicates that there is no CSRF token set for this route."*
- **What to Check:** Does the decorated route perform state-changing operations (POST, PUT, DELETE, database writes), or is it an idempotent, read-only GET handler?
- **TP Condition:** View performs account updates, password changes, data writes, or sensitive actions without CSRF token validation.
- **FP Condition:** View is strictly a public read-only endpoint (e.g., health check, static GET view) or handles external Webhook callbacks with independent cryptographic signature validation.

### 4.2 Insecure Cookie Flags (12 Findings)
- **Rule IDs:** `python.django.security.audit.secure-cookies.django-secure-set-cookie` (10), `python.flask.security.audit.secure-set-cookie.secure-set-cookie` (2) (CWE-614)
- **Semgrep Message:** *"Django/Flask cookies should be handled securely by setting secure=True, httponly=True, and samesite='Lax' in response.set_cookie(...)."*
- **What to Check:** What type of data does the cookie hold? Is it a sensitive session identifier or an unauthenticated UI display preference?
- **TP Condition:** Session token, authentication JWT, or sensitive user identifier set without `httponly=True` or `secure=True`.
- **FP Condition:** Non-sensitive client-side UI preference cookie (e.g., `theme=dark`) explicitly intended to be read by client-side JavaScript.

### 4.3 Template Autoescaping Disabled via `| safe` (7 Findings)
- **Rule ID:** `python.flask.security.xss.audit.template-unescaped-with-safe.template-unescaped-with-safe` (CWE-79)
- **Semgrep Message:** *"Detected a segment of a Flask template where autoescaping is explicitly disabled with '| safe' filter. Ensure no user data is rendered here..."*
- **What to Check:** What variable is filtered with `| safe` in the template? Does it contain user-submitted input or server-generated static markup?
- **TP Condition:** Variable originates from user parameters (URL query, form POST, database user comment) rendered without prior sanitization.
- **FP Condition:** Variable contains hardcoded HTML authored by developers (e.g., static navigation menu or hardcoded SVG icons).

### 4.4 Insecure Deserialization via `pickle` (6 Findings)
- **Rule IDs:** `python.lang.security.deserialization.pickle.avoid-pickle` (4), `python.flask.security.insecure-deserialization.insecure-deserialization` (2) (CWE-502)
- **Semgrep Message:** *"Avoid using `pickle`, which is known to lead to code execution vulnerabilities."*
- **What to Check:** Does `pickle.loads()` or `pickle.load()` deserialize data received over an HTTP request, query parameter, or untrusted file upload?
- **TP Condition:** `pickle.loads(base64.b64decode(request.POST['data']))` or any user-controlled binary payload unpickled directly.
- **FP Condition:** `pickle.dumps()` used purely for outgoing serialization, or deserializing an internal trusted cache with server-signed integrity hashes.

### 4.5 User-Controlled Data in File / Request Write (6 Findings)
- **Rule ID:** `python.django.security.injection.request-data-write.request-data-write` (CWE-93)
- **Semgrep Message:** *"Found user-controlled request data passed into '.write(...)'. This could be dangerous if a malicious actor is able to control data into sensitive files."*
- **What to Check:** Is the file destination a critical system file, log file subject to CRLF injection, or an isolated scratch file?
- **TP Condition:** Request data written directly into server logs or system configuration files without stripping newline characters (`\r`, `\n`).
- **FP Condition:** Writing fixed-format data to an isolated, temporary, unprivileged user export file.

### 4.6 Insecure MD5 Hashing (6 Findings)
- **Rule IDs:** `insecure-hash-algorithms-md5` (3), `md5-used-as-password` (3) (CWE-327)
- **Semgrep Message:** *"Detected MD5 hash algorithm which is considered insecure... not suitable as a cryptographic signature."*
- **What to Check:** Is MD5 used for password storage or digital signatures, or purely as a non-cryptographic checksum / cache hash key?
- **TP Condition:** `hashlib.md5(password.encode()).hexdigest()` used for password hashing or security token generation.
- **FP Condition:** MD5 used solely to generate a non-security cache bucket ID or file integrity checksum against non-adversarial corruption.

### 4.7 Command & Code Execution: `eval()` & `subprocess` (8 Findings)
- **Rule IDs:** `user-eval` (2), `eval-detected` (2), `subprocess-injection` (2), `subprocess-shell-true` (2) (CWE-78, CWE-95)
- **What to Check:** Does untrusted input concatenate into shell strings or dynamic Python expressions? Is `shell=True` used with a string argument?
- **TP Condition:** `eval(request.POST['expr'])` or `subprocess.Popen(f"ping {user_ip}", shell=True)`.
- **FP Condition:** `eval()` on a hardcoded mathematical string constant, or `subprocess.Popen(["ping", "-c", "1", "127.0.0.1"], shell=False)`.

---

## 5. Treatment of Non-Python Files (9 HTML Templates)

The scan identified 9 findings inside Jinja/Django HTML template files (`challenge.html`, `login.html`):
- **Template Context Tracing:** Check the rendering view in `views.py` that passes context variables to the template (e.g., `render(request, "challenge.html", {"content": user_input})`).
- **Labeling Standard:** If the template applies `| safe` to a context variable derived from untrusted input, the finding is labeled **`TRUE_POSITIVE`**. If the template applies `| safe` to static text or CSRF tokens generated internally, label it **`FALSE_POSITIVE`**.

---

## 6. Labeled Record Schema

Each verified finding is recorded in `tests/data/ground_truth.json` conforming to this exact JSON schema:

```json
{
  "finding_id": "sha256_hash_string",
  "rule_id": "python.django.security.injection.command.subprocess-injection",
  "file_path": "challenge/views.py",
  "line_number": 81,
  "ground_truth": "TRUE_POSITIVE",
  "justification": "User input from request.POST['target'] is formatted directly into a subprocess command string without validation.",
  "labeling_date": "2026-10-18",
  "labeler_id": "owner"
}
```

---

## 7. Bias Control Protocol

To ensure academic and scientific integrity in a single-developer evaluation:
1. **Pre-Commit Guidelines:** This document must be checked into git **before** the ground-truth JSON manifest is populated.
2. **AI-Blind Labeling:** The evaluator must not execute `intelliscan triage` or view model predictions while reviewing the code.
3. **Temporal Consistency Check (Inter-Rater Reliability):**
   - After a minimum interval of **3 days** from the initial labeling pass, the evaluator randomly selects 15 findings and re-labels them blind.
   - Agreement rate between Pass 1 and Pass 2 must be calculated and reported:
     $$\text{Agreement Rate} = \frac{\text{Concordant Labels}}{15} \times 100\%$$
4. **Time Tracking:** The evaluator logs the time spent inspecting each finding (target: 2–4 minutes per finding).

---

## 8. Known Limitations of the Evaluation Dataset

1. **Single-Labeler Subjectivity:** Labels reflect the technical security judgment of the project owner without independent cross-institution peer adjudication.
2. **Sample Size:** The dataset comprises 84 alerts from PyGoat. While sufficient for statistical indication, it is smaller than synthetic multi-thousand case benchmarks.
3. **Domain Bias:** Findings originate from an educational Django/Flask application (PyGoat), which intentionally concentrates insecure patterns compared to enterprise production repositories.
