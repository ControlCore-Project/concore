import psutil
import os
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from concore_cli.commands._process_match import is_concore_process


def _scan_processes():
    """Return the running concore processes as plain data (raw numbers)."""
    processes = []
    current_pid = os.getpid()

    for proc in psutil.process_iter(
        ["pid", "name", "cmdline", "create_time", "memory_info", "cpu_percent"]
    ):
        try:
            cmdline = proc.info.get("cmdline") or []

            if proc.info["pid"] == current_pid:
                continue

            cmdline_str = " ".join(cmdline) if cmdline else ""

            try:
                cwd = proc.cwd()
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                cwd = None

            if is_concore_process(cmdline, cwd):
                try:
                    create_time = datetime.fromtimestamp(proc.info["create_time"])
                    uptime_seconds = int((datetime.now() - create_time).total_seconds())
                except (OSError, OverflowError, ValueError):
                    # Failed to calculate uptime
                    uptime_seconds = None

                try:
                    memory_mb = proc.info["memory_info"].rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    # Failed to get memory info
                    memory_mb = None

                command = (
                    " ".join(cmdline[:3]) if len(cmdline) >= 3 else cmdline_str[:50]
                )

                processes.append(
                    {
                        "pid": proc.info["pid"],
                        "name": proc.info.get("name", "unknown"),
                        "command": command,
                        "uptime_seconds": uptime_seconds,
                        "memory_mb": memory_mb,
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process may have exited or be inaccessible; safe to ignore
            continue

    return processes


def _format_uptime(seconds):
    if seconds is None:
        return "unknown"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def _format_memory(memory_mb):
    return "unknown" if memory_mb is None else f"{memory_mb:.1f} MB"


def status_data():
    """Machine-readable status: {"count": N, "processes": [...]}."""
    processes = _scan_processes()
    for proc in processes:
        if proc["memory_mb"] is not None:
            proc["memory_mb"] = round(proc["memory_mb"], 1)
    return {"count": len(processes), "processes": processes}


def show_status(console):
    console.print("[cyan]Scanning for concore processes...[/cyan]\n")

    try:
        concore_processes = _scan_processes()
    except Exception as e:
        console.print(f"[red]Error scanning processes:[/red] {str(e)}")
        return

    if not concore_processes:
        console.print(
            Panel.fit(
                "[yellow]No concore processes currently running[/yellow]",
                border_style="yellow",
            )
        )
    else:
        table = Table(
            title=f"Concore Processes ({len(concore_processes)} running)",
            show_header=True,
        )
        table.add_column("PID", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Uptime", style="yellow")
        table.add_column("Memory", style="magenta")
        table.add_column("Command", style="white")

        for proc in concore_processes:
            table.add_row(
                str(proc["pid"]),
                proc["name"],
                _format_uptime(proc["uptime_seconds"]),
                _format_memory(proc["memory_mb"]),
                proc["command"],
            )

        console.print(table)
        console.print()
        console.print("[dim]Use 'concore stop' to terminate all processes[/dim]")
