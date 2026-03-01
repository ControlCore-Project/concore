# Protocol Conformance Fixtures (Phase 1)

This directory contains the phase-1 protocol conformance baseline for Python.

- `schema.phase1.json`: fixture document shape and supported case targets.
- `python_phase1_cases.json`: initial baseline cases (report-only mode metadata).
- `cross_runtime_matrix.phase2.json`: phase-2 cross-runtime mapping matrix in report-only mode.

Phase-1 scope:

- No runtime behavior changes.
- Python-only execution through `tests/test_protocol_conformance.py`.
- Fixture format is language-neutral to enable future cross-binding runners.

Phase-2 scope (mapping only):

- No runtime behavior changes.
- Adds a cross-runtime matrix to track per-case audit status and classification.
- Keeps CI non-blocking for non-Python runtimes by marking them as `not_audited` until adapters are added.
