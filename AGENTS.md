# AGENTS.md: Skill Latency Balancer (SLB)

## 1. Project Overview & Core Mission
**Skill Latency Balancer (SLB)** is a high-throughput, asynchronous load-balancing engine designed to optimize task distribution across heterogeneous worker pools based on real-time skill-latency metrics. 

**Mission:** Minimize global task execution latency by implementing a predictive, non-blocking scheduling algorithm that dynamically re-weights worker nodes based on historical performance telemetry.

## 2. Local PowerShell Commands
All automation must be executed via the project root. Agents are required to verify environment integrity before execution.

*   **Setup:** `./scripts/init.ps1` (Installs `poetry` dependencies, configures `pre-commit` hooks, and validates Python 3.11+).
*   **Test:** `pytest tests/ --cov=src --cov-report=term-missing` (Must maintain >95% coverage).
*   **Run:** `python -m slb.main --config ./config/prod.yaml`
*   **Lint:** `ruff check . && mypy src/ --strict` (Zero-warning policy).

## 3. Engineering Invariants
*   **Zero-Placeholder Mandate:** No `TODO`, `FIXME`, or `// TODO` comments are permitted in production code. If a feature is incomplete, the module must be stubbed with `NotImplementedError` and an associated tracking issue.
*   **Typing Strictness:** Every function, method, and class attribute must be explicitly typed. Use `typing.Protocol` for dependency injection and `Final` for immutable constants. No `Any` types allowed without explicit architectural justification.
*   **CRLF/LF Preservation:** The repository enforces `LF` line endings. Ensure `.gitattributes` is respected.
*   **Decoupling:** Business logic must be strictly separated from I/O (async drivers). Use the `Repository` pattern for state persistence and `Service` layers for orchestration.

## 4. Self-Healing & Error Recovery Protocol
When an agent encounters a traceback or runtime failure:

1.  **Traceback Analysis:** Capture the full stack trace. Identify if the failure is a `ConcurrencyError` (race condition), `TypeMismatch` (runtime violation of static types), or `LatencySpike` (resource exhaustion).
2.  **Local Reproduction:** Create a minimal reproduction script in `tests/repro/issue_XXXX.py`. Do not attempt a fix without a passing reproduction.
3.  **Root Cause Isolation:**
    *   If `ConcurrencyError`: Inspect `asyncio.TaskGroup` lifecycle and shared state locks.
    *   If `TypeMismatch`: Re-run `mypy --strict`.
    *   If `LatencySpike`: Analyze `src/telemetry/metrics.py` to identify bottlenecked event loops.
4.  **Verification:** Apply fix, run `pytest`, and verify that the reproduction script now passes. Delete the reproduction script before committing.

## 5. Definition of Done (DoD) Quality Gate
A task is considered complete only when the following criteria are met:

*   **Static Analysis:** `mypy --strict` returns 0 errors. `ruff` reports 0 violations.
*   **Test Coverage:** No reduction in overall coverage percentage. New logic must include unit tests covering edge cases (empty inputs, timeout scenarios, connection drops).
*   **Documentation:** All public-facing APIs (classes/methods) must have Google-style docstrings.
*   **Performance:** Execution time for the core scheduling loop must remain within the 5ms p99 threshold.
*   **Integration:** The feature must be integrated into the main branch via a clean, atomic commit with a descriptive message referencing the issue ID.
*   **Peer Review:** Code must be formatted according to `black` standards.