import os
import re
import subprocess
import sys
import time
from pathlib import Path

import psutil

EXIT_TIMEOUT = 124
EXIT_INTERRUPTED = 130
PID_WAIT_SECONDS = 10.0
POLL_SECONDS = 0.5


def _find_script(study_path, name):
    """Return the generated `<name>` script for this platform, or None."""
    if sys.platform == "win32":
        candidate = study_path / f"{name}.bat"
        if candidate.is_file():
            return candidate
    candidate = study_path / name
    if candidate.is_file():
        return candidate
    return None


def _command(script):
    if script.suffix.lower() == ".bat":
        return ["cmd", "/c", str(script)]
    if os.access(script, os.X_OK):
        return [str(script)]
    return ["bash", str(script)]


def _node_dirs(run_script):
    """Node folders started by a POSIX run script: lines like `(cd CZ; ... &`."""
    try:
        text = run_script.read_text()
    except OSError:
        return []
    dirs = []
    for match in re.finditer(r"\(cd\s+([^;\s]+)\s*;", text):
        folder = match.group(1).strip("'\"")
        if folder not in dirs:
            dirs.append(folder)
    return dirs


def _read_pid(pid_file, newer_than):
    """Read a pid file written by this run (older files are stale)."""
    try:
        if pid_file.stat().st_mtime < newer_than:
            return None
        return int(pid_file.read_text().strip())
    except (OSError, ValueError):
        return None


def _alive(pid):
    try:
        return psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return True


def _collect_pids(study_path, node_dirs, started, console):
    """Wait briefly for each node's pid file, then return {folder: pid}."""
    pids = {}
    deadline = time.monotonic() + PID_WAIT_SECONDS
    while True:
        for folder in node_dirs:
            if folder not in pids:
                pid = _read_pid(study_path / folder / "concorepid", started)
                if pid is not None:
                    pids[folder] = pid
        if len(pids) == len(node_dirs) or time.monotonic() > deadline:
            break
        time.sleep(0.2)
    for folder in node_dirs:
        if folder not in pids:
            console.print(
                f"[yellow]Warning:[/yellow] no process id found for node '{folder}'"
            )
    return pids


def _stop_study(study_path, pids):
    """Stop one study: run its own stop script, then make sure its pids are gone."""
    stop_script = _find_script(study_path, "stop")
    if stop_script is not None:
        subprocess.run(
            _command(stop_script),
            cwd=study_path,
            capture_output=True,
            text=True,
        )
    for pid in pids.values():
        if _alive(pid):
            try:
                psutil.Process(pid).kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


def run_study(study_dir, console, build=False, wait=False, timeout=None):
    """Start a built study. Returns the process exit code for the command."""
    study_path = Path(study_dir).resolve()
    if not study_path.is_dir():
        console.print(f"[red]Error:[/red] '{study_dir}' is not a directory")
        return 1
    if timeout is not None and not wait:
        console.print("[red]Error:[/red] --timeout requires --wait")
        return 1

    run_script = _find_script(study_path, "run")
    if run_script is None:
        console.print(
            f"[red]Error:[/red] No run script found in {study_path}\n"
            "[dim]Build the workflow first: concore build <workflow.graphml> "
            "--output <dir>[/dim]"
        )
        return 1

    if build:
        build_script = _find_script(study_path, "build")
        if build_script is None:
            console.print(f"[red]Error:[/red] No build script found in {study_path}")
            return 1
        console.print("[cyan]Building study...[/cyan]")
        build_result = subprocess.run(_command(build_script), cwd=study_path)
        if build_result.returncode != 0:
            console.print(
                f"[red]Build failed[/red] (exit code {build_result.returncode})"
            )
            return build_result.returncode

    node_dirs = _node_dirs(run_script)
    console.print(f"[cyan]Starting study:[/cyan] {study_path}")
    started = time.time() - 1
    run_result = subprocess.run(_command(run_script), cwd=study_path)
    if run_result.returncode != 0:
        console.print(
            f"[red]Run script failed[/red] (exit code {run_result.returncode})"
        )
        return run_result.returncode

    if not wait:
        console.print(
            "[green]✓[/green] Study started\n"
            "[dim]Monitor it with: concore watch <dir>   "
            "Stop it with: concore stop[/dim]"
        )
        return 0

    if not node_dirs:
        console.print(
            "[yellow]Warning:[/yellow] --wait needs a study that records node "
            "process ids (a posix/macOS build). The study was started, but "
            "there is nothing to wait for."
        )
        return 0

    pids = _collect_pids(study_path, node_dirs, started, console)
    console.print("[dim]Waiting for the study to finish (Ctrl+C to stop it)...[/dim]")
    start = time.monotonic()
    try:
        while any(_alive(pid) for pid in pids.values()):
            if timeout is not None and time.monotonic() - start > timeout:
                console.print(
                    f"[yellow]Timeout:[/yellow] study still running after {timeout}s, stopping it"
                )
                _stop_study(study_path, pids)
                return EXIT_TIMEOUT
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted:[/yellow] stopping the study...")
        _stop_study(study_path, pids)
        return EXIT_INTERRUPTED

    console.print("[green]✓[/green] Study finished")
    return 0
