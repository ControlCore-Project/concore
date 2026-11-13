"""Generated MATLAB/Octave studies must ship every runtime file they call.

concore_read.m, concore_write.m and concore_initval.m call
concore_literal_eval / concore_literal_serialize. mkconcore.py copies the
runtime .m files one by one, and these two helpers used to be missing from
the generated src/ folder, so a MATLAB node failed on its first read/write.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH = REPO_ROOT / "demo" / "sampleM.graphml"
HELPERS = ("concore_literal_eval.m", "concore_literal_serialize.m")


def _generate(tmp_path, concoretype):
    out = tmp_path / f"out_{concoretype}"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "mkconcore.py"),
            str(GRAPH),
            str(REPO_ROOT / "demo"),
            str(out),
            concoretype,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    return out


@pytest.mark.parametrize("concoretype", ["posix", "windows", "docker"])
def test_literal_helpers_are_copied(tmp_path, concoretype):
    src = _generate(tmp_path, concoretype) / "src"
    for name in HELPERS:
        assert (src / name).is_file(), f"{name} missing from generated src/"


@pytest.mark.parametrize("concoretype", ["posix", "windows", "docker"])
def test_every_concore_function_called_is_present(tmp_path, concoretype):
    """Any concore_* function referenced by a copied runtime file must exist."""
    src = _generate(tmp_path, concoretype) / "src"
    available = {p.stem for p in src.glob("concore_*.m")}
    missing = set()
    for runtime_file in src.glob("concore_*.m"):
        text = runtime_file.read_text()
        for called in re.findall(r"\bconcore_[a-z_]+\b", text):
            if called not in available and called != runtime_file.stem:
                missing.add((runtime_file.name, called))
    assert not missing, f"runtime files call functions that were not copied: {missing}"


@pytest.mark.parametrize("concoretype", ["posix", "windows"])
def test_build_script_copies_helpers_into_node_folders(tmp_path, concoretype):
    """The build script must use a glob (not a fixed list) so helpers reach nodes."""
    out = _generate(tmp_path, concoretype)
    script = out / ("build.bat" if concoretype == "windows" else "build")
    assert "concore_*.m" in script.read_text()
