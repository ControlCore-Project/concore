import json
from pathlib import Path
from bs4 import BeautifulSoup
from rich.panel import Panel
import re
import xml.etree.ElementTree as ET


def _classify_message(message, bucket_name):
    if bucket_name == "info":
        if message.startswith("Found ") and "node(s)" in message:
            return {"info_type": "node_count"}
        if message.startswith("Found ") and "edge(s)" in message:
            return {"info_type": "edge_count"}
        if message.startswith("ZMQ-based edges:"):
            return {"info_type": "zmq_edges"}
        if message.startswith("File-based edges:"):
            return {"info_type": "file_edges"}
        return {"info_type": "info"}

    if message == "File is empty":
        return {"error_type": "empty_file"}
    if message.startswith("Invalid XML:"):
        return {"error_type": "invalid_xml"}
    if message == "Not a valid GraphML file - missing <graphml> root element":
        return {"error_type": "invalid_graphml"}
    if message == "Missing <graph> element":
        return {"error_type": "missing_graph_element"}
    if message == "Graph missing required 'edgedefault' attribute":
        return {"error_type": "missing_edgedefault"}
    if message.startswith("Invalid edgedefault value"):
        return {"error_type": "invalid_edgedefault"}
    if message == "No nodes found in workflow":
        return {"error_type": "no_nodes"}
    if message == "No edges found in workflow":
        return {"error_type": "no_edges"}
    if message.startswith("Source directory not found:"):
        return {"error_type": "missing_source_dir"}
    if message == "Node missing required 'id' attribute":
        return {"error_type": "missing_node_id"}
    if message.startswith("Node '") and message.endswith("contains unsafe shell characters"):
        return {"error_type": "unsafe_node_label"}
    if message.startswith("Node '") and "missing format 'ID:filename'" in message:
        return {"error_type": "invalid_node_label_format"}
    if message.startswith("Node '") and message.endswith("has invalid format"):
        return {"error_type": "invalid_node_label_format"}
    if message.startswith("Node '") and message.endswith("has no filename"):
        return {"error_type": "missing_node_filename"}
    if message.startswith("Node '") and message.endswith("has unusual file extension"):
        return {"error_type": "unusual_file_extension"}
    if message.startswith("Missing source file:"):
        return {"error_type": "missing_source_file"}
    if message.startswith("Node ") and message.endswith(" has no label"):
        return {"error_type": "missing_node_label"}
    if message.startswith("Error parsing node:"):
        return {"error_type": "node_parse_error"}
    if message.startswith("Duplicate node label:"):
        return {"error_type": "duplicate_node_label"}
    if message == "Edge missing source or target":
        return {"error_type": "missing_edge_endpoint"}
    if message.startswith("Edge references non-existent source node:"):
        return {"error_type": "missing_edge_source"}
    if message.startswith("Edge references non-existent target node:"):
        return {"error_type": "missing_edge_target"}
    if message == "Workflow contains cycles (expected for control loops)":
        return {"error_type": "cycle_detected"}
    if message.startswith("Invalid port number:"):
        return {"error_type": "invalid_port_number"}
    if message.startswith("Port conflict:"):
        return {"error_type": "port_conflict"}
    if message.startswith("Port ") and "is in reserved range" in message:
        return {"error_type": "reserved_port"}
    if message.startswith("File not found:"):
        return {"error_type": "file_not_found"}
    if message.startswith("Validation failed:"):
        return {"error_type": "validation_exception"}
    return {"error_type": "validation_message"}


def _build_entries(bucket_name, messages, source_nodes):
    entries = []
    for message in messages:
        entry = {"message": message}
        entry.update(_classify_message(message, bucket_name))

        if message.startswith("Missing source file:"):
            filename = message.split(":", 1)[1].strip()
            node_id = source_nodes.get(filename)
            if node_id:
                entry["node_id"] = node_id
        elif message.startswith("Node ") and message.endswith(" has no label"):
            entry["node_id"] = message[5:-9]
        elif message.startswith("Edge references non-existent source node:"):
            entry["node_id"] = message.split(":", 1)[1].strip()
        elif message.startswith("Edge references non-existent target node:"):
            entry["node_id"] = message.split(":", 1)[1].strip()

        entries.append(entry)
    return entries


