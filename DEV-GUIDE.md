# Concore Developer Guide

## `concore init --interactive`

The interactive init wizard lets users scaffold a new multi-language concore project without writing any boilerplate by hand.

### Usage

```bash
concore init <project-name> --interactive
# or shorthand
concore init <project-name> -i
```

The wizard prompts for each supported language with a `y/n` question (default: yes):

```
Select the node types to include  (Enter = yes)

  Include Python node?        [Y/n]
  Include C++ node?           [Y/n]
  Include Octave/MATLAB node? [Y/n]
  Include Verilog node?       [Y/n]
  Include Java node?          [Y/n]
```

### What gets generated

For each selected language, the wizard:

1. Creates a **source stub** in `src/` with the correct concore API calls for that language.
2. Adds an **unconnected node** to `workflow.graphml`, colour-coded and vertically positioned for easy viewing in yEd.

Example output for Python + Java selected:

```
my_project/
├── workflow.graphml     ← 2 unconnected nodes
├── src/
│   ├── script.py        ← Python stub
│   └── Script.java      ← Java stub
├── README.md
└── STUDY.json
```

### Architecture

The feature lives entirely in `concore_cli/commands/init.py`:

| Symbol | Role |
|---|---|
| `LANGUAGE_NODES` | Dict mapping language key → `label`, `filename`, node `color`, source `stub` |
| `GRAPHML_HEADER` | XML template for the GraphML wrapper; `project_name` is escaped via `xml.sax.saxutils.quoteattr` |
| `GRAPHML_NODE` | XML template for a single node block |
| `run_wizard()` | Prompts y/n for each language; returns list of selected keys |
| `_build_graphml()` | Assembles the full GraphML string from selected languages |
| `init_project_interactive()` | Orchestrates directory creation, file writes, and success output |

---

## Adding a New Language

Adding Julia (or any other language) to the interactive wizard is a **one-file change** — just add an entry to the `LANGUAGE_NODES` dictionary in `concore_cli/commands/init.py`.

### Step-by-step: adding Julia

**1. Add the entry to `LANGUAGE_NODES`** in `concore_cli/commands/init.py`:

```python
"julia": {
    "label": "Julia",
    "filename": "script.jl",
    "color": "#9558b2",          # Julia purple
    "stub": (
        "using Concore\n\n"
        "Concore.state.delay   = 0.02\n"
        "Concore.state.inpath  = \"./in\"\n"
        "Concore.state.outpath = \"./out\"\n\n"
        "maxtime = default_maxtime(100.0)\n"
        'init_val = "[0.0, 0.0]"\n\n'
        "while Concore.state.simtime < maxtime\n"
        "    while unchanged()\n"
        '        val = Float64.(concore_read(1, "data", init_val))\n'
        "    end\n"
        "    # TODO: process val\n"
        "    result = val .* 2\n"
        '    concore_write(1, "result", result, 0.0)\n'
        "end\n"
        "println(\"retry=$(Concore.state.retrycount)\")\n"
    ),
},
```

Key Julia API points (based on real concore Julia scripts):

| Element | Julia equivalent |
|---|---|
| Import | `using Concore` |
| Setup | `Concore.state.delay`, `.inpath`, `.outpath` |
| Max time | `default_maxtime(100.0)` — returns the value |
| Sim time | `Concore.state.simtime` |
| Unchanged check | `unchanged()` — no module prefix |
| Read | `concore_read(port, name, initstr)` — snake\_case, no prefix |
| Write | `concore_write(port, name, val, delta)` — snake\_case, no prefix |
| Type cast | `Float64.(concore_read(...))` to ensure numeric type |

**2. That's it.** No other files need to change — the wizard, GraphML builder, and file writer all iterate over `LANGUAGE_NODES` dynamically.

### Node colours used

| Language | Hex colour |
|---|---|
| Python | `#ffcc00` (yellow) |
| C++ | `#ae85ca` (purple) |
| Octave/MATLAB | `#6db3f2` (blue) |
| Verilog | `#f28c8c` (red) |
| Java | `#a8d8a8` (green) |
| Julia *(proposed)* | `#9558b2` (Julia purple) |

---
