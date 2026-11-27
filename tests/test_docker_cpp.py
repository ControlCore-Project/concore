import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_dockerfile_cpp_template_exists():
    assert (REPO / "Dockerfile.cpp").is_file()


def test_docker_build_for_cpp_node(tmp_path):
    out = tmp_path / "study"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "mkconcore.py"),
            str(REPO / "testsou" / "testSM1.graphml"),
            str(REPO / "testsou"),
            str(out),
            "docker",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    dockerfiles = sorted((out / "src").glob("Dockerfile.*"))
    assert dockerfiles
    for df in dockerfiles:
        text = df.read_text()
        assert "g++" in text
        assert "RUN g++ ./" in text
        assert 'CMD ["./a.out"]' in text
