import os
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


@pytest.mark.parametrize(
    ("header", "key"),
    [("concore.hpp", 543210), ("concoredocker.hpp", 543212)],
)
def test_shared_segment_lives_until_last_writer_exits(header, key):
    with tempfile.TemporaryDirectory(prefix="concore_shm_test_") as temp_dir:
        temp_path = Path(temp_dir)
        key += os.getpid() * 2
        (temp_path / "concore.oport").write_text(f'{{"{key}": "1"}}', encoding="utf-8")

        source_file = temp_path / "shm_lifecycle_test.cpp"
        binary_file = temp_path / "shm_lifecycle_test"
        source_file.write_text(
            textwrap.dedent(
                f"""
                #include "{header}"
                #include <cstring>
                #include <iostream>
                #include <string>
                #include <sys/ipc.h>
                #include <sys/sem.h>
                #include <sys/shm.h>
                #include <vector>

                int probe(key_t key) {{
                    int shm_id = shmget(key, 4096, 0666);
                    int sem_id = semget(key + 1, 1, 0666);
                    if (shm_id == -1 || sem_id == -1)
                        return 2;

                    char* data = static_cast<char*>(shmat(shm_id, nullptr, 0));
                    if (data == reinterpret_cast<char*>(-1))
                        return 3;
                    std::string payload(data + 8, strnlen(data + 8, 4087));
                    shmdt(data);
                    return payload == "[0,42]" ? 0 : 4;
                }}

                int main(int argc, char** argv) {{
                    std::string mode = argv[1];
                    key_t key = static_cast<key_t>(std::stoi(argv[2]));
                    if (mode == "probe")
                        return probe(key);
                    if (mode == "cleanup") {{
                        int shm_id = shmget(key, 4096, 0666);
                        int sem_id = semget(key + 1, 1, 0666);
                        if (shm_id != -1)
                            shmctl(shm_id, IPC_RMID, nullptr);
                        if (sem_id != -1)
                            semctl(sem_id, 0, IPC_RMID);
                        return 0;
                    }}

                    Concore concore;
                    if (mode == "hold") {{
                        concore.delay = 0;
                        concore.simtime = 0;
                        concore.write(1, "payload", std::vector<double>{{42}});
                    }}
                    if (mode == "hold" || mode == "wait") {{
                        std::cout << "ready" << std::endl;
                        std::cin.get();
                    }}
                    return 0;
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

        command = [str(binary_file)]
        subprocess.run(command + ["cleanup", str(key)], cwd=temp_path, check=True)
        writers = []

        def start_writer(mode):
            writer = subprocess.Popen(
                command + [mode, str(key)],
                cwd=temp_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            writers.append(writer)
            assert writer.stdout.readline().strip() == "ready"
            return writer

        try:
            creator = start_writer("hold")
            attached = start_writer("wait")
            assert (
                subprocess.run(command + ["probe", str(key)], cwd=temp_path).returncode
                == 0
            )
            attached.communicate(input="\n", timeout=5)
            assert attached.returncode == 0
            assert (
                subprocess.run(command + ["probe", str(key)], cwd=temp_path).returncode
                == 0
            )

            attached = start_writer("wait")
            creator.communicate(input="\n", timeout=5)
            assert creator.returncode == 0
            assert (
                subprocess.run(command + ["probe", str(key)], cwd=temp_path).returncode
                == 0
            )
            attached.communicate(input="\n", timeout=5)
            assert attached.returncode == 0
            assert (
                subprocess.run(command + ["probe", str(key)], cwd=temp_path).returncode
                == 2
            )
        finally:
            for writer in writers:
                if writer.poll() is None:
                    writer.kill()
                    writer.wait()
            subprocess.run(command + ["cleanup", str(key)], cwd=temp_path, check=False)
