import psutil
import os
import subprocess
import sys
from pathlib import Path
from rich.panel import Panel

def stop_all(console):
    console.print("[cyan]Finding concore processes...[/cyan]\n")
    
    processes_to_kill = []
    current_pid = os.getpid()
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                
                cmdline = proc.info.get('cmdline') or []
                name = proc.info.get('name', '').lower()
                cmdline_str = ' '.join(cmdline) if cmdline else ''
                
                is_concore = (
                    'concore' in cmdline_str.lower() or
                    'concore.py' in cmdline_str.lower() or
                    any('concorekill.bat' in str(item) for item in cmdline) or
                    (name in ['python.exe', 'python', 'python3'] and 'concore' in cmdline_str)
                )
                
                if is_concore:
                    processes_to_kill.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return
    
    if not processes_to_kill:
        console.print(Panel.fit(
            "[yellow]No concore processes found[/yellow]",
            border_style="yellow"
        ))
        return
    
    console.print(f"[yellow]Stopping {len(processes_to_kill)} process(es)...[/yellow]\n")
    
    killed_count = 0
    failed_count = 0
    
    for proc in processes_to_kill:
        try:
            pid = proc.info['pid']
            name = proc.info.get('name', 'unknown')
            
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                             capture_output=True, 
                             check=False)
            else:
                proc.terminate()
                proc.wait(timeout=3)
            
            console.print(f"  [green]✓[/green] Stopped {name} (PID: {pid})")
            killed_count += 1
            
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                console.print(f"  [yellow]⚠[/yellow] Force killed {name} (PID: {pid})")
                killed_count += 1
            except:
                console.print(f"  [red]✗[/red] Failed to stop {name} (PID: {pid})")
                failed_count += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to stop PID {pid}: {str(e)}")
            failed_count += 1
    
    console.print()
    
    if failed_count == 0:
        console.print(Panel.fit(
            f"[green]✓[/green] Successfully stopped all {killed_count} process(es)",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[yellow]Stopped {killed_count} process(es)\n"
            f"Failed to stop {failed_count} process(es)[/yellow]",
            border_style="yellow"
        ))
