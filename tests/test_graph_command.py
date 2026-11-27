from click.testing import CliRunner

from concore_cli.cli import cli

GRAPH = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    <node id="n0"><data key="d0"><y:NodeLabel>CZ:controller.py</y:NodeLabel></data></node>
    <node id="n1"><data key="d0"><y:NodeLabel>OUT:</y:NodeLabel></data></node>
    <node id="n2"><data key="d0"><y:NodeLabel>say "hi":x.py</y:NodeLabel></data></node>
    <edge id="e0" source="n0" target="n1"><data key="d1"><y:EdgeLabel>0x1000_u</y:EdgeLabel></data></edge>
    <edge id="e1" source="n1" target="n2"><data key="d1"><y:EdgeLabel>VCY</y:EdgeLabel></data></edge>
    <edge id="e2" source="n2" target="n0"></edge>
    <edge id="e3" source="n0" target="missing"></edge>
  </graph>
</graphml>
"""


def _graph(tmp_path):
    path = tmp_path / "wf.graphml"
    path.write_text(GRAPH, encoding="utf-8")
    return str(path)


def test_graph_defaults_to_mermaid(tmp_path):
    result = CliRunner().invoke(cli, ["graph", _graph(tmp_path)])
    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert lines[0] == "flowchart LR"
    assert '    n0["CZ:controller.py"]' in lines
    assert '    n1["OUT"]' in lines
    assert '    n0 -->|"0x1000_u"| n1' in lines
    assert "    n2 --> n0" in lines


def test_graph_mermaid_escapes_quotes(tmp_path):
    result = CliRunner().invoke(cli, ["graph", _graph(tmp_path)])
    assert '    n2["say #quot;hi#quot;:x.py"]' in result.output.splitlines()


def test_graph_skips_edges_to_unknown_nodes(tmp_path):
    result = CliRunner().invoke(cli, ["graph", _graph(tmp_path)])
    assert "missing" not in result.output
    assert result.output.count("-->") == 3


def test_graph_dot(tmp_path):
    result = CliRunner().invoke(cli, ["graph", _graph(tmp_path), "-f", "dot"])
    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert lines[0] == "digraph concore {"
    assert lines[-1] == "}"
    assert '    n0 [label="CZ:controller.py"];' in lines
    assert '    n2 [label="say \\"hi\\":x.py"];' in lines
    assert '    n0 -> n1 [label="0x1000_u"];' in lines
    assert "    n2 -> n0;" in lines


def test_graph_writes_output_file(tmp_path):
    out = tmp_path / "wf.mmd"
    result = CliRunner().invoke(cli, ["graph", _graph(tmp_path), "-o", str(out)])
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").startswith("flowchart LR\n")


def test_graph_rejects_non_graphml(tmp_path):
    bad = tmp_path / "bad.graphml"
    bad.write_text("<html></html>", encoding="utf-8")
    result = CliRunner().invoke(cli, ["graph", str(bad)])
    assert result.exit_code == 1
    assert "Not a valid GraphML" in result.output


def test_graph_rejects_unknown_format(tmp_path):
    result = CliRunner().invoke(cli, ["graph", _graph(tmp_path), "-f", "svg"])
    assert result.exit_code != 0
