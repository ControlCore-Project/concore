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

# Run your workflow
concore run workflow.graphml

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

### `concore run <workflow_file>`

Generates and optionally builds a workflow from a GraphML file.

**Options:**
- `-s, --source <dir>` - Source directory (default: src)
- `-o, --output <dir>` - Output directory (default: out)
- `-t, --type <type>` - Execution type: windows, posix, or docker (default: windows)
- `--auto-build` - Automatically run build script after generation

**Example:**
```bash
concore run workflow.graphml --source ./src --output ./build --auto-build
```

### `concore validate <workflow_file>`

Validates a GraphML workflow file before running.

Checks:
- Valid XML structure
- GraphML format compliance
- Node and edge definitions
- File references and naming conventions
- ZMQ vs file-based communication

**Example:**
```bash
concore validate workflow.graphml
```

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
   concore run workflow.graphml --auto-build
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
