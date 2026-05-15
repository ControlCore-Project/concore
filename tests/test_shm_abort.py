import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(
    shutil.which("g++") is None,
    reason="g++ not available",
)


@pytest.fixture(autouse=True)
def _skip_windows():
    if sys.platform == "win32":
        pytest.skip("SHM requires POSIX")


def _compile_and_run(payload_size):
    with tempfile.TemporaryDirectory(prefix="concore_shm_test_") as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "concore.oport").write_text('{"1": "1"}', encoding="utf-8")

        source_file = temp_path / "shm_abort_test.cpp"
        binary_file = temp_path / "shm_abort_test"
        source_file.write_text(
            textwrap.dedent(
                f"""
                #include "concore.hpp"
                #include <exception>
                #include <string>

                int main() {{
                    try {{
                        Concore concore;
                        concore.delay = 0;
                        concore.simtime = 0;
                        std::string payload({payload_size}, 'a');
                        concore.write(1, "payload", payload);
                        return 0;
                    }} catch (const std::exception& error) {{
                        std::cerr << error.what() << std::endl;
                        return 1;
                    }}
                }}
                """
            ).lstrip(),
            encoding="utf-8",
        )

        compile_result = subprocess.run(
            [
                "g++",
                "-std=c++17",
                "-I",
                str(REPO_ROOT),
                "-o",
                str(binary_file),
                str(source_file),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=temp_path,
        )
        if compile_result.returncode != 0:
            pytest.fail(f"g++ compile failed:\n{compile_result.stderr}")

        return subprocess.run(
            [str(binary_file)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_path,
        )


def test_oversized_payload_throws():
    result = _compile_and_run(5000)
    assert result.returncode != 0
    assert "Aborting" in result.stderr
    assert "truncated" not in result.stderr.lower()


def test_within_limit_succeeds():
    result = _compile_and_run(100)
    assert result.returncode == 0
    assert result.stderr == ""


def test_exactly_at_limit_throws():
    result = _compile_and_run(4096)
    assert result.returncode != 0
    assert "Aborting" in result.stderr


def test_one_under_limit_succeeds():
    result = _compile_and_run(4095)
    assert result.returncode == 0
    assert result.stderr == ""
