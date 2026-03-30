import argparse
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys


JEROMQ_URL = "https://repo1.maven.org/maven2/org/zeromq/jeromq/0.6.0/jeromq-0.6.0.jar"


def parse_args():
    parser = argparse.ArgumentParser(description="Run Java e2e example smoke check")
    parser.add_argument("--jar", type=Path, help="Path to jeromq jar")
    parser.add_argument("--keep-study", action="store_true", help="Keep generated study files")
    return parser.parse_args()

def main():
    args = parse_args()
    here = Path(__file__).resolve().parent
    repo_root = here.parents[1]
    study_dir = here / "study"
    jar_path = args.jar or (repo_root / ".ci-cache" / "java" / "jeromq-0.6.0.jar")

    if not jar_path.exists():
        raise FileNotFoundError(
            f"Missing jeromq jar at {jar_path}. Download from {JEROMQ_URL} or pass --jar."
        )

    if study_dir.exists():
        shutil.rmtree(study_dir)
    (study_dir / "1").mkdir(parents=True, exist_ok=True)
    (study_dir / "1" / "concore.maxtime").write_text("20", encoding="utf-8")

    subprocess.run(
        [
            "javac",
            "-cp",
            str(jar_path),
            str(repo_root / "concoredocker.java"),
            str(here / "pm_java.java"),
        ],
        check=True,
        cwd=repo_root,
    )

    env = os.environ.copy()
    env["CONCORE_STUDY_DIR"] = str(study_dir)
    classpath = os.pathsep.join([str(repo_root), str(here), str(jar_path)])

    py_log = open(study_dir / "controller.log", "w", encoding="utf-8")
    java_log = open(study_dir / "pm_java.log", "w", encoding="utf-8")

    py_proc = subprocess.Popen(
        [sys.executable, str(here / "controller.py")],
        cwd=repo_root,
        env=env,
        stdout=py_log,
        stderr=subprocess.STDOUT,
    )
    java_proc = subprocess.Popen(
        ["java", "-cp", classpath, "pm_java"],
        cwd=repo_root,
        env=env,
        stdout=java_log,
        stderr=subprocess.STDOUT,
    )

    try:
        py_rc = py_proc.wait(timeout=45)
        java_rc = java_proc.wait(timeout=45)
    except subprocess.TimeoutExpired:
        py_proc.kill()
        java_proc.kill()
        py_log.close()
        java_log.close()
        raise RuntimeError("Timed out waiting for node processes")

    py_log.close()
    java_log.close()

    if py_rc != 0 or java_rc != 0:
        raise RuntimeError(
            f"Node process failed (controller={py_rc}, pm_java={java_rc}). "
            f"See {study_dir / 'controller.log'} and {study_dir / 'pm_java.log'}."
        )

    u_path = study_dir / "1" / "u"
    ym_path = study_dir / "1" / "ym"
    if not u_path.exists() or not ym_path.exists():
        raise RuntimeError("Expected output files were not produced")

    u_val = ast.literal_eval(u_path.read_text(encoding="utf-8"))
    ym_val = ast.literal_eval(ym_path.read_text(encoding="utf-8"))
    if not isinstance(u_val, list) or len(u_val) < 2:
        raise RuntimeError("u output did not match expected wire format")
    if not isinstance(ym_val, list) or len(ym_val) < 2:
        raise RuntimeError("ym output did not match expected wire format")

    print("smoke_check passed")
    print(f"u: {u_val}")
    print(f"ym: {ym_val}")

    if not args.keep_study and study_dir.exists():
        shutil.rmtree(study_dir)

    class_file = here / "pm_java.class"
    if class_file.exists():
        class_file.unlink()


if __name__ == "__main__":
    main()
