import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _templates_referenced_by_mkconcore():
    """Dockerfile.<ext> names that mkconcore.py can select in docker mode."""
    text = (REPO / "mkconcore.py").read_text()
    return sorted(set(re.findall(r'CONCOREPATH\s*\+\s*"/(Dockerfile\.\w+)"', text)))


def test_mkconcore_references_templates():
    assert _templates_referenced_by_mkconcore()


@pytest.mark.parametrize("name", _templates_referenced_by_mkconcore())
def test_referenced_dockerfile_template_exists(name):
    assert (REPO / name).is_file(), (
        f"mkconcore.py selects {name} but it is not in the repo"
    )


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ not installed")
@pytest.mark.parametrize("source", ["pmpymat.cpp", "ccpymat.cpp"])
def test_sample_cpp_node_compiles_like_docker_build(tmp_path, source):
    # Mirrors the generated Dockerfile: the source plus the two headers
    # that mkconcore copies into the build directory, compiled with plain g++.
    for name in (source, "concore.hpp", "concore_base.hpp"):
        shutil.copy(
            REPO / "testsou" / name if name == source else REPO / name, tmp_path
        )
    result = subprocess.run(
        ["g++", f"./{source}", "-o", str(tmp_path / "a.out")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
