from click.testing import CliRunner

from concore_cli.cli import cli
from concore_cli.commands.build import _missing_sources

GRAPH = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    {nodes}
  </graph>
</graphml>
"""


def _node(node_id, label):
    return (
        f'<node id="{node_id}"><data key="d0">'
        f"<y:NodeLabel>{label}</y:NodeLabel></data></node>"
    )


def _write_graph(tmp_path, *labels):
    nodes = "\n".join(_node(f"n{i}", label) for i, label in enumerate(labels))
    path = tmp_path / "wf.graphml"
    path.write_text(GRAPH.format(nodes=nodes), encoding="utf-8")
    return path


def test_missing_sources_lists_absent_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "controller.py").write_text("x\n")
    wf = _write_graph(tmp_path, "CZ:controller.py", "PZ:pm.py", "OZ:pm.py", "A:b.m")
    assert _missing_sources(wf, src) == ["b.m", "pm.py"]


def test_missing_sources_ignores_pulled_containers_and_port_nodes(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    wf = _write_graph(tmp_path, "CZ:cpymat", "IN:", "OUT:")
    assert _missing_sources(wf, src) == []


def test_missing_sources_tolerates_unreadable_workflow(tmp_path):
    assert _missing_sources(tmp_path / "nope.graphml", tmp_path) == []


def test_build_fails_early_when_source_file_is_missing(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "controller.py").write_text("x\n")
    wf = _write_graph(tmp_path, "CZ:controller.py", "PZ:pm.py")
    out = tmp_path / "out"
    result = CliRunner().invoke(
        cli, ["build", str(wf), "--source", str(src), "--output", str(out)]
    )
    assert result.exit_code == 1
    assert "pm.py" in result.output
    assert not out.exists()
