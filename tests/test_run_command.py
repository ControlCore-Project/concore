"""Tests for `concore run` (concore_cli/commands/run.py)."""

import os
import subprocess
import sys
import time

import psutil
import pytest
from click.testing import CliRunner

from concore_cli.cli import cli
from concore_cli.commands import run as run_mod
from concore_cli.commands.run import (
    EXIT_INTERRUPTED,
    EXIT_TIMEOUT,
    _node_dirs,
    run_study,
)

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="uses generated POSIX shell scripts"
)


class FakeConsole:
    def __init__(self):
        self.lines = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))

    @property
    def text(self):
        return "\n".join(self.lines)


def _write_script(path, body):
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(0o700)


def _make_study(tmp_path, seconds="0.5", nodes=("A", "B")):
    """A tiny study shaped like mkconcore's POSIX output."""
    study = tmp_path / "study"
    study.mkdir()
    run_lines = ""
    stop_lines = ""
    for node in nodes:
        (study / node).mkdir()
        run_lines += f"(cd {node}; sleep {seconds} & echo $! >concorepid) &\n"
        stop_lines += f"kill -9 `cat {node}/concorepid`\nrm {node}/concorepid\n"
    _write_script(study / "run", run_lines)
    _write_script(study / "stop", stop_lines)
    return study


def _pids(study, nodes=("A", "B")):
    return [int((study / n / "concorepid").read_text().strip()) for n in nodes]


def test_node_dirs_parses_generated_run_script(tmp_path):
    script = tmp_path / "run"
    script.write_text(
        "#!/bin/bash\n"
        "(cd CZ; python3 controller.py >concoreout.txt & echo $! >concorepid) &\n"
        "(cd PZ; python3 pm.py >concoreout.txt & echo $! >concorepid) &\n"
        "(cd CZ; echo again) &\n"
    )
    assert _node_dirs(script) == ["CZ", "PZ"]


def test_node_dirs_empty_for_docker_style_script(tmp_path):
    script = tmp_path / "run"
    script.write_text("docker run --name=CZ -v CU:/out1 docker-controller&\n")
    assert _node_dirs(script) == []


def test_missing_run_script_fails(tmp_path):
    console = FakeConsole()
    assert run_study(tmp_path, console) == 1
    assert "No run script" in console.text


def test_timeout_requires_wait(tmp_path):
    study = _make_study(tmp_path)
    console = FakeConsole()
    assert run_study(study, console, timeout=5) == 1
    assert "--timeout requires --wait" in console.text


def test_start_without_wait_returns_immediately(tmp_path):
    study = _make_study(tmp_path, seconds="30")
    console = FakeConsole()
    began = time.monotonic()
    try:
        assert run_study(study, console) == 0
        assert time.monotonic() - began < 5
        time.sleep(0.5)
        assert all(psutil.pid_exists(pid) for pid in _pids(study))
    finally:
        subprocess.run([str(study / "stop")], cwd=study, capture_output=True)


def test_wait_returns_zero_when_nodes_finish(tmp_path):
    study = _make_study(tmp_path, seconds="1")
    console = FakeConsole()
    assert run_study(study, console, wait=True) == 0
    assert "Study finished" in console.text


def test_wait_timeout_stops_the_study(tmp_path):
    study = _make_study(tmp_path, seconds="60")
    console = FakeConsole()
    began = time.monotonic()
    code = run_study(study, console, wait=True, timeout=1)
    assert code == EXIT_TIMEOUT
    assert time.monotonic() - began < 30
    assert "Timeout" in console.text
    time.sleep(0.5)
    # the stop script removed the pid files and the nodes are gone
    assert not (study / "A" / "concorepid").exists()


def test_interrupt_stops_the_study(tmp_path, monkeypatch):
    study = _make_study(tmp_path, seconds="60")
    console = FakeConsole()
    calls = {"n": 0}
    real_sleep = time.sleep

    def interrupting_sleep(seconds):
        calls["n"] += 1
        if calls["n"] > 3:
            raise KeyboardInterrupt
        real_sleep(0.05)

    monkeypatch.setattr(run_mod.time, "sleep", interrupting_sleep)
    assert run_study(study, console, wait=True) == EXIT_INTERRUPTED
    assert "Interrupted" in console.text
    assert not (study / "A" / "concorepid").exists()


def test_run_script_failure_exit_code_is_returned(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    _write_script(study / "run", "exit 3\n")
    console = FakeConsole()
    assert run_study(study, console) == 3
    assert "Run script failed" in console.text


def test_build_runs_before_run(tmp_path):
    study = _make_study(tmp_path, seconds="0.2")
    _write_script(study / "build", "touch built\n")
    console = FakeConsole()
    assert run_study(study, console, build=True, wait=True) == 0
    assert (study / "built").exists()


def test_failed_build_stops_before_running(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    _write_script(study / "build", "exit 4\n")
    _write_script(study / "run", "touch ran\n")
    console = FakeConsole()
    assert run_study(study, console, build=True) == 4
    assert not (study / "ran").exists()
    assert "Build failed" in console.text


def test_wait_ignores_stale_pid_files(tmp_path, monkeypatch):
    monkeypatch.setattr(run_mod, "PID_WAIT_SECONDS", 0.5)
    study = tmp_path / "study"
    (study / "A").mkdir(parents=True)
    # a pid file left by an earlier run, pointing at a live process
    pid_file = study / "A" / "concorepid"
    pid_file.write_text(str(os.getpid()))
    old = time.time() - 3600
    os.utime(pid_file, (old, old))
    # this run's script never writes a pid file for A
    _write_script(study / "run", "(cd A; true) &\n")
    console = FakeConsole()
    began = time.monotonic()
    assert run_study(study, console, wait=True) == 0
    assert time.monotonic() - began < 10
    assert "no process id found for node 'A'" in console.text


def test_wait_on_study_without_pid_files_only_warns(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    _write_script(study / "run", "true\n")
    console = FakeConsole()
    assert run_study(study, console, wait=True) == 0
    assert "nothing to wait for" in console.text


def test_cli_run_starts_a_study(tmp_path):
    study = _make_study(tmp_path, seconds="0.3")
    result = CliRunner().invoke(cli, ["run", str(study), "--wait"])
    assert result.exit_code == 0, result.output


def test_cli_run_propagates_exit_code(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    _write_script(study / "run", "exit 3\n")
    result = CliRunner().invoke(cli, ["run", str(study)])
    assert result.exit_code == 3


def test_cli_run_rejects_missing_directory(tmp_path):
    result = CliRunner().invoke(cli, ["run", str(tmp_path / "nope")])
    assert result.exit_code != 0


def test_cli_run_rejects_non_positive_timeout(tmp_path):
    study = _make_study(tmp_path)
    result = CliRunner().invoke(cli, ["run", str(study), "--wait", "--timeout", "0"])
    assert result.exit_code != 0
