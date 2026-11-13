"""makestudy and makedocker must exit non-zero when they fail.

The FRI server (fri/server/main.py) runs them with subprocess.check_output and
only reports an error on a non-zero exit code, so exiting 0 after a failure
made the editor report "Directory successfully created".
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = ["makestudy", "makedocker"]

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="makestudy and makedocker are bash scripts"
)


def _run(script, *args):
    return subprocess.run(
        ["bash", str(REPO / script), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("script", SCRIPTS)
def test_no_arguments_exits_nonzero(script):
    result = _run(script)
    assert result.returncode != 0
    assert "Make a concore study" in result.stdout


@pytest.mark.parametrize("script", SCRIPTS)
def test_missing_graphml_exits_nonzero(script):
    result = _run(script, "demo/does_not_exist")
    assert result.returncode != 0
    assert "does not exist" in result.stdout


@pytest.mark.parametrize("script", SCRIPTS)
def test_existing_study_dir_exits_nonzero(script, tmp_path):
    result = _run(script, "demo/sample.graphml", str(tmp_path))
    assert result.returncode != 0
    assert "already exists" in result.stdout
    assert list(tmp_path.iterdir()) == []
