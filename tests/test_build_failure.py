"""`concore build --auto-build` must fail when the generated build script fails.

It used to print "Build failed" and then "Workflow ready!" and exit 0, so
scripts and CI treated a broken build as a success.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from concore_cli.cli import cli

REAL_RUN = subprocess.run


def _fail_only_the_build_script(*args, **kwargs):
    command = args[0] if args else kwargs.get("args")
    if isinstance(command, list) and Path(command[0]).name in ("build", "build.bat"):
        raise subprocess.CalledProcessError(
            3, command, output="build stdout", stderr="build stderr"
        )
    return REAL_RUN(*args, **kwargs)


def _build(runner, auto_build=True):
    assert runner.invoke(cli, ["init", "proj"]).exit_code == 0
    args = [
        "build",
        "proj/workflow.graphml",
        "--output",
        "out",
        "--type",
        "posix",
    ]
    if auto_build:
        args.append("--auto-build")
    return runner.invoke(cli, args)


def test_failed_auto_build_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    with patch(
        "concore_cli.commands.build.subprocess.run",
        side_effect=_fail_only_the_build_script,
    ):
        result = _build(runner)
    assert result.exit_code != 0
    assert "Build failed" in result.output
    assert "build stderr" in result.output
    assert "Workflow ready" not in result.output


def test_successful_auto_build_still_exits_zero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = _build(CliRunner())
    assert result.exit_code == 0, result.output
    assert "Build completed" in result.output
    assert "Workflow ready" in result.output


def test_build_without_auto_build_is_unaffected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = _build(CliRunner(), auto_build=False)
    assert result.exit_code == 0, result.output
    assert "Workflow ready" in result.output
