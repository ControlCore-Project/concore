import subprocess
import sys
from pathlib import Path

MKCONCORE = Path(__file__).resolve().parent.parent / "mkconcore.py"

GRAPH = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    <node id="n0"><data key="d0"><y:NodeLabel>a:a.py</y:NodeLabel></data></node>
    <node id="n1"><data key="d0"><y:NodeLabel>b:b.py</y:NodeLabel></data></node>
    <edge source="n0" target="n1"><data key="d1"><y:EdgeLabel>0x1_x</y:EdgeLabel></data></edge>
  </graph>
</graphml>
"""


def _run(tmp_path, scripts):
    src = tmp_path / "src"
    src.mkdir()
    for name in scripts:
        (src / name).write_text("print('x')\n")
    wf = tmp_path / "w.graphml"
    wf.write_text(GRAPH)
    return subprocess.run(
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


def test_mkconcore_fails_when_source_file_missing(tmp_path):
    result = _run(tmp_path, ["a.py"])
    assert result.returncode != 0
    assert "b.py" in result.stdout + result.stderr


def test_mkconcore_succeeds_when_all_sources_exist(tmp_path):
    assert _run(tmp_path, ["a.py", "b.py"]).returncode == 0
