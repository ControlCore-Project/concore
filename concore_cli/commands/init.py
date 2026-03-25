from pathlib import Path
from rich.panel import Panel

from .metadata import write_study_metadata

# ---------------------------------------------------------------------------
# GraphML templates
# ---------------------------------------------------------------------------

GRAPHML_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd"
         xmlns:y="http://www.yworks.com/xml/graphml">
  <key for="node" id="d6" yfiles.type="nodegraphics"/>
  <key for="edge" id="d10" yfiles.type="edgegraphics"/>
  <graph edgedefault="directed" id="1" projectName="{project_name}">
{nodes}
  </graph>
</graphml>
"""

GRAPHML_NODE = """    <node id="n{idx}">
      <data key="d6">
        <y:ShapeNode>
          <y:Geometry height="50" width="150" x="100" y="{y}"/>
          <y:Fill color="{color}" opacity="1"/>
          <y:BorderStyle color="#000000" width="1"/>
          <y:NodeLabel>N{idx}:{filename}</y:NodeLabel>
          <y:Shape type="rectangle"/>
        </y:ShapeNode>
      </data>
    </node>"""

# Single-node fallback used by non-interactive init
SAMPLE_GRAPHML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd" xmlns:y="http://www.yworks.com/xml/graphml">
  <key for="node" id="d6" yfiles.type="nodegraphics"/>
  <key for="edge" id="d10" yfiles.type="edgegraphics"/>
  <graph edgedefault="directed" id="1" projectName="sample">
    <node id="n1">
      <data key="d6">
        <y:ShapeNode>
          <y:Geometry height="50" width="150" x="100" y="100"/>
          <y:Fill color="#ffcc00" opacity="1"/>
          <y:BorderStyle color="#000" width="1"/>
          <y:NodeLabel>N1:script.py</y:NodeLabel>
          <y:Shape type="rectangle"/>
        </y:ShapeNode>
      </data>
    </node>
  </graph>
</graphml>
"""

# ---------------------------------------------------------------------------
# Per-language metadata: label, filename, node colour, source stub
# ---------------------------------------------------------------------------

