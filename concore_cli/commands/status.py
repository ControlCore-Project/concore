import psutil
import os
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

def show_status(console):
    console.print("[cyan]Scanning for concore processes...[/cyan]\n")
    
    concore_processes = []
    
    try:
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
            try:
                cmdline = proc.info.get('cmdline') or []
                name = proc.info.get('name', '').lower()
                
                if proc.info['pid'] == current_pid:
                    continue
                
                cmdline_str = ' '.join(cmdline) if cmdline else ''
                
                is_concore = (
                    'concore' in cmdline_str.lower() or
                    'concore.py' in cmdline_str.lower() or
                    any('concorekill.bat' in str(item) for item in cmdline) or
                    (name in ['python.exe', 'python', 'python3'] and 'concore' in cmdline_str)
                )
                
                if is_concore:
                    try:
                        create_time = datetime.fromtimestamp(proc.info['create_time'])
                        uptime = datetime.now() - create_time
                        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        uptime_str = f"{hours}h {minutes}m {seconds}s"
                    except:
                        uptime_str = "unknown"
                    
                    try:
                        mem_mb = proc.info['memory_info'].rss / 1024 / 1024
                        mem_str = f"{mem_mb:.1f} MB"
                    except:
                        mem_str = "unknown"
                    
                    command = ' '.join(cmdline[:3]) if len(cmdline) >= 3 else cmdline_str[:50]
                    
                    concore_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info.get('name', 'unknown'),
                        'command': command,
                        'uptime': uptime_str,
                        'memory': mem_str
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    except Exception as e:
        console.print(f"[red]Error scanning processes:[/red] {str(e)}")
        return
    
    if not concore_processes:
        console.print(Panel.fit(
            "[yellow]No concore processes currently running[/yellow]",
            border_style="yellow"
        ))
    else:
        table = Table(title=f"Concore Processes ({len(concore_processes)} running)", show_header=True)
        table.add_column("PID", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Uptime", style="yellow")
        table.add_column("Memory", style="magenta")
        table.add_column("Command", style="white")
        
        for proc in concore_processes:
            table.add_row(
                str(proc['pid']),
                proc['name'],
                proc['uptime'],
                proc['memory'],
                proc['command']
            )
        
        console.print(table)
        console.print()
        console.print(f"[dim]Use 'concore stop' to terminate all processes[/dim]")
