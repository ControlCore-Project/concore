import re
import shlex
import subprocess
import sys
import shutil
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .metadata import write_study_metadata


def _find_mkconcore_path():
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "mkconcore.py"
        if candidate.exists():
            return candidate
    return None


def _yaml_quote(value):
    return "'" + value.replace("'", "''") + "'"


def _parse_docker_run_line(line):
    text = line.strip()
    if not text or text.startswith("#"):
        return None

    if text.endswith("&"):
        text = text[:-1].strip()

    try:
        tokens = shlex.split(text)
    except ValueError:
        return None

    if "run" not in tokens:
        return None

    run_index = tokens.index("run")
    args = tokens[run_index + 1 :]

    container_name = None
    volumes = []
    image = None

    i = 0
    while i < len(args):
        token = args[i]
        if token.startswith("--name="):
            container_name = token.split("=", 1)[1]
        elif token == "--name" and i + 1 < len(args):
            container_name = args[i + 1]
            i += 1
        elif token in ("-v", "--volume") and i + 1 < len(args):
            volumes.append(args[i + 1])
            i += 1
        elif token.startswith("--volume="):
            volumes.append(token.split("=", 1)[1])
        elif token.startswith("-"):
            pass
        else:
            image = token
            break
        i += 1

    if not container_name or not image:
        return None

    return {
        "container_name": container_name,
        "volumes": volumes,
        "image": image,
    }


def _write_docker_compose(output_path, console, zmq_mode=False):
    run_script = output_path / "run"
    if not run_script.exists():
        console.print(
            f"[yellow]Warning:[/yellow] No docker run script found in {output_path}."
        )
        console.print(
            "[dim]Tip: run concore build --type docker first, then use --compose[/dim]"
        )
        return None

    services = []
    for line in run_script.read_text(encoding="utf-8").splitlines():
        parsed = _parse_docker_run_line(line)
        if parsed is not None:
            services.append(parsed)

    if not services:
        return None

    compose_lines = ["services:"]

    named_volumes = set()
    previous_service_name = None
    for index, service in enumerate(services, start=1):
        service_name = re.sub(r"[^A-Za-z0-9_.-]", "-", service["container_name"]).strip(
            "-."
        )
        if not service_name:
            service_name = f"service-{index}"
        elif not service_name[0].isalpha():
            service_name = f"service-{service_name}"

        compose_lines.append(f"  {service_name}:")
        compose_lines.append(f"    image: {_yaml_quote(service['image'])}")
        compose_lines.append(
            f"    container_name: {_yaml_quote(service['container_name'])}"
        )

        if service["volumes"]:
            compose_lines.append("    volumes:")
            for volume_spec in service["volumes"]:
                compose_lines.append(f"      - {_yaml_quote(volume_spec)}")
                part1 = volume_spec.split(":")[0]
                if re.match(r"^[a-zA-Z0-9_-]+$", part1):
                    named_volumes.add(part1)

        compose_lines.append("    restart: on-failure")
        if zmq_mode:
            compose_lines.append("    environment:")
            compose_lines.append("      - CONCORE_TRANSPORT=zmq")
        if index > 1 and previous_service_name:
            compose_lines.append("    depends_on:")
            compose_lines.append(f"      - {previous_service_name}")
        compose_lines.append("    networks:")
        compose_lines.append("      - concore_net")
        previous_service_name = service_name

    if named_volumes:
        compose_lines.append("")
        compose_lines.append("volumes:")
        for v in sorted(named_volumes):
            compose_lines.append(f"  {v}:")
            compose_lines.append(f"    name: {_yaml_quote(v)}")

    compose_lines.append("")
    compose_lines.append("networks:")
    compose_lines.append("  concore_net:")
    compose_lines.append("    driver: bridge")

    compose_lines.append("")
    compose_path = output_path / "docker-compose.yml"
    compose_path.write_text("\n".join(compose_lines), encoding="utf-8")
    return compose_path


