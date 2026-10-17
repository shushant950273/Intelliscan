# ADR 0004: Three-Way Triage Classification with Conservative UNCERTAIN Handling

## Context
Commercial SAST AI triage tools (such as Semgrep Assistant or Snyk DeepCode AI) typically employ binary decision models: an alert is either classified as a true positive (kept/fixed) or discarded as a false positive. However, academic research (e.g., Xiong & Zhang 2026) demonstrates that LLMs exhibit "suppression bias," where subtle sanitizers or confusing code constructs cause the model to mistakenly classify genuine, exploitable vulnerabilities as false positives (False Negatives). In safety-critical DevSecOps, a False Negative ($FN$) is catastrophic because it silently leaves vulnerabilities in production.

## Decision
1. We mandate a strict 3-way triage classification: `TRUE_POSITIVE`, `FALSE_POSITIVE`, or `UNCERTAIN`.
2. Any failure mode—including API outages, corrupt JSON responses, model hallucination outside schema bounds, or borderline confidence ($< 0.70$)—automatically defaults to `UNCERTAIN`.
3. Under AGENTS.md Rule 6, `UNCERTAIN` findings are **never silently discarded**; they are logged as "needs review" in the scan report and surfaced for human inspection via `intelliscan review`.
4. In primary evaluation metrics (EV-02/EV-03), `UNCERTAIN` is treated conservatively as a "Kept Alert", preventing the system from falsely claiming artificial noise reduction.

## Alternatives Considered
- **Binary Triage (TP vs. FP Only)**: *Rejected* because it forces the probabilistic LLM to guess on edge cases, directly introducing False Negatives.
- **Interactive Terminal Prompt During Scan**: Asking the developer to resolve uncertain findings immediately during scanning. *Rejected* (Owner Decision D4) because it blocks automated CI/CD pipeline execution.

## Consequences
- **Positive**: Maximizes security recall (targeting $FN \approx 0$ as a measured design goal); prevents silent vulnerability drops; ensures full developer oversight.
- **Negative**: Increases human triage review queue size if the LLM confidence is poorly calibrated or prompt context is ambiguous.
