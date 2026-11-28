import re

import pytest
from click.testing import CliRunner

from concore_cli.cli import cli


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["init", "proj"])
    assert result.exit_code == 0, result.output
    return tmp_path / "proj"


def _labels(project):
    text = (project / "workflow.graphml").read_text(encoding="utf-8")
    return re.findall(r"<y:NodeLabel[^>]*>([^<]*)</y:NodeLabel>", text)


def test_add_node_adds_source_and_graph_entry(project):
    result = CliRunner().invoke(cli, ["add-node", str(project), "--lang", "cpp"])
    assert result.exit_code == 0, result.output
    assert (
        (project / "src" / "script.cpp")
        .read_text()
        .startswith('#include "concore.hpp"')
    )
    assert _labels(project) == ["N1:script.py", "N2:script.cpp"]


def test_add_node_picks_unused_names(project):
    for _ in range(2):
        result = CliRunner().invoke(cli, ["add-node", str(project), "--lang", "python"])
        assert result.exit_code == 0, result.output
    assert _labels(project) == ["N1:script.py", "N2:script2.py", "N3:script3.py"]
    assert (project / "src" / "script2.py").is_file()
    assert (project / "src" / "script3.py").is_file()


def test_add_node_renames_java_class_to_match_file(project):
    for _ in range(2):
        CliRunner().invoke(cli, ["add-node", str(project), "--lang", "java"])
    assert "public class Script {" in (project / "src" / "Script.java").read_text()
    second = (project / "src" / "Script2.java").read_text()
    assert "public class Script2 {" in second
    assert "public class Script {" not in second


def test_added_node_is_placed_below_existing_nodes(project):
    CliRunner().invoke(cli, ["add-node", str(project), "--lang", "octave"])
    text = (project / "workflow.graphml").read_text(encoding="utf-8")
    ys = [int(y) for y in re.findall(r'<y:Geometry[^>]*\by="(\d+)"', text)]
    assert ys == [100, 200]


def test_add_node_uses_the_files_own_graphics_key_and_line_endings(project):
    wf = project / "workflow.graphml"
    text = wf.read_text(encoding="utf-8").replace('"d6"', '"d4"').replace("\n", "\r\n")
    wf.write_bytes(text.encode("utf-8"))
    result = CliRunner().invoke(cli, ["add-node", str(project), "--lang", "verilog"])
    assert result.exit_code == 0, result.output
    data = wf.read_bytes().decode("utf-8")
    assert data.count('<data key="d4">') == 2
    assert 'key="d6"' not in data
    assert "\r\n" in data and "\n" not in data.replace("\r\n", "")


def test_workflow_still_validates_after_adding_nodes(project):
    CliRunner().invoke(cli, ["add-node", str(project), "--lang", "cpp"])
    result = CliRunner().invoke(
        cli,
        [
            "validate",
            str(project / "workflow.graphml"),
            "--source",
            str(project / "src"),
        ],
    )
    assert "has no filename" not in result.output
    assert "Missing source file" not in result.output


def test_add_node_requires_a_project(tmp_path):
    result = CliRunner().invoke(cli, ["add-node", str(tmp_path), "--lang", "python"])
    assert result.exit_code == 1
    assert "No workflow.graphml" in result.output


def test_add_node_rejects_unknown_language(project):
    result = CliRunner().invoke(cli, ["add-node", str(project), "--lang", "cobol"])
    assert result.exit_code != 0