def build_workflow(
    workflow_file,
    source,
    output,
    exec_type,
    auto_build,
    console,
    compose=False,
    zmq_mode=False,
):
    workflow_path = Path(workflow_file).resolve()
    source_path = Path(source).resolve()
    output_path = Path(output).resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory '{source}' not found")

    if output_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] Output directory '{output}' already exists"
        )
        console.print("Remove it first or choose a different output directory")
        return

    console.print(f"[cyan]Workflow:[/cyan] {workflow_path.name}")
    console.print(f"[cyan]Source:[/cyan] {source_path}")
    console.print(f"[cyan]Output:[/cyan] {output_path}")
    console.print(f"[cyan]Type:[/cyan] {exec_type}")
    if compose:
        console.print("[cyan]Compose:[/cyan] enabled")
    console.print()

    if compose and exec_type != "docker":
        raise ValueError("--compose can only be used with --type docker")

    mkconcore_path = _find_mkconcore_path()
    if mkconcore_path is None:
        raise FileNotFoundError(
            "mkconcore.py not found. Please install concore from source."
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating workflow...", total=None)

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(mkconcore_path),
                    str(workflow_path),
                    str(source_path),
                    str(output_path),
                    exec_type,
                ],
                cwd=mkconcore_path.parent,
                capture_output=True,
                text=True,
                check=True,
            )

            progress.update(task, completed=True)

            if exec_type == "docker":
                req_src = Path.cwd() / "requirements.txt"
                if not req_src.exists():
                    req_src = source_path / "requirements.txt"
                req_dest = output_path / "src" / "requirements.txt"
                if req_src.exists() and (output_path / "src").exists():
                    shutil.copy2(req_src, req_dest)
                elif (output_path / "src").exists():
                    req_dest.touch()

                # Append requirement copying to generated scripts robustly
                for s_name in ["build", "build.bat"]:
                    s_path = output_path / s_name
                    if s_path.exists():
                        content = s_path.read_text(encoding="utf-8")
                        lines = content.splitlines()
                        if s_name == "build":
                            insert_line = "cp ../src/requirements.txt ."
                        else:
                            insert_line = "copy ..\\src\\requirements.txt ."

                        new_lines = []
                        for line in lines:
                            if " build" in line and "-t " in line:
                                new_lines.append(insert_line)
                            new_lines.append(line)

                        s_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

            if result.stdout:
                console.print(result.stdout)

            console.print(
                f"[green]✓[/green] Workflow generated in [cyan]{output_path}[/cyan]"
            )

            if compose:
                compose_path = _write_docker_compose(
                    output_path, console, zmq_mode=zmq_mode
                )
                if compose_path is not None:
                    console.print(
                        f"[green]✓[/green] Compose file written to [cyan]{compose_path}[/cyan]"
                    )
                else:
                    console.print(
                        "[yellow]Warning:[/yellow] Could not generate docker-compose.yml from run script"
                    )

            try:
                metadata_path = write_study_metadata(
                    output_path,
                    generated_by="concore build",
                    workflow_file=workflow_path,
                )
                console.print(
                    f"[green]✓[/green] Metadata written to [cyan]{metadata_path}[/cyan]"
                )
            except Exception as exc:
                # Metadata is additive, so workflow generation should still succeed on failure.
                console.print(
                    f"[yellow]Warning:[/yellow] Failed to write study metadata for [cyan]{output_path}[/cyan]: {exc}"
                )

        except subprocess.CalledProcessError as e:
            progress.stop()
            console.print("[red]Generation failed:[/red]")
            if e.stdout:
                console.print(e.stdout)
            if e.stderr:
                console.print(e.stderr)
            raise

    if auto_build:
        console.print()
        build_script = output_path / (
            "build.bat" if exec_type == "windows" else "build"
        )

        if build_script.exists():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Building workflow...", total=None)

                try:
                    result = subprocess.run(
                        [str(build_script)],
                        cwd=output_path,
                        capture_output=True,
                        text=True,
                        shell=True,
                        check=True,
                    )
                    progress.update(task, completed=True)
                    console.print("[green]✓[/green] Build completed")
                except subprocess.CalledProcessError as e:
                    progress.stop()
                    console.print("[yellow]Build failed[/yellow]")
                    if e.stderr:
                        console.print(e.stderr)

    run_command = "docker compose up" if compose else "./run"
    if exec_type == "windows":
        run_command = "run.bat"

    console.print()
    console.print(
        Panel.fit(
            f"[green]✓[/green] Workflow ready!\n\n"
            f"To run your workflow:\n"
            f"  cd {output_path}\n"
            f"  {'build.bat' if exec_type == 'windows' else './build'}\n"
            f"  {run_command}",
            title="Next Steps",
            border_style="green",
        )
    )
