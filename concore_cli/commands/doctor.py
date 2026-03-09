import shutil
import subprocess
import sys
import os
import platform
from pathlib import Path
from rich.panel import Panel

# Map of tool keys to their lookup names per platform
TOOL_DEFINITIONS = {
    "C++ compiler": {
        "names": {
            "posix": ["g++", "clang++"],
            "windows": ["g++", "cl"],
        },
        "version_flag": "--version",
        "config_keys": ["CPPEXE", "CPPWIN"],
        "install_hints": {
            "Linux": "sudo apt install g++",
            "Darwin": "brew install gcc",
            "Windows": "winget install -e --id GnuWin32.Gcc",
        },
    },
    "Python": {
        "names": {
            "posix": ["python3", "python"],
            "windows": ["python", "python3"],
        },
        "version_flag": "--version",
        "config_keys": ["PYTHONEXE", "PYTHONWIN"],
        "install_hints": {
            "Linux": "sudo apt install python3",
            "Darwin": "brew install python3",
            "Windows": "winget install -e --id Python.Python.3.11",
        },
    },
    "Verilog (iverilog)": {
        "names": {
            "posix": ["iverilog"],
            "windows": ["iverilog"],
        },
        "version_flag": "-V",
        "config_keys": ["VEXE", "VWIN"],
        "install_hints": {
            "Linux": "sudo apt install iverilog",
            "Darwin": "brew install icarus-verilog",
            "Windows": "Download from http://bleyer.org/icarus/",
        },
    },
    "Octave": {
        "names": {
            "posix": ["octave", "octave-cli"],
            "windows": ["octave", "octave-cli"],
        },
        "version_flag": "--version",
        "config_keys": ["OCTAVEEXE", "OCTAVEWIN"],
        "install_hints": {
            "Linux": "sudo apt install octave",
            "Darwin": "brew install octave",
            "Windows": "winget install -e --id JohnWHiggins.Octave",
        },
    },
    "MATLAB": {
        "names": {
            "posix": ["matlab"],
            "windows": ["matlab"],
        },
        "version_flag": "-batch \"disp('ok')\"",
        "config_keys": ["MATLABEXE", "MATLABWIN"],
        "install_hints": {
            "Linux": "Install from https://mathworks.com/downloads/",
            "Darwin": "Install from https://mathworks.com/downloads/",
            "Windows": "Install from https://mathworks.com/downloads/",
        },
    },
    "Docker": {
        "names": {
            "posix": ["docker", "podman"],
            "windows": ["docker", "podman"],
        },
        "version_flag": "--version",
        "config_keys": [],
        "install_hints": {
            "Linux": "sudo apt install docker.io",
            "Darwin": "brew install --cask docker",
            "Windows": "winget install -e --id Docker.DockerDesktop",
        },
    },
}

REQUIRED_PACKAGES = [
    "click",
    "rich",
    "beautifulsoup4",
    "lxml",
    "psutil",
    "numpy",
    "pyzmq",
]

OPTIONAL_PACKAGES = {
    "scipy": "pip install concore[demo]",
    "matplotlib": "pip install concore[demo]",
}

# Map import names that differ from package names
IMPORT_NAME_MAP = {
    "beautifulsoup4": "bs4",
    "pyzmq": "zmq",
}


def _get_platform_key():
    """Return 'posix' or 'windows' based on OS."""
    return "windows" if os.name == "nt" else "posix"


def _get_platform_name():
    """Return platform name for install hint lookup."""
    return platform.system()


def _resolve_concore_path():
    """Resolve CONCOREPATH the same way mkconcore.py does."""
    script_dir = Path(__file__).resolve().parent.parent.parent
    if (script_dir / "concore.py").exists():
        return script_dir
    cwd = Path.cwd()
    if (cwd / "concore.py").exists():
        return cwd
    return script_dir


