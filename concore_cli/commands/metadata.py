import hashlib
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

from concore_cli import __version__


def _checksum_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _detect_tools() -> dict:
    tool_candidates = {
        "python": ["python", "python3"],
        "g++": ["g++"],
        "docker": ["docker"],
        "octave": ["octave"],
        "iverilog": ["iverilog"],
    }
    detected = {}
    for tool_name, candidates in tool_candidates.items():
        detected_path = None
        for candidate in candidates:
            detected_path = shutil.which(candidate)
            if detected_path:
                break
        detected[tool_name] = detected_path or "not found"
    return detected


def write_study_metadata(study_path: Path, generated_by: str, workflow_file: Path = None):
    checksums = {}
    checksum_candidates = [
        "workflow.graphml",
        "docker-compose.yml",
        "concore.toml",
        "runner.py",
        "README.md",
        "build",
        "run",
        "build.bat",
        "run.bat",
    ]

    if workflow_file is not None and workflow_file.exists():
        checksums[workflow_file.name] = _checksum_file(workflow_file)

    for relative_name in checksum_candidates:
        file_path = study_path / relative_name
        if file_path.exists() and file_path.is_file():
            checksums[relative_name] = _checksum_file(file_path)

    metadata = {
        "generated_by": generated_by,
        "concore_version": __version__,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "study_name": study_path.name,
        "working_directory": str(study_path.resolve()),
        "tools_detected": _detect_tools(),
        "checksums": checksums,
        "schema_version": 1,
    }

    metadata_path = study_path / "STUDY.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata_path