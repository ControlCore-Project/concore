import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

pytestmark = [
    pytest.mark.skipif(shutil.which("g++") is None, reason="g++ not available"),
    pytest.mark.skipif(sys.platform == "win32", reason="concoredocker.hpp needs POSIX"),
]


def test_uses_same_port_dirs_as_docker_mounts(tmp_path):
    # mkconcore mounts docker volumes at /in1, /out1, ...
    (tmp_path / "in1").mkdir()
    (tmp_path / "out1").mkdir()
    (tmp_path / "in1" / "u").write_text("[5.0, 42.0]")
    (tmp_path / "in1" / "concore.maxtime").write_text("7")
    (tmp_path / "in1" / "concore.params").write_text("gain=3")

    source = tmp_path / "paths_test.cpp"
    binary = tmp_path / "paths_test"
    source.write_text(
        textwrap.dedent(
            f"""
            #include "concoredocker.hpp"
            #include <iostream>

            int main() {{
                Concore c;
                c.delay = 0;
                c.inpath = "{tmp_path}/in";
                c.outpath = "{tmp_path}/out";
                c.default_maxtime(100);
                c.load_params();
                std::vector<double> v = c.read(1, "u", "[0.0, 0.0]");
                std::cout << c.maxtime << " " << c.tryparam("gain", "none")
                          << " " << v[0] << std::endl;
                c.write(1, "y", {{7.0}});
                return 0;
            }}
            """
        )
    )
    subprocess.run(
        ["g++", "-std=c++17", "-I", str(REPO_ROOT), str(source), "-o", str(binary)],
        check=True,
    )
    result = subprocess.run(
        [str(binary)], cwd=tmp_path, capture_output=True, text=True, check=True
    )

    assert result.stdout.split() == ["7", "3", "42"]
    assert (tmp_path / "out1" / "y").read_text().startswith("[5")