def _detect_tool(names):
    """Try to find a tool by checking a list of candidate names.

    Returns (path, name) of the first match, or (None, None).
    """
    for name in names:
        path = shutil.which(name)
        if path:
            return path, name
    return None, None


def _get_version(path, version_flag):
    """Run tool with version flag and return first line of output."""
    try:
        result = subprocess.run(
            [path, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.strip() or result.stderr.strip()
        if output:
            return output.splitlines()[0]
    except Exception:
        pass
    return None


def _check_docker_daemon(docker_path):
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            [docker_path, "info"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_package(package_name):
    """Check if a Python package is importable and get its version."""
    import_name = IMPORT_NAME_MAP.get(package_name, package_name)
    try:
        mod = __import__(import_name)
        version = getattr(mod, "__version__", None)
        if version is None:
            version = getattr(mod, "VERSION", "installed")
        return True, str(version)
    except ImportError:
        return False, None


def doctor_check(console):
    """Run system readiness checks and display results."""
    passed = 0
    warnings = 0
    errors = 0

    console.print()
    console.print(
        Panel.fit(
            "[bold]concore Doctor — System Readiness Report[/bold]",
            border_style="cyan",
        )
    )
    console.print()

    # === Core Checks ===
    console.print("[bold cyan]Core Checks[/bold cyan]")

    # Python version
    py_version = platform.python_version()
    py_major, py_minor = sys.version_info.major, sys.version_info.minor
    if py_major >= 3 and py_minor >= 9:
        console.print(f"  [green]✓[/green] Python {py_version} (>= 3.9 required)")
        passed += 1
    else:
        console.print(
            f"  [red]✗[/red] Python {py_version} — "
            f"concore requires Python >= 3.9"
        )
        errors += 1

    # concore installation
    try:
        from concore_cli import __version__
        console.print(f"  [green]✓[/green] concore {__version__} installed")
        passed += 1
    except ImportError:
        console.print("  [red]✗[/red] concore package not found")
        errors += 1

    # CONCOREPATH
    concore_path = _resolve_concore_path()
    if concore_path.exists():
        writable = os.access(str(concore_path), os.W_OK)
        status = "writable" if writable else "read-only"
        if writable:
            console.print(
                f"  [green]✓[/green] CONCOREPATH: {concore_path} ({status})"
            )
            passed += 1
        else:
            console.print(
                f"  [yellow]![/yellow] CONCOREPATH: {concore_path} ({status})"
            )
            warnings += 1
    else:
        console.print(f"  [red]✗[/red] CONCOREPATH: {concore_path} (not found)")
        errors += 1

    console.print()

    # === Tool Detection ===
    console.print("[bold cyan]Tools[/bold cyan]")

    plat_key = _get_platform_key()
    plat_name = _get_platform_name()

    for tool_label, tool_def in TOOL_DEFINITIONS.items():
        candidates = tool_def["names"].get(plat_key, [])
        path, found_name = _detect_tool(candidates)

        if path:
            version = _get_version(path, tool_def["version_flag"])
            version_str = f" ({version})" if version else ""
            extra = ""
            if tool_label == "Docker":
                daemon_ok = _check_docker_daemon(path)
                extra = (
                    " [green](daemon running)[/green]"
                    if daemon_ok
                    else " [yellow](daemon not running)[/yellow]"
                )
                if not daemon_ok:
                    warnings += 1
                    console.print(
                        f"  [yellow]![/yellow] {tool_label}{version_str} "
                        f"→ {path}{extra}"
                    )
                    continue
            console.print(
                f"  [green]✓[/green] {tool_label}{version_str} → {path}{extra}"
            )
            passed += 1
        else:
            hint = tool_def["install_hints"].get(plat_name, "")
            hint_str = f" (install: {hint})" if hint else ""
            # MATLAB is optional if Octave is available, show as warning
            if tool_label == "MATLAB":
                console.print(
                    f"  [yellow]![/yellow] {tool_label} → Not found{hint_str}"
                )
                warnings += 1
            elif tool_label == "Verilog (iverilog)":
                console.print(
                    f"  [yellow]![/yellow] {tool_label} → Not found{hint_str}"
                )
                warnings += 1
            else:
                console.print(
                    f"  [red]✗[/red] {tool_label} → Not found{hint_str}"
                )
                errors += 1

    console.print()

    # === Configuration Checks ===
    console.print("[bold cyan]Configuration[/bold cyan]")

    config_files = {
        "concore.tools": "Tool path overrides",
        "concore.octave": "Treat .m files as Octave",
        "concore.mcr": "MATLAB Compiler Runtime path",
        "concore.sudo": "Docker executable override",
    }

    for filename, description in config_files.items():
        filepath = concore_path / filename
        if filepath.exists():
            try:
                content = filepath.read_text().strip()
                if filename == "concore.tools":
                    line_count = len(
                        [ln for ln in content.splitlines()
                         if ln.strip() and not ln.strip().startswith("#")]
                    )
                    console.print(
                        f"  [green]✓[/green] {filename} → "
                        f"{line_count} tool path(s) configured"
                    )
                elif filename == "concore.mcr":
                    if os.path.exists(os.path.expanduser(content)):
                        console.print(
                            f"  [green]✓[/green] {filename} → {content}"
                        )
                    else:
                        console.print(
                            f"  [yellow]![/yellow] {filename} → "
                            f"path does not exist: {content}"
                        )
                        warnings += 1
                        continue
                elif filename == "concore.sudo":
                    console.print(
                        f"  [green]✓[/green] {filename} → {content}"
                    )
                else:
                    console.print(
                        f"  [green]✓[/green] {filename} → Enabled"
                    )
                passed += 1
            except Exception:
                console.print(
                    f"  [yellow]![/yellow] {filename} → Could not read"
                )
                warnings += 1
        else:
            console.print(
                f"  [dim]—[/dim] {filename} → Not set ({description})"
            )

    # Check environment variables
    env_vars = [
        "CONCORE_CPPEXE", "CONCORE_PYTHONEXE", "CONCORE_VEXE",
        "CONCORE_OCTAVEEXE", "CONCORE_MATLABEXE", "DOCKEREXE",
    ]
    env_set = [v for v in env_vars if os.environ.get(v)]
    if env_set:
        console.print(
            f"  [green]✓[/green] Environment variables: "
            f"{', '.join(env_set)}"
        )
        passed += 1
    else:
        console.print("  [dim]—[/dim] No concore environment variables set")

    console.print()

    # === Dependency Checks ===
    console.print("[bold cyan]Dependencies[/bold cyan]")

    for pkg in REQUIRED_PACKAGES:
        found, version = _check_package(pkg)
        if found:
            console.print(f"  [green]✓[/green] {pkg} {version}")
            passed += 1
        else:
            console.print(
                f"  [red]✗[/red] {pkg} → Not installed "
                f"(pip install {pkg})"
            )
            errors += 1

    for pkg, install_hint in OPTIONAL_PACKAGES.items():
        found, version = _check_package(pkg)
        if found:
            console.print(f"  [green]✓[/green] {pkg} {version}")
            passed += 1
        else:
            console.print(
                f"  [yellow]![/yellow] {pkg} → Not installed "
                f"({install_hint})"
            )
            warnings += 1

    console.print()

    # === Summary ===
    summary_parts = []
    if passed:
        summary_parts.append(f"[green]{passed} passed[/green]")
    if warnings:
        summary_parts.append(f"[yellow]{warnings} warning(s)[/yellow]")
    if errors:
        summary_parts.append(f"[red]{errors} error(s)[/red]")

    console.print(f"[bold]Summary:[/bold] {', '.join(summary_parts)}")

    if errors == 0:
        console.print()
        console.print(
            Panel.fit(
                "[green]System is ready to run concore studies![/green]",
                border_style="green",
            )
        )

    console.print()

    return errors == 0
