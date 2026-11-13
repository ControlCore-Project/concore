"""Every demo workflow must generate a complete study for every build type.

This runs mkconcore.py on each demo/*.graphml for posix, windows and docker
and checks that it succeeds and writes the expected scripts. A language
that mkconcore.py does not know how to build (for example Julia nodes
before Julia support was added) shows up here as a failing workflow
instead of surfacing later in a user's build.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO_ROOT / "demo"
WORKFLOWS = sorted(DEMO_DIR.glob("*.graphml"))

EXPECTED_SCRIPTS = {
    "posix": ["build", "run", "stop", "clear", "debug", "maxtime", "params", "unlock"],
    "windows": [
        "build.bat",
        "run.bat",
        "stop.bat",
        "clear.bat",
        "debug.bat",
        "maxtime.bat",
        "params.bat",
        "unlock.bat",
    ],
    "docker": ["build", "run", "stop", "clear", "debug", "maxtime", "params", "unlock"],
}

# Workflows that mkconcore.py cannot build yet, as (workflow, type) -> reason.
# Remove an entry when the underlying support lands.
KNOWN_UNSUPPORTED = {
    ("sampleJ.graphml", "posix"): "Julia (.jl) nodes in local builds",
    ("sampleJ.graphml", "windows"): "Julia (.jl) nodes in local builds",
}


def _cases():
    for workflow in WORKFLOWS:
        for build_type in EXPECTED_SCRIPTS:
            reason = KNOWN_UNSUPPORTED.get((workflow.name, build_type))
            marks = [pytest.mark.xfail(reason=reason)] if reason else []
            yield pytest.param(
                workflow, build_type, id=f"{workflow.stem}-{build_type}", marks=marks
            )


def test_demo_workflows_were_found():
    assert WORKFLOWS, "no demo/*.graphml files found"


@pytest.mark.parametrize("workflow,build_type", list(_cases()))
def test_demo_workflow_generates_study(tmp_path, workflow, build_type):
    out = tmp_path / "study"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "mkconcore.py"),
            str(workflow),
            str(DEMO_DIR),
            str(out),
            build_type,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    for script in EXPECTED_SCRIPTS[build_type]:
        path = out / script
        assert path.is_file(), f"{script} was not generated"
        assert path.stat().st_size > 0, f"{script} is empty"
    assert (out / "src").is_dir()
