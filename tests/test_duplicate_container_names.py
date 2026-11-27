import subprocess
import sys
from pathlib import Path

from concore_cli.commands.validate import validate_workflow

MKCONCORE = Path(__file__).resolve().parent.parent / "mkconcore.py"

GRAPH = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:y="http://www.yworks.com/xml/graphml">
  <graph id="G" edgedefault="directed">
    <node id="n0"><data key="d0"><y:NodeLabel>{first}</y:NodeLabel></data></node>
    <node id="n1"><data key="d0"><y:NodeLabel>{second}</y:NodeLabel></data></node>
    <edge source="n0" target="n1"><data key="d1"><y:EdgeLabel>u</y:EdgeLabel></data></edge>
    <edge source="n1" target="n0"><data key="d1"><y:EdgeLabel>y</y:EdgeLabel></data></edge>
  </graph>
</graphml>
"""


class _Console:
    def __init__(self):
        self.lines = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))


def _setup(tmp_path, first, second):
    src = tmp_path / "src"
    src.mkdir()
    for name in ("a.py", "b.py"):
        (src / name).write_text("print('x')\n")
    wf = tmp_path / "w.graphml"
    wf.write_text(GRAPH.format(first=first, second=second))
    return wf, src


def _run_mkconcore(tmp_path, wf, src):
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


def test_mkconcore_rejects_two_nodes_with_same_container_name(tmp_path):
    wf, src = _setup(tmp_path, "ctrl:a.py", "ctrl:b.py")
    result = _run_mkconcore(tmp_path, wf, src)
    assert result.returncode != 0
    assert "Container name 'ctrl' is used by more than one node" in (
        result.stdout + result.stderr
    )


def test_mkconcore_accepts_distinct_container_names(tmp_path):
    wf, src = _setup(tmp_path, "ctrl:a.py", "plant:b.py")
    assert _run_mkconcore(tmp_path, wf, src).returncode == 0


def test_validate_reports_duplicate_container_name(tmp_path):
    wf, src = _setup(tmp_path, "ctrl:a.py", "ctrl:b.py")
    console = _Console()
    assert validate_workflow(str(wf), str(src), console) is False
    assert any(
        "Duplicate node container name: 'ctrl'" in line for line in console.lines
    )


def test_validate_accepts_distinct_container_names(tmp_path):
    wf, src = _setup(tmp_path, "ctrl:a.py", "plant:b.py")
    assert validate_workflow(str(wf), str(src), _Console()) is True
