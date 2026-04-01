# Protocol Conformance Fixtures (Phase 1)

This directory contains the phase-1 protocol conformance baseline for Python.

- `schema.phase1.json`: fixture document shape and supported case targets.
- `python_phase1_cases.json`: initial baseline cases (report-only mode metadata).
- `cross_runtime_matrix.phase2.json`: phase-2 cross-runtime mapping matrix in report-only mode.

Phase-1 scope:

- No runtime behavior changes.
- Python-only execution through `tests/test_protocol_conformance.py`.
- Fixture format is language-neutral to enable future cross-binding runners.
- Baseline now includes `read_file` runtime-behavior checks in addition to parser/API targets.

Phase-2 scope (mapping only):

- No runtime behavior changes.
- Adds a cross-runtime matrix to track per-case audit status and classification.
- Java runtime entries are tracked with observed status from the Java regression suite (`TestLiteralEval.java`, `TestConcoredockerApi.java`).
- Current baseline records Java as `observed_pass` for the listed phase-2 cases.
- Phase-2 matrix includes `read_file` status rows for cross-runtime tracking.
- Keeps CI non-blocking for non-Python runtimes that are not yet audited by marking them as `not_audited`.

Java conformance execution in CI:

- The `java-test` job in `.github/workflows/ci.yml` downloads `jeromq` for classpath compatibility.
- It compiles `concoredocker.java`, `TestLiteralEval.java`, and `TestConcoredockerApi.java`.
- It runs both Java test classes and records initial phase-2 matrix status as observed in CI.
