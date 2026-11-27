# Concore CLI

A command-line interface for managing concore neuromodulation workflows.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Create a new project
concore init my-project

# Navigate to your project
cd my-project

# Validate your workflow
concore validate workflow.graphml

# Build your workflow
concore build workflow.graphml

# Start the built study and wait for it to finish
concore run out --wait

# Check running processes
concore status

# Stop all processes
concore stop
```

## Commands

### `concore init <name>`

Creates a new concore project with a basic structure.

**Options:**
- `--template` - Template type to use (default: basic)

**Example:**
```bash
concore init my-workflow
```

Creates:
```
my-workflow/
├── workflow.graphml    # Sample workflow definition
├── src/
│   └── script.py      # Sample processing script
└── README.md          # Project documentation
```

### `concore build <workflow_file>`

Compiles a concore workflow GraphML file into executable scripts (POSIX, Windows, or Docker).

**Options:**
- `-s, --source <dir>` - Source directory (default: src)
- `-o, --output <dir>` - Output directory (default: out)
- `-t, --type <type>` - Execution type: windows, posix, or docker (default: windows)
- `--auto-build` - Automatically run build script after generation
- `--compose` - Generate `docker-compose.yml` (only valid with `--type docker`)

**Example:**
```bash
concore build workflow.graphml --source ./src --output ./build --auto-build
```

Docker compose example:

```bash
concore build workflow.graphml --source ./src --output ./out --type docker --compose
cd out
docker compose up
```

### `concore validate <workflow_file>`

Validates a GraphML workflow file before running.

**Options:**
- `-s, --source <dir>` - Source directory to verify file references exist

Checks:
- Valid XML structure
- GraphML format compliance
- Node and edge definitions
- File references and naming conventions
- Source file existence (when --source provided)
- ZMQ port conflicts and reserved ports
- Circular dependencies (warns for control loops)
- Edge connectivity

**Options:**
- `-s, --source <dir>` - Source directory (default: src)

**Example:**
```bash
concore validate workflow.graphml
concore validate workflow.graphml --source ./src
```

### `concore run <study_dir>`

Starts a built study (the folder `concore build` created) by running its generated `run` script, so you do not have to `cd` into it.

**Options:**
- `--build` - Run the study's `build` script first (stops if the build fails)
- `--wait` - Wait until every node has exited. `Ctrl+C` stops the study's nodes
- `--timeout <seconds>` - With `--wait`, stop the study after this many seconds (exit code 124)

**Examples:**
```bash
concore run out
concore run out --build --wait
concore run out --wait --timeout 300
```

**Notes:**
- `--wait` needs the node process ids that POSIX and macOS builds record; for Docker and Windows builds the study is started and a warning explains there is nothing to wait for.
- `--wait` reports when the nodes have exited, not whether they succeeded. Check each node's `concoreout.txt` for errors.
- Exit codes: `0` success, `124` timeout, `130` interrupted, or the exit code of the failing script.

### `concore status`

Shows all currently running concore processes with details:
- Process ID (PID)
- Process name
- Uptime
- Memory usage
- Command

**Example:**
```bash
concore status
```

### `concore stop`

Stops all running concore processes. Prompts for confirmation before proceeding.

**Example:**
```bash
concore stop
```

## Development Workflow

1. **Create a new project**
   ```bash
   concore init my-neuro-study
   cd my-neuro-study
   ```

2. **Edit your workflow**
   - Open `workflow.graphml` in yEd or similar GraphML editor
   - Add nodes for your processing steps
   - Connect nodes with edges to define data flow

3. **Add processing scripts**
   - Place your Python/C++/MATLAB/Verilog files in the `src/` directory
   - Reference them in your workflow nodes

4. **Validate before running**
   ```bash
   concore validate workflow.graphml
   ```

5. **Generate and run**
   ```bash
   concore build workflow.graphml --auto-build
   cd out
   ./run.bat  # or ./run on Linux/Mac
   ```

6. **Monitor execution**
   ```bash
   concore status
   ```

7. **Stop when done**
   ```bash
   concore stop
   ```

## Workflow File Format

Nodes should follow the format: `ID:filename.ext`

Example:
```
N1:controller.py
N2:processor.cpp
M1:analyzer.m
```

Supported file types:
- `.py` - Python
- `.cpp` - C++
- `.m` - MATLAB/Octave
- `.v` - Verilog
- `.java` - Java

## Troubleshooting

**Issue: "Output directory already exists"**
- Remove the existing output directory or choose a different name
- Use `concore stop` to terminate any running processes first

**Issue: Validation fails**
- Check that your GraphML file is properly formatted
- Ensure all nodes have labels in the format `ID:filename.ext`
- Verify that edge connections reference valid nodes

**Issue: Processes won't stop**
- Try running `concore stop` with administrator/sudo privileges
- Manually kill processes using Task Manager (Windows) or `kill` command (Linux/Mac)
