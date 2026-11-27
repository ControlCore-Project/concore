import time
from pathlib import Path

from .watch import _find_nodes

LOG_NAME = "concoreout.txt"
TAIL_CHUNK = 1024 * 1024
POLL_SECONDS = 0.5


def _tail(path, lines):
    """Return the last `lines` lines of a text file without loading all of it."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - TAIL_CHUNK))
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    if lines <= 0:
        return []
    return text.splitlines()[-lines:]


def _emit(console, line, prefix=None):
    text = f"[{prefix}] {line}" if prefix else line
    console.print(text, markup=False, highlight=False)


def logs_study(study_dir, node, lines, follow, console):
    study_path = Path(study_dir).resolve()
    if not study_path.is_dir():
        console.print(f"[red]Error:[/red] '{study_dir}' is not a directory")
        return False

    nodes = sorted(_find_nodes(study_path), key=lambda item: item[0])

    if node is not None:
        if node not in [name for name, _ in nodes]:
            known = ", ".join(name for name, _ in nodes) or "none"
            console.print(f"[red]Error:[/red] no node '{node}' in {study_path}")
            console.print(f"[dim]Nodes: {known}[/dim]")
            return False
        selected = [(n, p) for n, p in nodes if n == node]
    else:
        selected = nodes

    selected = [(n, p / LOG_NAME) for n, p in selected if (p / LOG_NAME).is_file()]
    if not selected:
        console.print(
            f"[yellow]No {LOG_NAME} found.[/yellow] "
            "[dim]Run the study first (concore run).[/dim]"
        )
        return True

    single = len(selected) == 1
    offsets = {}
    for name, path in selected:
        if not single:
            console.print(f"[bold cyan]== {name} ==[/bold cyan]")
        for line in _tail(path, lines):
            _emit(console, line, None if single else name)
        offsets[name] = path.stat().st_size

    if not follow:
        return True

    console.print("[dim]Following — Ctrl+C to stop[/dim]")
    pending = {name: b"" for name, _ in selected}
    try:
        while True:
            for name, path in selected:
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                if size < offsets[name]:  # file was truncated by a new run
                    offsets[name] = 0
                    pending[name] = b""
                if size == offsets[name]:
                    continue
                with open(path, "rb") as f:
                    f.seek(offsets[name])
                    chunk = f.read()
                offsets[name] += len(chunk)
                buf = pending[name] + chunk
                *complete, pending[name] = buf.split(b"\n")
                for raw in complete:
                    _emit(
                        console,
                        raw.decode("utf-8", errors="replace").rstrip("\r"),
                        None if single else name,
                    )
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped following.[/yellow]")
    return True
