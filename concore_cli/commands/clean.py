import re
from pathlib import Path

import click
import psutil

from .watch import _find_nodes

PORT_RE = re.compile(r"^(in|out)\d+$")
NODE_FILES = ("concoreout.txt", "concorepid")


def _edge_dirs(study_path, nodes):
    """Edge directories: what each node's in*/out* ports point at."""
    node_names = {name for name, _ in nodes}
    edges = {}
    for _, node_path in nodes:
        for port in node_path.iterdir():
            if not PORT_RE.match(port.name):
                continue
            target = port.resolve()
            if (
                target.is_dir()
                and target.parent == study_path
                and target.name not in node_names
                and target.name != "src"
            ):
                edges[target.name] = target
    return sorted(edges.values())


def _files_to_remove(study_path, nodes):
    found = []
    for _, node_path in nodes:
        for name in NODE_FILES:
            f = node_path / name
            if f.is_file() and not f.is_symlink():
                found.append(f)
    for edge in _edge_dirs(study_path, nodes):
        for f in sorted(edge.iterdir()):
            if f.is_file() and not f.is_symlink():
                found.append(f)
    return found


def _running_nodes(nodes):
    running = []
    for name, node_path in nodes:
        pidfile = node_path / "concorepid"
        try:
            pid = int(pidfile.read_text().strip())
        except (OSError, ValueError):
            continue
        if psutil.pid_exists(pid):
            try:
                if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
                    continue
            except psutil.Error:
                continue
            running.append((name, pid))
    return running


def clean_study(study_dir, dry_run, yes, force, console):
    study_path = Path(study_dir).resolve()
    if not study_path.is_dir():
        console.print(f"[red]Error:[/red] '{study_dir}' is not a directory")
        return False

    nodes = _find_nodes(study_path)
    if not nodes:
        console.print(
            "[red]Error:[/red] no nodes found. "
            "Point to a built study directory (run build first)."
        )
        return False

    running = _running_nodes(nodes)
    if running and not force and not dry_run:
        names = ", ".join(f"{n} (pid {p})" for n, p in running)
        console.print(f"[red]Error:[/red] study is still running: {names}")
        console.print("[dim]Stop it first (concore stop), or use --force.[/dim]")
        return False

    files = _files_to_remove(study_path, nodes)
    if not files:
        console.print("[green]Nothing to clean.[/green]")
        return True

    for f in files:
        console.print(f.relative_to(study_path).as_posix(), markup=False)

    if dry_run:
        console.print(f"\n[cyan]Dry run:[/cyan] {len(files)} file(s) would be removed.")
        return True

    if not yes and not click.confirm(f"\nRemove {len(files)} file(s)?", default=False):
        console.print("[yellow]Cancelled.[/yellow]")
        return True

    removed = 0
    for f in files:
        try:
            f.unlink()
            removed += 1
        except OSError as e:
            console.print(f"[red]Could not remove[/red] {f.name}: {e}", markup=True)
    console.print(f"[green]Removed {removed} file(s).[/green]")
    return removed == len(files)