LANGUAGE_NODES = {
    "python": {
        "label": "Python",
        "filename": "script.py",
        "color": "#ffcc00",
        "stub": (
            "import concore\n\n"
            "concore.default_maxtime(100)\n"
            "concore.delay = 0.02\n\n"
            'init_val = "[0.0, 0.0]"\n'
            "val = concore.initval(init_val)\n\n"
            "while concore.simtime < concore.maxtime:\n"
            "    while concore.unchanged():\n"
            '        val = concore.read(1, "data", init_val)\n'
            "    result = [v * 2 for v in val]\n"
            '    concore.write(1, "result", result, delta=0)\n'
        ),
    },
    "cpp": {
        "label": "C++",
        "filename": "script.cpp",
        "color": "#ae85ca",
        "stub": (
            '#include "concore.hpp"\n'
            "#include <vector>\n\n"
            "int main() {\n"
            "    Concore concore;\n"
            "    concore.default_maxtime(100);\n"
            "    concore.delay = 0.02;\n\n"
            '    std::string init_val = "[0.0, 0.0]";\n'
            "    std::vector<double> val = concore.initval(init_val);\n\n"
            "    while (concore.simtime < concore.maxtime) {\n"
            "        while (concore.unchanged()) {\n"
            '            val = concore.read(1, "data", init_val);\n'
            "        }\n"
            '        concore.write(1, "result", val, 0);\n'
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
    },
    "octave": {
        "label": "Octave/MATLAB",
        "filename": "script.m",
        "color": "#6db3f2",
        "stub": (
            "global concore;\n"
            "import_concore;\n\n"
            "concore.delay = 0.02;\n"
            "concore_default_maxtime(100);\n\n"
            "init_val = '[0.0, 0.0]';\n"
            "val = concore_initval(init_val);\n\n"
            "while concore.simtime < concore.maxtime\n"
            "    while concore_unchanged()\n"
            "        val = concore_read(1, 'data', init_val);\n"
            "    end\n"
            "    result = val * 2;\n"
            "    concore_write(1, 'result', result, 0);\n"
            "end\n"
        ),
    },
    "verilog": {
        "label": "Verilog",
        "filename": "script.v",
        "color": "#f28c8c",
        "stub": (
            '`include "concore.v"\n\n'
            "module script;\n"
            "  // concore module provides: simtime, maxtime, readdata, writedata, unchanged\n"
            "  // data[] and datasize are global arrays filled by readdata\n\n"
            "  real init_val[1:0];  // [simtime, value]\n"
            "  integer i;\n\n"
            "  initial begin\n"
            "    concore.simtime = 0;\n"
            "    // set your maxtime (or let concore.maxtime file override)\n\n"
            "    while (concore.simtime < 100) begin\n"
            "      while (concore.unchanged(0)) begin\n"
            "        // readdata fills concore.data[] and updates concore.simtime\n"
            '        concore.readdata(1, "data", "[0.0,0.0]");\n'
            "      end\n"
            "      // TODO: process concore.data[0..datasize-1]\n"
            "      concore.data[0] = concore.data[0] * 2;\n"
            "      concore.datasize = 1;\n"
            '      concore.writedata(1, "result", 0);  // delta=0\n'
            "    end\n"
            "    $finish;\n"
            "  end\n"
            "endmodule\n"
        ),
    },
    "java": {
        "label": "Java",
        "filename": "Script.java",
        "color": "#a8d8a8",
        "stub": (
            "public class Script {\n"
            "    public static void main(String[] args) throws Exception {\n"
            "        concoredocker cd = new concoredocker();\n"
            "        double maxtime = 100;\n"
            "        double delay   = 0.02;\n"
            '        String init_val = "[0.0, 0.0]";\n\n'
            "        String val = cd.initval(init_val);\n"
            "        while (cd.simtime() < maxtime) {\n"
            "            while (cd.unchanged()) {\n"
            '                val = cd.read(1, "data", init_val);\n'
            "            }\n"
            "            // TODO: process val\n"
            '            cd.write(1, "result", val, 0);\n'
            "        }\n"
            "    }\n"
            "}\n"
        ),
    },
}

README_TEMPLATE = """# {project_name}

A concore workflow project.

## Getting Started

1. Edit your workflow in `workflow.graphml` using yEd or similar GraphML editor
2. Add your processing scripts to the `src/` directory
3. Run your workflow:
   ```
   concore run workflow.graphml
   ```

## Project Structure

- `workflow.graphml` - Your workflow definition
- `src/` - Source files for your nodes
- `README.md` - This file

## Next Steps

- Open `workflow.graphml` in yEd and connect the nodes with edges
- Use `concore validate workflow.graphml` to check your workflow
- Use `concore status` to monitor running processes
"""


# ---------------------------------------------------------------------------
# Interactive wizard
# ---------------------------------------------------------------------------


def run_wizard(console):
    """Ask y/n for each supported language. Returns list of selected lang keys."""
    console.print()
    console.print(
        "[bold cyan]Select the node types to include[/bold cyan]  "
        "[dim](Enter = yes)[/dim]"
    )
    console.print()

    selected = []
    for key, info in LANGUAGE_NODES.items():
        raw = (
            console.input(f"  Include [bold]{info['label']}[/bold] node? [Y/n] ")
            .strip()
            .lower()
        )
        if raw in ("", "y", "yes"):
            selected.append(key)

    return selected


# ---------------------------------------------------------------------------
# GraphML builder
# ---------------------------------------------------------------------------


def _build_graphml(project_name, selected_langs):
    """Return a GraphML string with one unconnected node per selected language."""
    node_blocks = []
    for idx, lang_key in enumerate(selected_langs, start=1):
        info = LANGUAGE_NODES[lang_key]
        node_blocks.append(
            GRAPHML_NODE.format(
                idx=idx,
                y=100 + (idx - 1) * 100,  # stack vertically, 100 px apart
                color=info["color"],
                filename=info["filename"],
            )
        )
    return GRAPHML_HEADER.format(
        project_name=project_name,
        nodes="\n".join(node_blocks),
    )


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def init_project_interactive(name, selected_langs, console):
    """Create a project with one node per selected language (no edges)."""
    project_path = Path(name)

    if project_path.exists():
        raise FileExistsError(f"Directory '{name}' already exists")

    if not selected_langs:
        console.print("[yellow]No languages selected — nothing to create.[/yellow]")
        return

    console.print()
    console.print(f"[cyan]Creating project:[/cyan] {name}")

    project_path.mkdir()
    src_path = project_path / "src"
    src_path.mkdir()

    # workflow.graphml
    workflow_file = project_path / "workflow.graphml"
    workflow_file.write_text(_build_graphml(name, selected_langs))

    # one source stub per selected language
    for lang_key in selected_langs:
        info = LANGUAGE_NODES[lang_key]
        (src_path / info["filename"]).write_text(info["stub"])

    # README
    (project_path / "README.md").write_text(README_TEMPLATE.format(project_name=name))

    # Metadata
    metadata_info = ""
    try:
        metadata_path = write_study_metadata(
            project_path,
            generated_by="concore init --interactive",
            workflow_file=workflow_file,
        )
        metadata_info = f"Metadata:\n  {metadata_path.name}\n\n"
    except Exception as exc:
        console.print(
            f"[yellow]Warning:[/yellow] Failed to write study metadata: {exc}"
        )

    node_lines = "\n".join(
        f"    N{i}: {LANGUAGE_NODES[k]['filename']}"
        for i, k in enumerate(selected_langs, 1)
    )

    console.print()
    console.print(
        Panel.fit(
            f"[green]✓[/green] Project created with {len(selected_langs)} node(s)!\n\n"
            f"{metadata_info}"
            f"Nodes (unconnected — connect them in yEd):\n{node_lines}\n\n"
            f"Next steps:\n"
            f"  cd {name}\n"
            f"  concore validate workflow.graphml\n"
            f"  concore run workflow.graphml",
            title="Success",
            border_style="green",
        )
    )


def init_project(name, template, console):
    """Non-interactive init — single Python node skeleton."""
    project_path = Path(name)

    if project_path.exists():
        raise FileExistsError(f"Directory '{name}' already exists")

    console.print(f"[cyan]Creating project:[/cyan] {name}")

    project_path.mkdir()
    (project_path / "src").mkdir()

    workflow_file = project_path / "workflow.graphml"
    with open(workflow_file, "w") as f:
        f.write(SAMPLE_GRAPHML)

    (project_path / "src" / "script.py").write_text(LANGUAGE_NODES["python"]["stub"])

    (project_path / "README.md").write_text(README_TEMPLATE.format(project_name=name))

    metadata_info = ""
    try:
        metadata_path = write_study_metadata(
            project_path,
            generated_by="concore init",
            workflow_file=workflow_file,
        )
        metadata_info = f"Metadata:\n  {metadata_path.name}\n\n"
    except Exception as exc:
        # Metadata is additive, so project creation should still succeed on failure.
        console.print(
            f"[yellow]Warning:[/yellow] Failed to write study metadata: {exc}"
        )

    console.print()
    console.print(
        Panel.fit(
            f"[green]✓[/green] Project created successfully!\n\n"
            f"{metadata_info}"
            f"Next steps:\n"
            f"  cd {name}\n"
            f"  concore validate workflow.graphml\n"
            f"  concore run workflow.graphml",
            title="Success",
            border_style="green",
        )
    )
