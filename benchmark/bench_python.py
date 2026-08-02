import argparse
import os
import platform
import statistics
import sys
import tempfile
import time
from ast import literal_eval
from pathlib import Path


PAYLOAD = [1.0, 2.0, 3.0, 4.0]
WIRE = "[0.0, 1.0, 2.0, 3.0, 4.0]"
INITIAL = "[0.0, 0.0, 0.0, 0.0, 0.0]"


def measure(label, unit, function, expected, iterations, warmup, repeats):
    result = None
    for _ in range(warmup):
        result = function()
    if result != expected:
        raise RuntimeError(f"{label} warmup returned an unexpected value")

    elapsed = []
    for _ in range(repeats):
        start = time.perf_counter()
        for _ in range(iterations):
            result = function()
        elapsed.append(time.perf_counter() - start)
        if result != expected:
            raise RuntimeError(f"{label} returned an unexpected value")

    seconds = statistics.median(elapsed)
    rate = iterations / seconds
    print(f"{label:<24} {seconds * 1e3:>12.3f} {rate:>18.0f} {unit}/s")


def load_concore(workdir):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    old_cwd = os.getcwd()
    try:
        os.chdir(workdir)
        import concore
    finally:
        os.chdir(old_cwd)
    return concore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    iterations = 100 if args.quick else 5_000
    warmup = 10 if args.quick else 100
    repeats = 3 if args.quick else 5

    print(
        f"Python {platform.python_version()} | {platform.system()} {platform.machine()}"
    )
    print(f"iterations={iterations} warmup={warmup} repeats={repeats}")
    print()
    print(f"{'workload':<24} {'median ms':>12} {'rate':>18}")
    print("-" * 58)

    measure(
        "Parse wire",
        "operations",
        lambda: literal_eval(WIRE),
        [0.0] + PAYLOAD,
        iterations,
        warmup,
        repeats,
    )
    measure(
        "Format wire",
        "operations",
        lambda: str([0.0] + PAYLOAD),
        WIRE,
        iterations,
        warmup,
        repeats,
    )

    with tempfile.TemporaryDirectory() as tempdir:
        concore = load_concore(tempdir)
        path = os.path.join(tempdir, "io")
        os.makedirs(path + "1")
        concore.inpath = path
        concore.outpath = path
        concore.delay = 0
        concore.simtime = 0

        def file_roundtrip():
            concore.write(1, "request", PAYLOAD)
            request = concore.read(1, "request", INITIAL)
            concore.write(1, "reply", request)
            reply = concore.read(1, "reply", INITIAL)
            concore.s = ""
            concore.olds = ""
            return reply

        measure(
            "File round trip",
            "round trips",
            file_roundtrip,
            PAYLOAD,
            iterations,
            warmup,
            repeats,
        )
        concore.terminate_zmq()


if __name__ == "__main__":
    main()
