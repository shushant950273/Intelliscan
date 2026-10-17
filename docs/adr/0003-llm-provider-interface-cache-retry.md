# ADR 0003: LLM Provider Interface with Caching, Retry, and Model Fallback

## Context
IntelliScan uses frontier Large Language Models (LLMs) via the Google GenAI SDK to adjudicate SAST alerts. However, relying directly on raw API calls introduces severe operational risks:
1. Public free/low-cost tiers enforce strict rate limits (e.g., 15 RPM).
2. Network calls experience transient HTTP 429 (rate limit) and 503 (service overload) errors.
3. Repeated runs across identical codebases drain quotas and generate unpredictable billing costs.
4. Hardcoding model calls prevents scientific model comparisons.

## Decision
1. We define an abstract `LLMProvider` interface in `core/llm/base.py` enforcing structured schema generation (`generate_structured`).
2. The active model ID is loaded from `.env`, but each `TriageResult` records the exact `model_id_used` that actually produced the adjudication, plus an `is_fallback: bool` flag. The `ScanReport` metadata records the list of all `models_used` across the run.
3. We wrap the provider using the Decorator pattern:
   - **`CachedLLMProvider`**: Computes an SHA-256 composite cache key: `SHA256(code_context_hash + prompt_template_version + model_id + rule_id)` and caches JSON results to `.cache/llm/`. Modifying the code context, prompt template, model ID, or rule ID automatically invalidates stale entries.
   - **Failures Are Never Cached**: API errors, exhausted retries, and unparseable responses that trigger an `UNCERTAIN` fallback are strictly **never** stored in the cache, ensuring transient faults are re-attempted on subsequent runs.
   - **`RetryingLLMProvider`**: Implements exponential backoff (up to 3 retries) on 429/503 errors via `tenacity`, switches to a configured fallback model on repeated failure, and defaults safely to `UNCERTAIN` if all attempts fail.

## Alternatives Considered
- **No Caching (Live API Calls Every Time)**: *Rejected* because running benchmark suites (50–80 alerts) repeatedly during development quickly triggers rate limits and slows down local iteration.
- **In-Memory Cache Dictionary**: *Rejected* because the cache is lost between CLI executions; on-disk file caching persists across separate runs.
- **Caching Failures / Errors**: *Rejected* because transient server outages (HTTP 503) or rate spikes (HTTP 429) would become permanently stuck as `UNCERTAIN` until manual cache deletion.

## Consequences
- **Positive**: Resilient against transient outages; lightning-fast local development on cached prompts; transparent model provenance tracking; safe automatic cache invalidation on prompt updates.
- **Negative**: Disk cache must be maintained in `.cache/` (added to `.gitignore`).
