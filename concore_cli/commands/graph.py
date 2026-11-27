from pathlib import Path

from bs4 import BeautifulSoup

FORMATS = ("mermaid", "dot")


def _text(element, name):
    tag = element.find(f"y:{name}")
    if tag is None:
        tag = element.find(name)
    return tag.text.strip() if tag is not None and tag.text else ""


def _read_graph(workflow_path):
    soup = BeautifulSoup(workflow_path.read_text(encoding="utf-8"), "xml")
    if not soup.find("graphml"):
        raise ValueError("Not a valid GraphML file")

    names = {}
    for node in soup.find_all("node"):
        node_id = node.get("id")
        if node_id:
            names[node_id] = _text(node, "NodeLabel") or node_id

    edges = []
    for edge in soup.find_all("edge"):
        source, target = edge.get("source"), edge.get("target")
        if source in names and target in names:
            edges.append((source, target, _text(edge, "EdgeLabel")))
    return names, edges


def _display(label):
    # 'CZ:controller.py' stays as is; a port-only node 'IN:' shows as 'IN'.
    return label[:-1] if label.endswith(":") and len(label) > 1 else label


def _mermaid_quote(text):
    return '"' + text.replace('"', "#quot;") + '"'


def _dot_quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_mermaid(names, edges):
    index = {node_id: f"n{i}" for i, node_id in enumerate(names)}
    lines = ["flowchart LR"]
    for node_id, label in names.items():
        lines.append(f"    {index[node_id]}[{_mermaid_quote(_display(label))}]")
    for source, target, label in edges:
        arrow = f"-->|{_mermaid_quote(label)}|" if label else "-->"
        lines.append(f"    {index[source]} {arrow} {index[target]}")
    return "\n".join(lines) + "\n"


def render_dot(names, edges):
    index = {node_id: f"n{i}" for i, node_id in enumerate(names)}
    lines = ["digraph concore {", "    rankdir=LR;", "    node [shape=box];"]
    for node_id, label in names.items():
        lines.append(f"    {index[node_id]} [label={_dot_quote(_display(label))}];")
    for source, target, label in edges:
        attr = f" [label={_dot_quote(label)}]" if label else ""
        lines.append(f"    {index[source]} -> {index[target]}{attr};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def graph_workflow(workflow_file, output_format):
    """Return the workflow drawn as Mermaid or Graphviz DOT text."""
    names, edges = _read_graph(Path(workflow_file))
    if output_format == "mermaid":
        return render_mermaid(names, edges)
    if output_format == "dot":
        return render_dot(names, edges)
    raise ValueError(f"Unknown format '{output_format}' (use mermaid or dot)")
