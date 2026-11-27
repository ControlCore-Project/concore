import json
import subprocess
import sys

import pytest
from click.testing import CliRunner

from concore_cli.cli import cli
from concore_cli.commands.status import _format_memory, _format_uptime


@pytest.fixture
def fake_node(tmp_path):
    """A process whose working directory looks like a generated concore node."""
    (tmp_path / "concore.iport").write_text("{}\n")
    (tmp_path / "concore.py").write_text("\n")
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], cwd=tmp_path
    )
    yield proc
    proc.kill()
    proc.wait()


def test_status_json_is_pure_json_with_consistent_count():
    result = CliRunner().invoke(cli, ["status", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["count"] == len(data["processes"])
    assert "Scanning" not in result.output


def test_status_json_reports_a_running_node(fake_node):
    result = CliRunner().invoke(cli, ["status", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    entry = next(p for p in data["processes"] if p["pid"] == fake_node.pid)
    assert set(entry) == {"pid", "name", "command", "uptime_seconds", "memory_mb"}
    assert isinstance(entry["uptime_seconds"], int) and entry["uptime_seconds"] >= 0
    assert isinstance(entry["memory_mb"], float) and entry["memory_mb"] > 0
    assert "time.sleep" in entry["command"]


def test_status_text_output_still_works(fake_node):
    result = CliRunner().invoke(cli, ["status"])
    assert result.exit_code == 0, result.output
    assert "Scanning for concore processes" in result.output
    assert "Use 'concore stop' to terminate all processes" in result.output


def test_text_formatting_helpers():
    assert _format_uptime(3725) == "1h 2m 5s"
    assert _format_uptime(0) == "0h 0m 0s"
    assert _format_uptime(None) == "unknown"
    assert _format_memory(12.34) == "12.3 MB"
    assert _format_memory(None) == "unknown"
