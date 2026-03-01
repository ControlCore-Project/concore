import click
from rich.console import Console
import os
import sys

from .commands.init import init_project
from .commands.run import run_workflow
from .commands.validate import validate_workflow
from .commands.status import show_status
from .commands.stop import stop_all
from .commands.inspect import inspect_workflow
from .commands.watch import watch_study
from . import __version__

console = Console()
DEFAULT_EXEC_TYPE = "windows" if os.name == "nt" else "posix"


@click.group()
@click.version_option(version=__version__, prog_name="concore")
def cli():
    pass


@cli.command()
@click.argument("name", required=True)
@click.option("--template", default="basic", help="Template type to use")
def init(name, template):
    """Create a new concore project"""
    try:
        init_project(name, template, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--source", "-s", default="src", help="Source directory")
@click.option("--output", "-o", default="out", help="Output directory")
@click.option(
    "--type",
    "-t",
    default=DEFAULT_EXEC_TYPE,
    type=click.Choice(["windows", "posix", "docker"]),
    help="Execution type",
)
@click.option(
    "--auto-build", is_flag=True, help="Automatically run build after generation"
)
def run(workflow_file, source, output, type, auto_build):
    """Run a concore workflow"""
    try:
        run_workflow(workflow_file, source, output, type, auto_build, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--source", "-s", default="src", help="Source directory")
def validate(workflow_file, source):
    """Validate a workflow file"""
    try:
        ok = validate_workflow(workflow_file, source, console)
        if not ok:
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--source", "-s", default="src", help="Source directory")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def inspect(workflow_file, source, output_json):
    """Inspect a workflow file and show its structure"""
    try:
        inspect_workflow(workflow_file, source, output_json, console)
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
@click.confirmation_option(prompt="Stop all running concore processes?")
def stop():
    """Stop all running concore processes"""
    try:
        stop_all(console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("study_dir", type=click.Path(exists=True))
@click.option("--interval", "-n", default=2.0, help="Refresh interval in seconds")
@click.option("--once", is_flag=True, help="Print a single snapshot and exit")
def watch(study_dir, interval, once):
    """Watch a running simulation study for live monitoring"""
    try:
        watch_study(study_dir, interval, once, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