def _build_payload(workflow_path, source_root, errors, warnings, info, source_nodes):
    error_entries = _build_entries("errors", errors, source_nodes)
    warning_entries = _build_entries("warnings", warnings, source_nodes)
    info_entries = _build_entries("info", info, source_nodes)

    nodes_affected = []
    for entry in error_entries + warning_entries:
        node_id = entry.get("node_id")
        if node_id and node_id not in nodes_affected:
            nodes_affected.append(node_id)

    return {
        "workflow": workflow_path.name,
        "source_dir": str(source_root),
        "valid": len(errors) == 0,
        "errors": error_entries,
        "warnings": warning_entries,
        "info": info_entries,
        "summary": {
            "error_count": len(error_entries),
            "warning_count": len(warning_entries),
            "info_count": len(info_entries),
            "nodes_affected": nodes_affected,
        },
    }


def validate_workflow(workflow_file, source_dir, console, output_format="text"):
    workflow_path = Path(workflow_file)
    source_root = workflow_path.parent / source_dir

    if output_format == "text":
        console.print(f"[cyan]Validating:[/cyan] {workflow_path.name}")
        console.print()

    errors = []
    warnings = []
    info = []
    source_nodes = {}

    def finalize():
        if output_format == "json":
            print(
                json.dumps(
                    _build_payload(
                        workflow_path,
                        source_root,
                        errors,
                        warnings,
                        info,
                        source_nodes,
                    ),
                    indent=2,
                )
            )
        else:
            show_results(console, errors, warnings, info)
        return len(errors) == 0

    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            errors.append("File is empty")
            return finalize()

        # strict XML syntax check
        try:
            ET.fromstring(content)
        except ET.ParseError as e:
            errors.append(f"Invalid XML: {str(e)}")
            return finalize()

        try:
            soup = BeautifulSoup(content, "xml")
        except Exception as e:
            errors.append(f"Invalid XML: {str(e)}")
            return finalize()

        root = soup.find("graphml")
        if not root:
            errors.append("Not a valid GraphML file - missing <graphml> root element")
            return finalize()

        # check the graph attributes
        graph = soup.find("graph")
        if not graph:
            errors.append("Missing <graph> element")
        else:
            edgedefault = graph.get("edgedefault")
            if not edgedefault:
                errors.append("Graph missing required 'edgedefault' attribute")
            elif edgedefault not in ["directed", "undirected"]:
                errors.append(
                    f"Invalid edgedefault value '{edgedefault}' (must be 'directed' or 'undirected')"
                )

        nodes = soup.find_all("node")
        edges = soup.find_all("edge")

        if len(nodes) == 0:
            warnings.append("No nodes found in workflow")
        else:
            info.append(f"Found {len(nodes)} node(s)")

        if len(edges) == 0:
            warnings.append("No edges found in workflow")
        else:
            info.append(f"Found {len(edges)} edge(s)")

        if not source_root.exists():
            warnings.append(f"Source directory not found: {source_root}")

        node_labels = []
        for node in nodes:
            # check the node id
            node_id = node.get("id")
            if not node_id:
                errors.append("Node missing required 'id' attribute")
                # skip further checks for this node to avoid noise
                continue

            try:
                # robust find: try with namespace prefix first, then without
                label_tag = node.find("y:NodeLabel")
                if not label_tag:
                    label_tag = node.find("NodeLabel")

                if label_tag and label_tag.text:
                    label = label_tag.text.strip()
                    node_labels.append(label)

                    # reject shell metacharacters to prevent command injection (#251)
                    if re.search(r'[;&|`$\'"()\\]', label):
                        errors.append(
                            f"Node '{label}' contains unsafe shell characters"
                        )
                        continue

                    if ":" not in label:
                        warnings.append(f"Node '{label}' missing format 'ID:filename'")
                    else:
                        parts = label.split(":")
                        if len(parts) != 2:
                            warnings.append(f"Node '{label}' has invalid format")
                        else:
                            nodeId_part, filename = parts
                            source_nodes[filename] = node_id
                            if not filename:
                                errors.append(f"Node '{label}' has no filename")
                            elif not any(
                                filename.endswith(ext)
                                for ext in [".py", ".cpp", ".m", ".v", ".java"]
                            ):
                                warnings.append(
                                    f"Node '{label}' has unusual file extension"
                                )
                            elif source_root.exists():
                                file_path = source_root / filename
                                if not file_path.exists():
                                    errors.append(f"Missing source file: {filename}")
                else:
                    warnings.append(f"Node {node_id} has no label")
            except Exception as e:
                warnings.append(f"Error parsing node: {str(e)}")

        # duplicate labels cause silent corruption in mkconcore.py
        seen = set()
        for label in node_labels:
            if label in seen:
                errors.append(f"Duplicate node label: '{label}'")
            seen.add(label)

        node_ids = {node.get("id") for node in nodes if node.get("id")}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if not source or not target:
                errors.append("Edge missing source or target")
                continue

            if source not in node_ids:
                errors.append(f"Edge references non-existent source node: {source}")
            if target not in node_ids:
                errors.append(f"Edge references non-existent target node: {target}")

        edge_label_regex = re.compile(r"0x([a-fA-F0-9]+)_(\S+)")
        zmq_edges = 0
        file_edges = 0

        for edge in edges:
            try:
                label_tag = edge.find("y:EdgeLabel")
                if not label_tag:
                    label_tag = edge.find("EdgeLabel")

                if label_tag and label_tag.text:
                    if edge_label_regex.match(label_tag.text.strip()):
                        zmq_edges += 1
                    else:
                        file_edges += 1
            except Exception:
                pass

        if zmq_edges > 0:
            info.append(f"ZMQ-based edges: {zmq_edges}")
        if file_edges > 0:
            info.append(f"File-based edges: {file_edges}")

        _check_cycles(soup, errors, warnings)
        _check_zmq_ports(soup, errors, warnings)

        return finalize()

    except FileNotFoundError:
        if output_format == "json":
            print(
                json.dumps(
                    _build_payload(
                        workflow_path,
                        source_root,
                        [f"File not found: {workflow_path}"],
                        [],
                        [],
                        source_nodes,
                    ),
                    indent=2,
                )
            )
        else:
            console.print(f"[red]Error:[/red] File not found: {workflow_path}")
        return False
    except Exception as e:
        if output_format == "json":
            print(
                json.dumps(
                    _build_payload(
                        workflow_path,
                        source_root,
                        [f"Validation failed: {str(e)}"],
                        [],
                        [],
                        source_nodes,
                    ),
                    indent=2,
                )
            )
        else:
            console.print(f"[red]Validation failed:[/red] {str(e)}")
        return False


