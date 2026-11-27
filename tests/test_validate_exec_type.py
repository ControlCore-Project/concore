import pytest
from click.testing import CliRunner

from concore_cli.cli import cli

GRAPH = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    <node id="n0"><data key="d0"><y:NodeLabel>CZ:{first}</y:NodeLabel></data></node>
    <node id="n1"><data key="d0"><y:NodeLabel>PZ:pm.py</y:NodeLabel></data></node>
  </graph>
</graphml>
"""


def _validate(tmp_path, first, *extra):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "pm.py").write_text("x\n")
    if "." in first:
        (src / first).write_text("x\n")
    wf = tmp_path / "wf.graphml"
    wf.write_text(GRAPH.format(first=first), encoding="utf-8")
    return CliRunner().invoke(cli, ["validate", str(wf), "--source", str(src), *extra])


@pytest.mark.parametrize("exec_type", ["posix", "windows"])
def test_pulled_container_is_an_error_for_posix_and_windows(tmp_path, exec_type):
    result = _validate(tmp_path, "cpymat", "--type", exec_type)
    assert result.exit_code == 1
    assert "pulled container" in result.output
    assert f"not {exec_type}" in result.output


def test_pulled_container_is_fine_for_docker(tmp_path):
    result = _validate(tmp_path, "cpymat", "--type", "docker")
    assert "pulled container" not in result.output


def test_without_type_nothing_changes(tmp_path):
    result = _validate(tmp_path, "cpymat")
    assert "pulled container" not in result.output


def test_regular_source_files_pass_with_a_type(tmp_path):
    result = _validate(tmp_path, "controller.py", "--type", "posix")
    assert result.exit_code == 0, result.output
    assert "pulled container" not in result.output
