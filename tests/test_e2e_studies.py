import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# controller CZ and plant PZ from testsou/, each prints "retry=..." once its
# loop reaches simtime 100, so both printing it means the study ran through
STUDIES = [
    ("testZ", []),  # python <-> python
    ("testZC", ["g++"]),  # python controller, C++ plant
]
NODES = ["CZ", "PZ"]
TIMEOUT = 120

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="posix study scripts need bash"
)


def _finished(log):
    return log.exists() and re.search(r"^retry=", log.read_text(), re.M) is not None


@pytest.mark.parametrize("study,tools", STUDIES, ids=[s for s, _ in STUDIES])
def test_study_runs_to_completion(study, tools, tmp_path):
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        pytest.skip(f"{', '.join(missing)} not installed")

    out = tmp_path / study
    env = dict(os.environ, CONCORE_PYTHONEXE=sys.executable)
    subprocess.run(
        [
            sys.executable,
            "mkconcore.py",
            f"testsou/{study}.graphml",
            "testsou",
            str(out),
            "posix",
        ],
        cwd=REPO,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(["./build"], cwd=out, check=True, capture_output=True)

    run_log = out / "run.log"
    with run_log.open("w") as f:
        subprocess.run(["./run"], cwd=out, check=True, stdout=f, stderr=f)

    logs = [out / node / "concoreout.txt" for node in NODES]
    try:
        deadline = time.time() + TIMEOUT
        while not all(_finished(log) for log in logs) and time.time() < deadline:
            time.sleep(0.5)
    finally:
        subprocess.run(["./stop"], cwd=out, capture_output=True)

    if not all(_finished(log) for log in logs):
        details = [f"run.log:\n{run_log.read_text()}"]
        for log in logs:
            text = log.read_text() if log.exists() else "<missing>"
            details.append(
                f"{log.parent.name}/concoreout.txt (last lines):\n{text[-300:]}"
            )
        pytest.fail(
            f"{study} did not finish within {TIMEOUT}s\n\n" + "\n\n".join(details)
        )
