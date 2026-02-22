import time
import re
from pathlib import Path
from ast import literal_eval
from datetime import datetime
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.console import Group


def watch_study(study_dir, interval, once, console):
    study_path = Path(study_dir).resolve()
    if not study_path.is_dir():
        console.print(f"[red]Error:[/red] '{study_dir}' is not a directory")
        return

    nodes = _find_nodes(study_path)
    edges = _find_edges(study_path, nodes)

    if not nodes and not edges:
        console.print(Panel(
            "[yellow]No nodes or edge directories found.[/yellow]\n"
            "[dim]Make sure you point to a built study directory (run makestudy/build first).[/dim]",
            title="concore watch", border_style="yellow"))
        return

    if once:
        output = _build_display(study_path, nodes, edges)
        console.print(output)
        return

    console.print(f"[cyan]Watching:[/cyan] {study_path}")
    console.print(f"[dim]Refresh every {interval}s — Ctrl+C to stop[/dim]\n")

    try:
        with Live(console=console, refresh_per_second=1, screen=False) as live:
            while True:
                nodes = _find_nodes(study_path)
                edges = _find_edges(study_path, nodes)
                live.update(_build_display(study_path, nodes, edges))
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch stopped.[/yellow]")


def _build_display(study_path, nodes, edges):
    parts = []

    header = Text()
    header.append("Study ", style="bold cyan")
    header.append(study_path.name, style="bold white")
    header.append(f"  |  {len(nodes)} node(s), {len(edges)} edge(s)", style="dim")
    parts.append(header)

    if edges:
        parts.append(Text())
        parts.append(_edge_table(edges))

    if nodes:
        parts.append(Text())
        parts.append(_node_table(nodes))

    if not edges and not nodes:
        parts.append(Panel("[yellow]No data yet[/yellow]",
                           border_style="yellow"))

    return Group(*parts)


def _edge_table(edges):
    table = Table(title="Edges (port data)", show_header=True,
                  title_style="bold cyan", expand=True)
    table.add_column("Edge", style="green", min_width=10)
    table.add_column("Port File", style="cyan")
    table.add_column("Simtime", style="yellow", justify="right")
    table.add_column("Value", style="white")
    table.add_column("Age", style="magenta", justify="right")

    now = time.time()
    for edge_name, edge_path in sorted(edges):
        files = _read_edge_files(edge_path)
        if not files:
            table.add_row(edge_name, "[dim]—[/dim]", "", "[dim]empty[/dim]", "")
            continue
        first = True
        for fname, simtime_val, value_str, mtime in files:
            age_str = _format_age(now, mtime)
            label = edge_name if first else ""
            st = str(simtime_val) if simtime_val is not None else "—"
            table.add_row(label, fname, st, value_str, age_str)
            first = False

    return table


def _node_table(nodes):
    table = Table(title="Nodes", show_header=True,
                  title_style="bold cyan", expand=True)
    table.add_column("Node", style="green", min_width=10)
    table.add_column("Ports (in)", style="cyan")
    table.add_column("Ports (out)", style="cyan")
    table.add_column("Source", style="dim")

    for node_name, node_path in sorted(nodes):
        in_dirs = sorted(d.name for d in node_path.iterdir()
                         if d.is_dir() and re.match(r'^in\d+$', d.name))
        out_dirs = sorted(d.name for d in node_path.iterdir()
                          if d.is_dir() and re.match(r'^out\d+$', d.name))
        src = _detect_source(node_path)
        table.add_row(
            node_name,
            ", ".join(in_dirs) if in_dirs else "—",
            ", ".join(out_dirs) if out_dirs else "—",
            src,
        )

    return table


def _find_nodes(study_path):
    nodes = []
    port_re = re.compile(r'^(in|out)\d+$')
    skip = {'src', '__pycache__', '.git'}
    for entry in study_path.iterdir():
        if not entry.is_dir() or entry.name in skip or entry.name.startswith('.'):
            continue
        try:
            has_ports = any(c.is_dir() and port_re.match(c.name)
                           for c in entry.iterdir())
        except PermissionError:
            continue
        if has_ports:
            nodes.append((entry.name, entry))
    return nodes


def _find_edges(study_path, nodes=None):
    if nodes is None:
        nodes = _find_nodes(study_path)
    node_names = {name for name, _ in nodes}
    skip = {'src', '__pycache__', '.git'}
    edges = []
    for entry in study_path.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in skip or entry.name in node_names or entry.name.startswith('.'):
            continue
        try:
            has_file = any(f.is_file() for f in entry.iterdir())
        except PermissionError:
            continue
        if has_file:
            edges.append((entry.name, entry))
    return edges


def _read_edge_files(edge_path):
    results = []
    try:
        children = sorted(edge_path.iterdir())
    except PermissionError:
        return results
    for f in children:
        if not f.is_file():
            continue
        # skip concore internal files
        if f.name.startswith('concore.'):
            continue
        simtime_val, value_str = _parse_port_file(f)
        try:
            mtime = f.stat().st_mtime
        except OSError:
            mtime = 0
        results.append((f.name, simtime_val, value_str, mtime))
    return results


def _detect_source(node_path):
    for ext in ('*.py', '*.m', '*.cpp', '*.v', '*.sh', '*.java'):
        matches = list(node_path.glob(ext))
        for m in matches:
            # skip concore library copies
            if m.name.startswith('concore'):
                continue
            return m.name
    return "—"


def _parse_port_file(port_file):
    try:
        content = port_file.read_text().strip()
        if not content:
            return None, "(empty)"
        val = literal_eval(content)
        if isinstance(val, list) and len(val) > 0:
            simtime = val[0] if isinstance(val[0], (int, float)) else None
            data = val[1:] if simtime is not None else val
            data_str = str(data)
            if len(data_str) > 50:
                data_str = data_str[:47] + "..."
            return simtime, data_str
        raw = str(val)
        return None, raw[:50] if len(raw) > 50 else raw
    except Exception:
        try:
            raw = port_file.read_text().strip()
            return None, raw[:50] if raw else "(empty)"
        except Exception:
            return None, "(read error)"


def _format_age(now, mtime):
    if mtime == 0:
        return "—"
    age = now - mtime
    if age < 3:
        return "[bold green]now[/bold green]"
    elif age < 60:
        return f"{int(age)}s"
    elif age < 3600:
        return f"{int(age // 60)}m"
    else:
        return datetime.fromtimestamp(mtime).strftime("%H:%M:%S")
