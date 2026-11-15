import re
from pathlib import Path

from rich.panel import Panel

from .init import GRAPHML_NODE, LANGUAGE_NODES

LANGUAGES = tuple(LANGUAGE_NODES)

NODE_KEY_RE = re.compile(r"<key\b[^>]*>")
NODE_ID_RE = re.compile(r'<node\b[^>]*\bid="([^"]*)"')
LABEL_RE = re.compile(r"<y:NodeLabel[^>]*>([^<]*)</y:NodeLabel>")
Y_RE = re.compile(r'<y:Geometry\b[^>]*\by="(-?[0-9.]+)"')


def _nodegraphics_key(text):
    for tag in NODE_KEY_RE.findall(text):
        if 'for="node"' in tag and 'yfiles.type="nodegraphics"' in tag:
            match = re.search(r'\bid="([^"]*)"', tag)
            if match:
                return match.group(1)
    return None


def _pick_filename(default_filename, src_path, used_files):
    stem, dot, ext = default_filename.rpartition(".")
    candidate, n = default_filename, 1
    while (src_path / candidate).exists() or candidate in used_files:
        n += 1
        candidate = f"{stem}{n}{dot}{ext}"
    return candidate


def _pick_index(node_ids, labels):
    i = 1
    while f"n{i}" in node_ids or any(lab.startswith(f"N{i}:") for lab in labels):
        i += 1
    return i


def add_node(project_dir, lang, console):
    project_path = Path(project_dir)
    workflow = project_path / "workflow.graphml"
    if not workflow.is_file():
        raise FileNotFoundError(f"No workflow.graphml in '{project_dir}'")
    if lang not in LANGUAGE_NODES:
        raise ValueError(f"Unsupported language '{lang}'")

    # Read bytes so a CRLF file keeps its line endings (read_text would convert them).
    text = workflow.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"

    key_id = _nodegraphics_key(text)
    if key_id is None:
        raise ValueError("workflow.graphml has no node graphics key to attach to")
    close = text.rfind("</graph>")
    if close == -1:
        raise ValueError("workflow.graphml has no </graph> element")

    info = LANGUAGE_NODES[lang]
    src_path = project_path / "src"
    labels = [m.strip() for m in LABEL_RE.findall(text)]
    used_files = {lab.split(":", 1)[1] for lab in labels if ":" in lab}
    filename = _pick_filename(info["filename"], src_path, used_files)
    idx = _pick_index(set(NODE_ID_RE.findall(text)), labels)
    ys = [float(y) for y in Y_RE.findall(text)]
    y = int(max(ys) + 100) if ys else 100

    stub = info["stub"]
    if lang == "java":
        class_name = Path(filename).stem
        stub = stub.replace("public class Script", f"public class {class_name}")

    node_xml = GRAPHML_NODE.format(
        idx=idx, y=y, color=info["color"], filename=filename
    ).replace('key="d6"', f'key="{key_id}"')
    node_xml = node_xml.replace("\n", newline)

    src_path.mkdir(exist_ok=True)
    (src_path / filename).write_text(stub, encoding="utf-8")

    line_start = text.rfind(newline, 0, close) + len(newline)
    updated = text[:line_start] + node_xml + newline + text[line_start:]
    workflow.write_bytes(updated.encode("utf-8"))

    console.print(
        Panel.fit(
            f"[green]✓[/green] Added node N{idx}: {filename}\n\n"
            f"  src/{filename}\n"
            f"  workflow.graphml (unconnected — connect it in yEd)",
            title="Success",
            border_style="green",
        )
    )
