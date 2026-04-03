from pathlib import Path
from bs4 import BeautifulSoup
from rich.table import Table
from rich.tree import Tree
from collections import defaultdict
import re


def inspect_workflow(workflow_file, source_dir, output_json, console):
    workflow_path = Path(workflow_file)

    if output_json:
        return _inspect_json(workflow_path, source_dir)

    _inspect_rich(workflow_path, source_dir, console)


def _inspect_rich(workflow_path, source_dir, console):
    console.print()
    console.print(f"[bold cyan]Workflow:[/bold cyan] {workflow_path.name}")
    console.print()

    try:
        with open(workflow_path, "r") as f:
            content = f.read()

        soup = BeautifulSoup(content, "xml")

        if not soup.find("graphml"):
            console.print("[red]Not a valid GraphML file[/red]")
            return

        nodes = soup.find_all("node")
        edges = soup.find_all("edge")

        tree = Tree("📊 [bold]Workflow Overview[/bold]")

        lang_counts = defaultdict(int)
        node_files = []
        missing_files = []

        for node in nodes:
            label_tag = node.find("y:NodeLabel")
            if label_tag and label_tag.text:
                label = label_tag.text.strip()
                if ":" in label:
                    _, filename = label.split(":", 1)
                    node_files.append(filename)

                    ext = Path(filename).suffix
                    if ext == ".py":
                        lang_counts["Python"] += 1
                    elif ext == ".m":
                        lang_counts["MATLAB"] += 1
                    elif ext == ".java":
                        lang_counts["Java"] += 1
                    elif ext == ".cpp" or ext == ".hpp":
                        lang_counts["C++"] += 1
                    elif ext == ".v":
                        lang_counts["Verilog"] += 1
                    else:
                        lang_counts["Other"] += 1

                    src_dir = workflow_path.parent / source_dir
                    if not (src_dir / filename).exists():
                        missing_files.append(filename)

        nodes_branch = tree.add(f"Nodes: [bold]{len(nodes)}[/bold]")
        if lang_counts:
            for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
                nodes_branch.add(f"{lang}: {count}")

        edges_branch = tree.add(f"Edges: [bold]{len(edges)}[/bold]")

        edge_label_regex = re.compile(r"0x([a-fA-F0-9]+)_(\S+)")
        zmq_count = 0
        file_count = 0

        for edge in edges:
            label_tag = edge.find("y:EdgeLabel")
            label_text = label_tag.text.strip() if label_tag and label_tag.text else ""
            if label_text and edge_label_regex.match(label_text):
                zmq_count += 1
            else:
                file_count += 1

        if zmq_count > 0:
            edges_branch.add(f"ZMQ: {zmq_count}")
        if file_count > 0:
            edges_branch.add(f"File-based: {file_count}")

        comm_type = (
            "ZMQ (0mq)" if zmq_count > 0 else "File-based" if file_count > 0 else "None"
        )
        tree.add(f"Communication: [bold]{comm_type}[/bold]")

        if missing_files:
            missing_branch = tree.add(
                f"[yellow]Missing files: {len(missing_files)}[/yellow]"
            )
            for f in missing_files[:5]:
                missing_branch.add(f"[yellow]{f}[/yellow]")
            if len(missing_files) > 5:
                missing_branch.add(f"[dim]...and {len(missing_files) - 5} more[/dim]")

        console.print(tree)
        console.print()

        if nodes:
            table = Table(
                title="Node Details", show_header=True, header_style="bold magenta"
            )
            table.add_column("ID", style="cyan", width=12)
            table.add_column("File", style="white")
            table.add_column("Language", style="green")
            table.add_column("Status", style="yellow")

            for node in nodes[:10]:
                label_tag = node.find("y:NodeLabel")
                if label_tag and label_tag.text:
                    label = label_tag.text.strip()
                    if ":" in label:
                        node_id, filename = label.split(":", 1)

                        ext = Path(filename).suffix
                        lang_map = {
                            ".py": "Python",
                            ".m": "MATLAB",
                            ".java": "Java",
                            ".cpp": "C++",
                            ".hpp": "C++",
                            ".v": "Verilog",
                        }
                        lang = lang_map.get(ext, "Other")

                        src_dir = workflow_path.parent / source_dir
                        status = "✓" if (src_dir / filename).exists() else "✗"

                        table.add_row(node_id, filename, lang, status)

            if len(nodes) > 10:
                table.caption = f"Showing 10 of {len(nodes)} nodes"

            console.print(table)
            console.print()

        if edges:
            edge_table = Table(
                title="Edge Connections", show_header=True, header_style="bold magenta"
            )
            edge_table.add_column("From", style="cyan", width=12)
            edge_table.add_column("To", style="cyan", width=12)
            edge_table.add_column("Type", style="green")

            for edge in edges[:10]:
                source = edge.get("source", "unknown")
                target = edge.get("target", "unknown")

                label_tag = edge.find("y:EdgeLabel")
                edge_type = "File"
                if label_tag and label_tag.text:
                    if edge_label_regex.match(label_tag.text.strip()):
                        edge_type = "ZMQ"

                edge_table.add_row(source, target, edge_type)

            if len(edges) > 10:
                edge_table.caption = f"Showing 10 of {len(edges)} edges"

            console.print(edge_table)
            console.print()

    except FileNotFoundError:
        console.print(f"[red]File not found:[/red] {workflow_path}")
    except Exception as e:
        console.print(f"[red]Inspection failed:[/red] {str(e)}")


def _inspect_json(workflow_path, source_dir):
    import json

    try:
        with open(workflow_path, "r") as f:
            content = f.read()

        soup = BeautifulSoup(content, "xml")

        if not soup.find("graphml"):
            print(json.dumps({"error": "Not a valid GraphML file"}, indent=2))
            return

        nodes = soup.find_all("node")
        edges = soup.find_all("edge")

        lang_counts = defaultdict(int)
        node_list = []
        edge_list = []
        missing_files = []

        for node in nodes:
            label_tag = node.find("y:NodeLabel")
            if label_tag and label_tag.text:
                label = label_tag.text.strip()
                if ":" in label:
                    node_id, filename = label.split(":", 1)

                    ext = Path(filename).suffix
                    lang_map = {
                        ".py": "python",
                        ".m": "matlab",
                        ".java": "java",
                        ".cpp": "cpp",
                        ".hpp": "cpp",
                        ".v": "verilog",
                    }
                    lang = lang_map.get(ext, "other")
                    lang_counts[lang] += 1

                    src_dir = workflow_path.parent / source_dir
                    exists = (src_dir / filename).exists()
                    if not exists:
                        missing_files.append(filename)

                    node_list.append(
                        {
                            "id": node_id,
                            "file": filename,
                            "language": lang,
                            "exists": exists,
                        }
                    )

        edge_label_regex = re.compile(r"0x([a-fA-F0-9]+)_(\S+)")
        zmq_count = 0
        file_count = 0

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            label_tag = edge.find("y:EdgeLabel")
            label_text = label_tag.text.strip() if label_tag and label_tag.text else ""
            edge_type = "file"
            if label_text and edge_label_regex.match(label_text):
                edge_type = "zmq"
                zmq_count += 1
            else:
                file_count += 1

            edge_list.append({"source": source, "target": target, "type": edge_type})

        result = {
            "workflow": str(workflow_path.name),
            "nodes": {
                "total": len(nodes),
                "by_language": dict(lang_counts),
                "list": node_list,
            },
            "edges": {
                "total": len(edges),
                "zmq": zmq_count,
                "file": file_count,
                "list": edge_list,
            },
            "missing_files": missing_files,
        }

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