def _check_cycles(soup, errors, warnings):
    nodes = soup.find_all("node")
    edges = soup.find_all("edge")

    node_ids = [node.get("id") for node in nodes if node.get("id")]
    if not node_ids:
        return

    graph = {nid: [] for nid in node_ids}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target and source in graph:
            graph[source].append(target)

    def has_cycle_from(start, visited, rec_stack):
        visited.add(start)
        rec_stack.add(start)

        for neighbor in graph.get(start, []):
            if neighbor not in visited:
                if has_cycle_from(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(start)
        return False

    visited = set()
    for node_id in node_ids:
        if node_id not in visited:
            if has_cycle_from(node_id, visited, set()):
                warnings.append("Workflow contains cycles (expected for control loops)")
                return


def _check_zmq_ports(soup, errors, warnings):
    edges = soup.find_all("edge")
    port_pattern = re.compile(r"0x([a-fA-F0-9]+)_(\S+)")

    ports_used = {}

    for edge in edges:
        label_tag = edge.find("y:EdgeLabel") or edge.find("EdgeLabel")
        if not label_tag or not label_tag.text:
            continue

        match = port_pattern.match(label_tag.text.strip())
        if not match:
            continue

        port_hex = match.group(1)
        port_name = match.group(2)
        port_num = int(port_hex, 16)

        if port_num < 1:
            errors.append(
                f"Invalid port number: {port_num} (0x{port_hex}) must be at least 1"
            )
            continue
        elif port_num > 65535:
            errors.append(
                f"Invalid port number: {port_num} (0x{port_hex}) exceeds maximum (65535)"
            )
            continue

        if port_num in ports_used:
            existing_name = ports_used[port_num]
            if existing_name != port_name:
                errors.append(
                    f"Port conflict: 0x{port_hex} used for both '{existing_name}' and '{port_name}'"
                )
        else:
            ports_used[port_num] = port_name

        if port_num < 1024:
            warnings.append(
                f"Port {port_num} (0x{port_hex}) is in reserved range (< 1024)"
            )


def show_results(console, errors, warnings, info):
    if errors:
        console.print("[red]✗ Validation failed[/red]\n")
        for error in errors:
            console.print(f"  [red]✗[/red] {error}")
    else:
        console.print("[green]✓ Validation passed[/green]\n")

    if warnings:
        console.print()
        for warning in warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")

    if info:
        console.print()
        for item in info:
            console.print(f"  [blue]ℹ[/blue] {item}")

    console.print()

    if not errors:
        console.print(
            Panel.fit(
                "[green]✓[/green] Workflow is valid and ready to run",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                f"[red]Found {len(errors)} error(s)[/red]\n"
                "Fix the errors above before running the workflow",
                border_style="red",
            )
        )
