import subprocess
import sys
from pathlib import Path

import pytest

MKCONCORE = Path(__file__).resolve().parent.parent / "mkconcore.py"

GRAPH = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    <node id="n0"><data key="d0"><y:NodeLabel>{node}:a.py</y:NodeLabel></data></node>
    <node id="n1"><data key="d0"><y:NodeLabel>plant:b.py</y:NodeLabel></data></node>
    <edge source="n0" target="n1"><data key="d1"><y:EdgeLabel>{edge}</y:EdgeLabel></data></edge>
    <edge source="n1" target="n0"><data key="d1"><y:EdgeLabel>back</y:EdgeLabel></data></edge>
  </graph>
</graphml>
"""


def _run(tmp_path, node, edge, outdir="out"):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("print('a')\n")
    (src / "b.py").write_text("print('b')\n")
    wf = tmp_path / "w.graphml"
    wf.write_text(GRAPH.format(node=node, edge=edge))
    return subprocess.run(
        [
            sys.executable,
            str(MKCONCORE),
            str(wf),
            str(src),
            str(tmp_path / outdir),
            "posix",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "node,edge", [("my ctrl", "u"), ("ctrl", "my edge")], ids=["node", "edge"]
)
def test_spaces_in_names_are_rejected_with_a_hint(tmp_path, node, edge):
    result = _run(tmp_path, node, edge)
    assert result.returncode != 0
    assert "Spaces are not allowed in names" in result.stderr + result.stdout


def test_names_without_spaces_still_build(tmp_path):
    assert _run(tmp_path, "my_ctrl", "u").returncode == 0


def test_output_directory_with_spaces_still_works(tmp_path):
    result = _run(tmp_path, "ctrl", "u", outdir="my study out")
    assert result.returncode == 0
    assert (tmp_path / "my study out" / "build").exists()
