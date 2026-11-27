import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "concore_cli", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def test_python_dash_m_runs_the_cli():
    result = _run("--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("concore, version ")


def test_python_dash_m_shows_commands_under_the_concore_name():
    result = _run("--help")
    assert result.returncode == 0, result.stderr
    assert "Usage: concore" in result.stdout
    assert "validate" in result.stdout
