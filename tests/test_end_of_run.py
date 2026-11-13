import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Same shape as testsou/cpymat.py and testsou/pmpymat.py: the controller writes
# its init values back to u right after its loop. The plant is slower than the
# controller, so it can miss the last real u (see #608).
CONTROLLER = """
import concore
concore.inpath, concore.outpath = {ym!r}, {u!r}
concore.delay = 0.01
init = "[0.0,0.0,0.0]"
u = concore.initval(init)
while concore.simtime < 20:
    while concore.unchanged():
        ym = concore.read(1, "ym", init)
    u[0] = ym[0] + 1
    concore.write(1, "u", u)
concore.write(1, "u", init)
print("done")
"""

PLANT = """
import concore
concore.inpath, concore.outpath = {u!r}, {ym!r}
concore.delay = 0.05
init = "[0.0,0.0,0.0]"
ym = concore.initval(init)
while concore.simtime < 20:
    while concore.unchanged():
        u = concore.read(1, "u", init)
    ym[0] = u[0] + 10000
    concore.write(1, "ym", ym, delta=1)
concore.write(1, "ym", init)
print("done")
"""


def test_slow_plant_still_finishes(tmp_path):
    ports = {"u": str(tmp_path / "u"), "ym": str(tmp_path / "ym")}
    for base in ports.values():
        os.makedirs(base + "1")
    env = dict(os.environ, PYTHONPATH=str(REPO))

    procs = {}
    for name, source in (("controller", CONTROLLER), ("plant", PLANT)):
        node = tmp_path / name
        node.mkdir()
        (node / "node.py").write_text(source.format(**ports))
        procs[name] = subprocess.Popen(
            [sys.executable, "node.py"],
            cwd=node,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    deadline = time.time() + 60
    while any(p.poll() is None for p in procs.values()) and time.time() < deadline:
        time.sleep(0.2)
    hung = [name for name, p in procs.items() if p.poll() is None]
    for p in procs.values():
        if p.poll() is None:
            p.kill()
    for p in procs.values():
        p.wait()

    assert not hung, f"{', '.join(hung)} never reached the end of its loop"
    for name, p in procs.items():
        assert "done" in p.stdout.read(), name
