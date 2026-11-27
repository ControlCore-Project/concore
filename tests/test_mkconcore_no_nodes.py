import subprocess
import sys
from pathlib import Path

import pytest

MKCONCORE = Path(__file__).resolve().parent.parent / "mkconcore.py"

EMPTY_GRAPH = (
    '<?xml version="1.0"?>\n'
    '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">'
    '<graph id="G" edgedefault="directed"></graph></graphml>\n'
)


@pytest.mark.parametrize("content", [EMPTY_GRAPH, "this is not xml"])
def test_mkconcore_fails_when_graph_has_no_nodes(tmp_path, content):
    wf = tmp_path / "w.graphml"
    wf.write_text(content)
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"

    result = subprocess.run(
        [sys.executable, str(MKCONCORE), str(wf), str(src), str(out), "posix"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "No nodes found" in result.stdout + result.stderr
