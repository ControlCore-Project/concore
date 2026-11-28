import json
import pytest
from click.testing import CliRunner

from concore_cli.cli import cli

GRAPH_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    <node id="n0"><data key="d0"><y:NodeLabel>{node_a}</y:NodeLabel></data></node>
    <node id="n1"><data key="d0"><y:NodeLabel>{node_b}</y:NodeLabel></data></node>
    <edge source="n0" target="n1"><data key="d1"><y:EdgeLabel>{edge}</y:EdgeLabel></data></edge>
  </graph>
</graphml>
"""


def _invoke_validate(
    tmp_path, node_a, edge, *extra, node_b="plant:b.py", files=("a.py", "b.py")
):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    for rel in files:
        target = src / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x = 1\n", encoding="utf-8")
    wf = tmp_path / "wf.graphml"
    wf.write_text(
        GRAPH_TEMPLATE.format(node_a=node_a, node_b=node_b, edge=edge),
        encoding="utf-8",
    )
    return CliRunner().invoke(cli, ["validate", str(wf), "--source", str(src), *extra])


def test_validate_rejects_spaces_in_node_container_name(tmp_path):
    res = _invoke_validate(tmp_path, "my ctrl:a.py", "u", "--format", "json")
    assert res.exit_code == 1
    payload = json.loads(res.output)
    assert payload["valid"] is False
    assert payload["errors"][0]["error_type"] == "invalid_node_container_name"
    assert "use '_' instead" in payload["errors"][0]["message"]


def test_validate_rejects_slash_and_empty_container_name(tmp_path):
    for node_label in ("a/b:a.py", ":a.py"):
        res = _invoke_validate(tmp_path, node_label, "u", "--format", "json")
        assert res.exit_code == 1, node_label
        payload = json.loads(res.output)
        assert payload["valid"] is False


@pytest.mark.parametrize(
    "node_label",
    [
        "ctrl:../evil.py",
        "ctrl:/etc/passwd.py",
        "ctrl:~/a.py",
        "ctrl:C:/a.py",
        "ctrl:a:b.py",
        "ctrl:sub/",
    ],
)
def test_validate_rejects_unsafe_source_paths(tmp_path, node_label):
    res = _invoke_validate(tmp_path, node_label, "u", "--format", "json")
    assert res.exit_code == 1, node_label
    payload = json.loads(res.output)
    assert payload["valid"] is False
    assert any(e["error_type"] == "unsafe_source_path" for e in payload["errors"])


def test_validate_allows_relative_subdir_source(tmp_path):
    res = _invoke_validate(
        tmp_path,
        "ctrl:sub/a.py",
        "u",
        files=("sub/a.py", "b.py"),
    )
    assert res.exit_code == 0, res.output


@pytest.mark.parametrize(
    "edge_label",
    [
        "my edge",
        "../out",
        "a/b",
        "a:b",
        "a;rm",
        "a*b",
        "0x1000_portA extra",
    ],
)
def test_validate_rejects_unsafe_edge_labels(tmp_path, edge_label):
    res = _invoke_validate(tmp_path, "ctrl:a.py", edge_label, "--format", "json")
    assert res.exit_code == 1, edge_label
    payload = json.loads(res.output)
    assert payload["valid"] is False
    assert any(e["error_type"] == "unsafe_edge_label" for e in payload["errors"])


def test_validate_allows_valid_zmq_edge_label(tmp_path):
    res = _invoke_validate(tmp_path, "ctrl:a.py", "0x1000_port_a")
    assert res.exit_code == 0, res.output


def test_validate_supports_sh_and_checks_missing_unusual_ext(tmp_path):
    ok_res = _invoke_validate(
        tmp_path,
        "ctrl:run.sh",
        "u",
        "--format",
        "json",
        files=("run.sh", "b.py"),
    )
    assert ok_res.exit_code == 0, ok_res.output
    ok_payload = json.loads(ok_res.output)
    assert not any(
        w["error_type"] == "unusual_file_extension" for w in ok_payload["warnings"]
    )

    bad_res = _invoke_validate(
        tmp_path,
        "ctrl:missing.rb",
        "u",
        "--format",
        "json",
        files=("b.py",),
    )
    assert bad_res.exit_code == 1
    bad_payload = json.loads(bad_res.output)
    assert any(
        w["error_type"] == "unusual_file_extension" for w in bad_payload["warnings"]
    )
    assert any(e["error_type"] == "missing_source_file" for e in bad_payload["errors"])
