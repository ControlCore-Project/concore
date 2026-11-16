import subprocess
import sys
from pathlib import Path

MKCONCORE = Path(__file__).resolve().parent.parent / "mkconcore.py"

NODE_A = '<node id="n0"><data key="d0"><y:NodeLabel>a:a.py</y:NodeLabel></data></node>'
NODE_B = '<node id="n1"><data key="d0"><y:NodeLabel>b:b.py</y:NodeLabel></data></node>'


def _build(tmp_path, body):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("print('a')\n")
    (src / "b.py").write_text("print('b')\n")
    wf = tmp_path / "w.graphml"
    wf.write_text(
        '<?xml version="1.0"?>\n'
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
        'xmlns:y="http://www.yworks.com/xml/graphml">'
        f'<graph id="G" edgedefault="directed">{body}</graph></graphml>\n'
    )
    result = subprocess.run(
        [
            sys.executable,
            str(MKCONCORE),
            str(wf),
            str(src),
            str(tmp_path / "out"),
            "posix",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    return result, result.stdout + result.stderr


def test_edge_without_label_is_reported(tmp_path):
    result, output = _build(
        tmp_path, f'{NODE_A}{NODE_B}<edge source="n0" target="n1"/>'
    )
    assert result.returncode == 0
    assert "Edge 'n0' -> 'n1' has no label" in output


def test_edge_to_missing_node_is_reported(tmp_path):
    edge = '<edge source="n0" target="nX"><data key="d1"><y:EdgeLabel>c</y:EdgeLabel></data></edge>'
    result, output = _build(tmp_path, f"{NODE_A}{NODE_B}{edge}")
    assert result.returncode == 0
    assert "Edge 'n0' -> 'nX'" in output


def test_node_without_label_is_reported(tmp_path):
    result, output = _build(tmp_path, f'{NODE_A}{NODE_B}<node id="n9"/>')
    assert result.returncode == 0
    assert "Node 'n9' has no label" in output


def test_valid_graph_has_no_skip_warnings(tmp_path):
    edge = '<edge source="n0" target="n1"><data key="d1"><y:EdgeLabel>c</y:EdgeLabel></data></edge>'
    result, output = _build(tmp_path, f"{NODE_A}{NODE_B}{edge}")
    assert result.returncode == 0
    assert "was ignored" not in output


def test_label_in_second_data_element_is_used(tmp_path):
    """yEd can write an empty <data> (e.g. a description) before the graphics one."""

    def node(i, label):
        return (
            f'<node id="n{i}"><data key="d4"/><data key="d5"><y:ShapeNode>'
            f"<y:NodeLabel>{label}</y:NodeLabel></y:ShapeNode></data></node>"
        )

    edge = (
        '<edge source="n0" target="n1"><data key="d6"/><data key="d7"><y:PolyLineEdge>'
        "<y:EdgeLabel>c</y:EdgeLabel></y:PolyLineEdge></data></edge>"
    )
    result, output = _build(tmp_path, node(0, "a:a.py") + node(1, "b:b.py") + edge)
    assert result.returncode == 0
    assert "was ignored" not in output
    generated = {p.name for p in (tmp_path / "out" / "src").glob("*.py")}
    assert {"a.py", "b.py"} <= generated
