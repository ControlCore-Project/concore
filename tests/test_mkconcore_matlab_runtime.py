import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# The script that copies src/concore_*.m into each node folder, per target type.
BUILD_SCRIPT = {"posix": "build", "windows": "build.bat", "docker": "build"}

# A call such as concore_literal_eval(x) in the body of a .m file.
CALL = re.compile(r"\b(concore_\w+)\s*\(")


@pytest.fixture(params=sorted(BUILD_SCRIPT))
def generated_study(request, tmp_path):
    """Generate demo/sampleM.graphml (MATLAB/Octave nodes) for one target type."""
    out = tmp_path / "out"
    subprocess.run(
        [
            sys.executable,
            "mkconcore.py",
            "demo/sampleM.graphml",
            "demo",
            str(out),
            request.param,
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    return request.param, out


def _called_concore_functions(path):
    body = "\n".join(
        line
        for line in path.read_text().splitlines()
        if not line.lstrip().startswith(("%", "#"))
    )
    return set(CALL.findall(body))


def test_every_concore_function_called_by_a_copied_file_is_copied(generated_study):
    target, out = generated_study
    src = out / "src"
    # concore_read.m and concore_write.m depend on these two (#648)
    for helper in ("concore_literal_eval.m", "concore_literal_serialize.m"):
        assert (src / helper).exists(), f"{target}: {helper} not copied into src/"

    runtime_files = sorted(src.glob("concore_*.m")) + [src / "import_concore.m"]

    missing = {
        f"{path.name} calls {name}"
        for path in runtime_files
        for name in _called_concore_functions(path)
        if not (src / f"{name}.m").exists()
    }
    assert not missing, f"{target}: not copied into src/: {sorted(missing)}"


def test_build_script_copies_all_concore_m_files_into_the_node(generated_study):
    target, out = generated_study
    # The wildcard is what carries every file above from src/ into the node folder.
    assert "concore_*.m" in (out / BUILD_SCRIPT[target]).read_text()
