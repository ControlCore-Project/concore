from pathlib import Path

from .doctor import (
    TOOL_DEFINITIONS,
    _detect_tool,
    _get_platform_key,
    _resolve_concore_path,
)


def _pick_config_key(config_keys, plat_key):
    if plat_key == "windows":
        for key in config_keys:
            if key.endswith("WIN"):
                return key
    else:
        for key in config_keys:
            if key.endswith("EXE"):
                return key
    return config_keys[0] if config_keys else None


def _detect_tool_overrides(plat_key):
    found = []
    for tool_def in TOOL_DEFINITIONS.values():
        config_keys = tool_def.get("config_keys", [])
        if not config_keys:
            continue
        candidates = tool_def["names"].get(plat_key, [])
        path, _ = _detect_tool(candidates)
        if not path:
            continue
        config_key = _pick_config_key(config_keys, plat_key)
        if config_key:
            found.append((config_key, path))
    return found


def _write_text(path, content, dry_run, force, console):
    if path.exists() and not force:
        console.print(
            f"[yellow]![/yellow] Skipping {path.name} "
            "(already exists; use --force)"
        )
        return True
    if dry_run:
        preview = content if content else "<empty file>"
        console.print(f"[dim]-[/dim] Would write {path.name}:\n{preview}")
        return True
    path.write_text(content)
    console.print(f"[green]+[/green] Wrote {path.name}")
    return True


def setup_concore(console, dry_run=False, force=False):
    plat_key = _get_platform_key()
    concore_path = _resolve_concore_path()

    console.print(f"[cyan]CONCOREPATH:[/cyan] {concore_path}")

    tool_overrides = _detect_tool_overrides(plat_key)
    docker_candidates = TOOL_DEFINITIONS["Docker"]["names"].get(plat_key, [])
    _, docker_command = _detect_tool(docker_candidates)
    octave_candidates = TOOL_DEFINITIONS["Octave"]["names"].get(plat_key, [])
    octave_path, _ = _detect_tool(octave_candidates)
    octave_found = bool(octave_path)

    wrote_any = False

    tools_file = Path(concore_path) / "concore.tools"
    if tool_overrides:
        tools_content = "\n".join(f"{k}={v}" for k, v in tool_overrides) + "\n"
        wrote_any = (
            _write_text(tools_file, tools_content, dry_run, force, console)
            or wrote_any
        )
    else:
        console.print("[yellow]![/yellow] No tool paths detected for concore.tools")

    sudo_file = Path(concore_path) / "concore.sudo"
    if docker_command:
        sudo_content = f"{docker_command}\n"
        wrote_any = (
            _write_text(sudo_file, sudo_content, dry_run, force, console)
            or wrote_any
        )
    else:
        console.print("[yellow]![/yellow] Docker/Podman not detected; not writing concore.sudo")

    octave_file = Path(concore_path) / "concore.octave"
    if octave_found:
        wrote_any = (
            _write_text(octave_file, "", dry_run, force, console)
            or wrote_any
        )
    else:
        console.print("[dim]-[/dim] Octave not detected; not writing concore.octave")

    if not wrote_any:
        console.print("[yellow]No files written.[/yellow]")
        return False

    if dry_run:
        console.print("[green]Dry run complete.[/green]")
    else:
        console.print("[green]Setup complete.[/green]")
    return True