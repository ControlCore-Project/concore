import os
import sys
import subprocess
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

def run_workflow(workflow_file, source, output, exec_type, auto_build, console):
    workflow_path = Path(workflow_file).resolve()
    source_path = Path(source).resolve()
    output_path = Path(output)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory '{source}' not found")
    
    if output_path.exists():
        console.print(f"[yellow]Warning:[/yellow] Output directory '{output}' already exists")
        console.print("Remove it first or choose a different output directory")
        return
    
    console.print(f"[cyan]Workflow:[/cyan] {workflow_path.name}")
    console.print(f"[cyan]Source:[/cyan] {source_path}")
    console.print(f"[cyan]Output:[/cyan] {output_path}")
    console.print(f"[cyan]Type:[/cyan] {exec_type}")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating workflow...", total=None)
        
        try:
            result = subprocess.run(
                [sys.executable, 'mkconcore.py', str(workflow_path), str(source_path), str(output_path), exec_type],
                capture_output=True,
                text=True,
                check=True
            )
            
            progress.update(task, completed=True)
            
            if result.stdout:
                console.print(result.stdout)
            
            console.print(f"[green]✓[/green] Workflow generated in [cyan]{output_path}[/cyan]")
            
        except subprocess.CalledProcessError as e:
            progress.stop()
            console.print(f"[red]Generation failed:[/red]")
            if e.stdout:
                console.print(e.stdout)
            if e.stderr:
                console.print(e.stderr)
            raise
    
    if auto_build:
        console.print()
        build_script = output_path / ('build.bat' if exec_type == 'windows' else 'build')
        
        if build_script.exists():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Building workflow...", total=None)
                
                try:
                    result = subprocess.run(
                        [str(build_script)],
                        cwd=output_path,
                        capture_output=True,
                        text=True,
                        shell=True,
                        check=True
                    )
                    progress.update(task, completed=True)
                    console.print(f"[green]✓[/green] Build completed")
                except subprocess.CalledProcessError as e:
                    progress.stop()
                    console.print(f"[yellow]Build failed[/yellow]")
                    if e.stderr:
                        console.print(e.stderr)
    
    console.print()
    console.print(Panel.fit(
        f"[green]✓[/green] Workflow ready!\n\n"
        f"To run your workflow:\n"
        f"  cd {output_path}\n"
        f"  {'build.bat' if exec_type == 'windows' else './build'}\n"
        f"  {'run.bat' if exec_type == 'windows' else './run'}",
        title="Next Steps",
        border_style="green"
    ))
