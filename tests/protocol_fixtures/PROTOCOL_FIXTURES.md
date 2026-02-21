# Protocol Conformance Fixtures (Phase 1)

This directory contains the phase-1 protocol conformance baseline for Python.

- `schema.phase1.json`: fixture document shape and supported case targets.
- `python_phase1_cases.json`: initial baseline cases (report-only mode metadata).

Phase-1 scope:

- No runtime behavior changes.
- Python-only execution through `tests/test_protocol_conformance.py`.
- Fixture format is language-neutral to enable future cross-binding runners.
