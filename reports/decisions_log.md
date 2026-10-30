# Decisions & Architecture Log - Scheme Finder

## Architectural & Research Principles
1. **Separation of Concerns**:
   - The LLM is **never** an eligibility evaluator or arbitrator. It functions solely as an offline rule proposition and conversational interface.
   - All eligibility logic is implemented in a deterministic rule engine using **Three-Valued Logic (Kleene / Lukasiewicz)** (`SATISFIED`, `NOT_SATISFIED`, `UNKNOWN`).

2. **Uncertainty is First-Class**:
   - Missing profile information evaluates to `UNKNOWN` and is **never** coerced to `False` or `True`.
   - Schemes with missing information are classified as `MORE_INFORMATION_NEEDED`, never failed or passed.

3. **Human-in-the-Loop Safeguards**:
   - The classification `LIKELY_NOT_ELIGIBLE` can **only** be triggered if a criterion is both:
     1. Marked as `is_mandatory = True`.
     2. Formally marked as `review_status = "verified"` by human domain review.
   - Any scheme with unreviewed rules or discretionary administrative clauses receives `NEEDS_MANUAL_VERIFICATION`.

4. **Cryptographic Provenance**:
   - Every scheme has an immutable JSON snapshot under `data/raw_snapshots/` with UTC fetch date and SHA-256 hash.
   - Every individual rule criterion links directly to its `verbatim_source_sentence`.

