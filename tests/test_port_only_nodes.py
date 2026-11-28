"""Nodes with no source file ("IN:", "OUT:") must not stop a study from building.

Port-only nodes are used by the distributed / ZMQ and measurement workflows
in this repository. mkconcore.py used to reject them while validating node
labels ("Node source file '' cannot be empty"), although the rest of the
generator handles a node without a source file.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LABEL_RE = re.compile(r"<y:NodeLabel[^>]*>([^<]*)</y:NodeLabel>")


def _has_port_only_node(graphml):
    text = graphml.read_text(errors="ignore")
    for label in LABEL_RE.findall(text):
        label = re.sub(r"\s+", " ", label)
        if ":" in label and not label.split(":", 1)[1].strip():
            return True
    return False


PORT_ONLY_WORKFLOWS = sorted(
    p for p in REPO_ROOT.rglob("*.graphml") if _has_port_only_node(p)
)


def test_port_only_workflows_were_found():
    assert PORT_ONLY_WORKFLOWS, "no workflow with a port-only node found"


@pytest.mark.parametrize("build_type", ["posix", "windows", "docker"])
@pytest.mark.parametrize(
    "workflow",
    PORT_ONLY_WORKFLOWS,
    ids=[str(p.relative_to(REPO_ROOT)) for p in PORT_ONLY_WORKFLOWS],
)
def test_workflow_with_port_only_node_builds(tmp_path, workflow, build_type):
    # mkconcore refuses nodes whose source file is missing, and not every
    # bundled workflow ships its node scripts, so give each node an empty file.
    src = tmp_path / "src"
    src.mkdir()
    for label in LABEL_RE.findall(workflow.read_text(errors="ignore")):
        label = re.sub(r"\s+", " ", label)
        if ":" in label:
            name = label.split(":", 1)[1].strip()
            if name:
                (src / name).parent.mkdir(parents=True, exist_ok=True)
                (src / name).write_text("")
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "mkconcore.py"),
            str(workflow),
            str(src),
            str(tmp_path / "study"),
            build_type,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
