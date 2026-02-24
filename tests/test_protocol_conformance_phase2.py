import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "protocol_fixtures"
PHASE1_CASES_PATH = FIXTURE_DIR / "python_phase1_cases.json"
PHASE2_MATRIX_PATH = FIXTURE_DIR / "cross_runtime_matrix.phase2.json"

EXPECTED_RUNTIMES = {"python", "cpp", "matlab", "octave", "verilog"}
EXPECTED_CLASSIFICATIONS = {"required", "implementation_defined", "known_deviation"}
EXPECTED_STATUSES = {"observed_pass", "observed_fail", "not_audited"}


def _load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _phase1_cases():
    doc = _load_json(PHASE1_CASES_PATH)
    return {case["id"]: case for case in doc["cases"]}


def _phase2_matrix():
    return _load_json(PHASE2_MATRIX_PATH)


def test_phase2_matrix_metadata_and_enums():
    doc = _phase2_matrix()
    assert doc["phase"] == "2"
    assert doc["mode"] == "report_only"
    assert doc["source_fixture"] == "python_phase1_cases.json"
    assert set(doc["runtimes"]) == EXPECTED_RUNTIMES
    assert set(doc["classifications"]) == EXPECTED_CLASSIFICATIONS
    assert set(doc["statuses"]) == EXPECTED_STATUSES


def test_phase2_matrix_covers_all_phase1_cases():
    phase1 = _phase1_cases()
    matrix_cases = _phase2_matrix()["cases"]
    matrix_ids = {case["id"] for case in matrix_cases}
    assert matrix_ids == set(phase1.keys())


def test_phase2_matrix_rows_have_consistent_shape():
    phase1 = _phase1_cases()
    for row in _phase2_matrix()["cases"]:
        assert row["id"] in phase1
        assert row["target"] == phase1[row["id"]]["target"]
        assert set(row["runtime_results"].keys()) == EXPECTED_RUNTIMES

        for runtime, result in row["runtime_results"].items():
            assert result["status"] in EXPECTED_STATUSES
            assert result["classification"] in EXPECTED_CLASSIFICATIONS
            assert isinstance(result["note"], str) and result["note"].strip()
            if runtime == "python":
                assert result["status"] == "observed_pass"
