import os
import sys
import shutil
import subprocess
from rich.console import Console

console = Console()
EDITOR_URL = "https://controlcore-project.github.io/concore-editor/"


def open_editor_url(url):
    try:
        if sys.platform == "win32":
            os.system(f'start "" chrome "{url}"')
        else:
            if shutil.which("open"):
                if sys.platform == "darwin":
                    subprocess.run(["open", "-a", "Google Chrome", url])
                elif sys.platform.startswith("linux"):
                    subprocess.run(["xdg-open", url])
            else:
                if shutil.which("xdg-open"):
                    subprocess.run(["xdg-open", url])
                else:
                    console.print("unable to open browser for the concore editor.")
    except Exception as e:
        console.print(f"unable to open browser for the concore editor. ({e})")


def launch_editor():
    console.print("[cyan]Opening concore-editor...[/cyan]")
    open_editor_url(EDITOR_URL)
