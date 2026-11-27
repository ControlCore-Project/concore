"""Tests for Julia (.jl) nodes in local (non-Docker) builds.

Julia nodes used to work only with ``--type docker``. For every other build
type ``mkconcore.py`` stopped with "Extension .jl is unsupported", so a mixed
Julia/Python study could not be run on a plain machine.

These tests run ``mkconcore.py`` on the repository's own mixed demo study
(``demo/sampleJ.graphml``: a Julia controller ``CZ`` and a Python plant ``PZ``)
and check the generated build, run and debug scripts. They need no Julia
installation because they only look at the generated files.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MKCONCORE = REPO_ROOT / "mkconcore.py"
DEMO_DIR = REPO_ROOT / "demo"
GRAPH = DEMO_DIR / "sampleJ.graphml"

POSIX_TYPES = ["posix", "macos", "ubuntu"]


def build_study(tmp_path, build_type, extra_env=None):
    """Run mkconcore.py and return (result, output_dir)."""
    out_dir = tmp_path / "study"
    env = {k: v for k, v in os.environ.items() if not k.startswith("CONCORE_JULIA")}
    env.update(extra_env or {})
    result = subprocess.run(
        [
            sys.executable,
            str(MKCONCORE),
            str(GRAPH),
            str(DEMO_DIR),
            str(out_dir),
            build_type,
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result, out_dir


def read_script(out_dir, name, windows=False):
    return (out_dir / (name + (".bat" if windows else ""))).read_text()


@pytest.mark.parametrize("build_type", POSIX_TYPES + ["windows"])
def test_local_build_accepts_julia_node(tmp_path, build_type):
    result, out_dir = build_study(tmp_path, build_type)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "unsupported" not in (result.stdout + result.stderr)
    assert (out_dir / "src" / "controller_jl.jl").exists()


@pytest.mark.parametrize("build_type", POSIX_TYPES)
def test_posix_build_copies_local_julia_runtime(tmp_path, build_type):
    result, out_dir = build_study(tmp_path, build_type)
    assert result.returncode == 0, result.stdout + result.stderr

    # The local runtime (relative ./in and ./out paths), not the Docker one.
    assert (out_dir / "src" / "concore.jl").read_text() == (
        REPO_ROOT / "concore.jl"
    ).read_text()

    build = read_script(out_dir, "build")
    assert "cp ./src/controller_jl.jl ./CZ/controller_jl.jl" in build
    assert "cp ./src/concore.jl ./CZ/concore.jl" in build
    # The Python node keeps getting its own runtime, and no Julia files.
    assert "cp ./src/concore.py ./PZ/concore.py" in build
    assert "./PZ/concore.jl" not in build


def test_posix_run_script_launches_julia_node(tmp_path):
    result, out_dir = build_study(tmp_path, "posix")
    assert result.returncode == 0, result.stdout + result.stderr

    run = read_script(out_dir, "run")
    assert (
        "(cd CZ; julia controller_jl.jl >concoreout.txt & echo $! >concorepid) &" in run
    )
    # concore stop relies on this pid file
    assert "pm.py" in run


def test_ubuntu_debug_script_opens_julia_in_xterm(tmp_path):
    result, out_dir = build_study(tmp_path, "ubuntu")
    assert result.returncode == 0, result.stdout + result.stderr

    debug = read_script(out_dir, "debug")
    assert (
        'xterm -e bash -c "cd \\"$concorewd/CZ\\"; julia controller_jl.jl; bash" &'
        in debug
    )


def test_macos_debug_script_opens_julia_in_terminal(tmp_path):
    result, out_dir = build_study(tmp_path, "macos")
    assert result.returncode == 0, result.stdout + result.stderr

    debug = read_script(out_dir, "debug")
    assert "osascript" in debug
    assert "julia controller_jl.jl" in debug


def test_windows_scripts_copy_and_launch_julia_node(tmp_path):
    result, out_dir = build_study(tmp_path, "windows")
    assert result.returncode == 0, result.stdout + result.stderr

    build = read_script(out_dir, "build", windows=True)
    assert "copy .\\src\\concore.jl .\\CZ\\concore.jl" in build

    run = read_script(out_dir, "run", windows=True)
    assert 'start /B /D "CZ" "julia" "controller_jl.jl" >"CZ"\\concoreout.txt' in run

    debug = read_script(out_dir, "debug", windows=True)
    assert 'start /D "CZ" cmd /K "julia" "controller_jl.jl"' in debug


def test_julia_executable_can_be_overridden_with_env(tmp_path):
    result, out_dir = build_study(
        tmp_path, "posix", {"CONCORE_JULIAEXE": "/opt/julia/bin/julia"}
    )
    assert result.returncode == 0, result.stdout + result.stderr

    run = read_script(out_dir, "run")
    assert "(cd CZ; /opt/julia/bin/julia controller_jl.jl >" in run


def test_docker_build_still_uses_docker_runtime(tmp_path):
    result, out_dir = build_study(tmp_path, "docker")
    assert result.returncode == 0, result.stdout + result.stderr

    assert (out_dir / "src" / "concore.jl").read_text() == (
        REPO_ROOT / "concoredocker.jl"
    ).read_text()
