import json
from pathlib import Path

import pytest

import concore


FIXTURE_DIR = Path(__file__).parent / "protocol_fixtures"
SCHEMA_PATH = FIXTURE_DIR / "schema.phase1.json"
CASES_PATH = FIXTURE_DIR / "python_phase1_cases.json"
SUPPORTED_TARGETS = {"parse_params", "initval", "write_zmq"}


def _load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate_fixture_document_shape(doc):
    required_top = {"schema_version", "runtime", "mode", "cases"}
    missing = required_top - set(doc.keys())
    if missing:
        raise AssertionError(f"Fixture document missing required top-level keys: {sorted(missing)}")
    if doc["runtime"] != "python":
        raise AssertionError(f"Phase-1 fixture runtime must be 'python', found: {doc['runtime']}")
    if doc["mode"] != "report_only":
        raise AssertionError(f"Phase-1 fixture mode must be 'report_only', found: {doc['mode']}")
    if not isinstance(doc["cases"], list) or not doc["cases"]:
        raise AssertionError("Fixture document must contain a non-empty 'cases' list")

    for idx, case in enumerate(doc["cases"]):
        for key in ("id", "target", "input", "expected"):
            if key not in case:
                raise AssertionError(f"Case index {idx} missing required key '{key}'")
        if case["target"] not in SUPPORTED_TARGETS:
            raise AssertionError(
                f"Case '{case['id']}' has unsupported target '{case['target']}'"
            )


def _run_parse_params_case(case):
    result = concore.parse_params(case["input"]["sparams"])
    assert result == case["expected"]["result"]


def _run_initval_case(case):
    old_simtime = concore.simtime
    try:
        concore.simtime = case["input"]["initial_simtime"]
        result = concore.initval(case["input"]["simtime_val_str"])
        assert result == case["expected"]["result"]
        assert concore.simtime == case["expected"]["simtime_after"]
    finally:
        concore.simtime = old_simtime


def _run_write_zmq_case(case):
    class DummyPort:
        def __init__(self):
            self.sent_payload = None

        def send_json_with_retry(self, message):
            self.sent_payload = message

    old_simtime = concore.simtime
    port_name = f"fixture_{case['id'].replace('/', '_')}"
    existing_port = concore.zmq_ports.get(port_name)
    dummy_port = DummyPort()

    try:
        concore.simtime = case["input"]["initial_simtime"]
        concore.zmq_ports[port_name] = dummy_port
        concore.write(
            port_name,
            case["input"]["name"],
            case["input"]["value"],
            delta=case["input"]["delta"],
        )
        assert dummy_port.sent_payload == case["expected"]["sent_payload"]
        assert concore.simtime == case["expected"]["simtime_after"]
    finally:
        concore.simtime = old_simtime
        if existing_port is None:
            concore.zmq_ports.pop(port_name, None)
        else:
            concore.zmq_ports[port_name] = existing_port


def _run_case(case):
    if case["target"] == "parse_params":
        _run_parse_params_case(case)
    elif case["target"] == "initval":
        _run_initval_case(case)
    elif case["target"] == "write_zmq":
        _run_write_zmq_case(case)
    else:
        raise AssertionError(f"Unsupported target: {case['target']}")


def _load_cases():
    doc = _load_json(CASES_PATH)
    _validate_fixture_document_shape(doc)
    return doc["cases"]


def test_phase1_schema_file_present_and_basic_shape():
    schema = _load_json(SCHEMA_PATH)
    assert schema["title"] == "Concore Protocol Conformance Fixtures (Phase 1)"
    assert "cases" in schema["properties"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case["id"])
def test_phase1_python_protocol_conformance(case):
    _run_case(case)
