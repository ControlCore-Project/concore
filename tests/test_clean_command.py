import os

import pytest
from click.testing import CliRunner

from concore_cli.cli import cli

pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="study layout uses symlinks created by POSIX build"
)


def _study(tmp_path):
    study = tmp_path / "study"
    for name in ("CZ", "PZ", "CU", "PYM", "src"):
        (study / name).mkdir(parents=True)
    os.symlink("../CU", study / "CZ" / "out1")
    os.symlink("../PYM", study / "CZ" / "in1")
    os.symlink("../PYM", study / "PZ" / "out1")
    os.symlink("../CU", study / "PZ" / "in1")
    (study / "CZ" / "controller.py").write_text("code\n")
    (study / "CZ" / "concoreout.txt").write_text("log\n")
    (study / "PZ" / "concoreout.txt").write_text("log\n")
    (study / "PZ" / "concorepid").write_text("99999999\n")  # not a live pid
    (study / "CU" / "u").write_text("[0.0, 1]\n")
    (study / "PYM" / "ym").write_text("[0.0, 2]\n")
    (study / "src" / "controller.py").write_text("src\n")
    (study / "results").mkdir()
    (study / "results" / "keep.csv").write_text("keep\n")
    return study


def test_dry_run_lists_but_removes_nothing(tmp_path):
    study = _study(tmp_path)
    result = CliRunner().invoke(cli, ["clean", str(study), "--dry-run"])
    assert result.exit_code == 0
    assert "CZ/concoreout.txt" in result.output
    assert "CU/u" in result.output
    assert (study / "CU" / "u").exists()
    assert (study / "CZ" / "concoreout.txt").exists()


def test_clean_removes_only_run_leftovers(tmp_path):
    study = _study(tmp_path)
    result = CliRunner().invoke(cli, ["clean", str(study), "-y"])
    assert result.exit_code == 0
    for gone in (
        "CZ/concoreout.txt",
        "PZ/concoreout.txt",
        "PZ/concorepid",
        "CU/u",
        "PYM/ym",
    ):
        assert not (study / gone).exists(), gone
    for kept in (
        "CZ/controller.py",
        "src/controller.py",
        "results/keep.csv",
    ):
        assert (study / kept).exists(), kept
    assert (study / "CZ" / "in1").is_symlink()
    assert (study / "CU").is_dir()


def test_clean_asks_for_confirmation(tmp_path):
    study = _study(tmp_path)
    result = CliRunner().invoke(cli, ["clean", str(study)], input="n\n")
    assert result.exit_code == 0
    assert "Cancelled" in result.output
    assert (study / "CU" / "u").exists()


def test_clean_refuses_when_node_is_running(tmp_path):
    study = _study(tmp_path)
    (study / "CZ" / "concorepid").write_text(f"{os.getpid()}\n")
    result = CliRunner().invoke(cli, ["clean", str(study), "-y"])
    assert result.exit_code == 1
    assert "still running" in result.output
    assert (study / "CU" / "u").exists()


def test_clean_force_overrides_running_check(tmp_path):
    study = _study(tmp_path)
    (study / "CZ" / "concorepid").write_text(f"{os.getpid()}\n")
    result = CliRunner().invoke(cli, ["clean", str(study), "-y", "--force"])
    assert result.exit_code == 0
    assert not (study / "CU" / "u").exists()


def test_clean_nothing_to_do(tmp_path):
    study = _study(tmp_path)
    CliRunner().invoke(cli, ["clean", str(study), "-y"])
    result = CliRunner().invoke(cli, ["clean", str(study), "-y"])
    assert result.exit_code == 0
    assert "Nothing to clean" in result.output


def test_clean_rejects_non_study_directory(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    result = CliRunner().invoke(cli, ["clean", str(plain), "-y"])
    assert result.exit_code == 1
    assert "no nodes found" in result.output


def test_clean_does_not_follow_symlink_out_of_study(tmp_path):
    study = _study(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("x\n")
    os.symlink(str(outside), study / "CZ" / "out2")
    result = CliRunner().invoke(cli, ["clean", str(study), "-y"])
    assert result.exit_code == 0
    assert (outside / "precious.txt").exists()
