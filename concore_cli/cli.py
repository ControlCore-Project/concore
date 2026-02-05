import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import sys
import os
from pathlib import Path

from .commands.init import init_project
from .commands.run import run_workflow
from .commands.validate import validate_workflow
from .commands.status import show_status
from .commands.stop import stop_all

console = Console()

@click.group()
@click.version_option(version='1.0.0', prog_name='concore')
def cli():
    pass

@cli.command()
@click.argument('name', required=True)
@click.option('--template', default='basic', help='Template type to use')
def init(name, template):
    """Create a new concore project"""
    try:
        init_project(name, template, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--source', '-s', default='src', help='Source directory')
@click.option('--output', '-o', default='out', help='Output directory')
@click.option('--type', '-t', default='windows', type=click.Choice(['windows', 'posix', 'docker']), help='Execution type')
@click.option('--auto-build', is_flag=True, help='Automatically run build after generation')
def run(workflow_file, source, output, type, auto_build):
    """Run a concore workflow"""
    try:
        run_workflow(workflow_file, source, output, type, auto_build, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
def validate(workflow_file):
    """Validate a workflow file"""
    try:
        validate_workflow(workflow_file, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@cli.command()
def status():
    """Show running concore processes"""
    try:
        show_status(console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@cli.command()
@click.confirmation_option(prompt='Stop all running concore processes?')
def stop():
    """Stop all running concore processes"""
    try:
        stop_all(console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
