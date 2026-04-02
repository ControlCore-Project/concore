# concore Configuration Reference

This document describes the configuration files used by `mkconcore.py` to locate compilers, runtimes, and Docker settings. All config files are read from `CONCOREPATH` — the directory containing `concore.py`.

## How CONCOREPATH Is Resolved

`mkconcore.py` resolves `CONCOREPATH` in the following order:

1. The directory containing `mkconcore.py` itself (if `concore.py` exists there)
2. The current working directory (if `concore.py` exists there)
3. Falls back to the `mkconcore.py` directory

---

## Configuration Files

### `concore.tools`

**Purpose:** Override compiler and runtime paths for all supported languages.

**Format:** Key-value pairs, one per line. Lines starting with `#` and blank lines are ignored.

```
KEY=value
```

**Supported Keys:**

| Key | Platform | Default | Description |
|-----|----------|---------|-------------|
| `CPPWIN` | Windows | `g++` | C++ compiler |
| `CPPEXE` | POSIX | `g++` | C++ compiler |
| `VWIN` | Windows | `iverilog` | Verilog compiler |
| `VEXE` | POSIX | `iverilog` | Verilog compiler |
| `PYTHONWIN` | Windows | `python` | Python interpreter |
| `PYTHONEXE` | POSIX | `python3` | Python interpreter |
| `MATLABWIN` | Windows | `matlab` | MATLAB executable |
| `MATLABEXE` | POSIX | `matlab` | MATLAB executable |
| `OCTAVEWIN` | Windows | `octave` | GNU Octave executable |
| `OCTAVEEXE` | POSIX | `octave` | GNU Octave executable |
| `JAVACWIN` | Windows | `javac` | Java compiler |
| `JAVACEXE` | POSIX | `javac` | Java compiler |
| `JAVAWIN` | Windows | `java` | Java runtime |
| `JAVAEXE` | POSIX | `java` | Java runtime |

**Example (`concore.tools`):**

```
CPPEXE=/usr/bin/g++
PYTHONEXE=/opt/python3.11/bin/python3
VEXE=/usr/local/bin/iverilog
OCTAVEEXE=/usr/bin/octave
JAVACEXE=/usr/lib/jvm/java-17/bin/javac
JAVAEXE=/usr/lib/jvm/java-17/bin/java
```

**Windows Example:**

```
CPPWIN=C:\MinGW\bin\g++.exe
PYTHONWIN=C:\Python313\python.exe
JAVACWIN=C:\Program Files\Java\jdk-17\bin\javac.exe
JAVAWIN=C:\Program Files\Java\jdk-17\bin\java.exe
```

---

### `concore.octave`

**Purpose:** When this file is present, `.m` files are treated as GNU Octave instead of MATLAB. The file content is ignored — only its existence matters.

**Format:** Empty file (presence-based flag).

**How to enable:**

```bash
touch $CONCOREPATH/concore.octave
```

**How to disable:** Delete the file.

---

### `concore.mcr`

**Purpose:** Path to the local MATLAB Compiler Runtime (MCR) installation. Used when running compiled MATLAB executables instead of MATLAB directly.

**Format:** Single line containing the absolute path to the MCR installation.

**Default:** `~/MATLAB/R2021a`

**Example (`concore.mcr`):**

```
/opt/matlab/mcr/v913
```

**Windows Example:**

```
C:\Program Files\MATLAB\R2021a\runtime\win64
```

---

### `concore.sudo`

**Purpose:** Override the Docker executable command. Originally intended to control whether Docker runs with `sudo`, but can specify any container runtime (Docker, Podman, etc.).

**Format:** Single line containing the Docker executable command.

**Default:** `docker` (from `DOCKEREXE` environment variable, or the literal string `docker`)

**Example (`concore.sudo`):**

```
sudo docker
```

**To use Podman instead of Docker:**

```
podman
```

---

### `concore.repo`

**Purpose:** Override the Docker Hub repository prefix used when pulling pre-built images.

**Format:** Single line containing the Docker Hub username or organization.

**Default:** `markgarnold`

**Example (`concore.repo`):**

```
myorganization
```

This means Docker images will be pulled from `myorganization/<image-name>` instead of `markgarnold/<image-name>`.

---

## Environment Variables

Environment variables are read **before** config files and provide initial defaults. Config files override environment variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `CONCORE_CPPWIN` | `g++` | Windows C++ compiler |
| `CONCORE_CPPEXE` | `g++` | POSIX C++ compiler |
| `CONCORE_VWIN` | `iverilog` | Windows Verilog compiler |
| `CONCORE_VEXE` | `iverilog` | POSIX Verilog compiler |
| `CONCORE_PYTHONEXE` | `python3` | POSIX Python interpreter |
| `CONCORE_PYTHONWIN` | `python` | Windows Python interpreter |
| `CONCORE_MATLABEXE` | `matlab` | POSIX MATLAB executable |
| `CONCORE_MATLABWIN` | `matlab` | Windows MATLAB executable |
| `CONCORE_OCTAVEEXE` | `octave` | POSIX GNU Octave executable |
| `CONCORE_OCTAVEWIN` | `octave` | Windows GNU Octave executable |
| `CONCORE_JAVACEXE` | `javac` | POSIX Java compiler |
| `CONCORE_JAVACWIN` | `javac` | Windows Java compiler |
| `CONCORE_JAVAEXE` | `java` | POSIX Java runtime |
| `CONCORE_JAVAWIN` | `java` | Windows Java runtime |
| `DOCKEREXE` | `docker` | Docker executable |

---

## Precedence (Priority Order)

When `mkconcore.py` resolves a tool path, the following precedence applies (highest priority first):

1. **`concore.tools` file** — overrides everything for compiler/runtime paths
2. **`concore.sudo` file** — overrides `DOCKEREXE` for Docker executable
3. **`concore.repo` file** — overrides `DOCKEREPO` for Docker repository
4. **Environment variables** (`CONCORE_*`, `DOCKEREXE`) — initial defaults
5. **Hardcoded defaults** — `g++`, `python3`, `iverilog`, `octave`, `docker`, etc.

For `concore.octave` and `concore.mcr`, there is no environment variable equivalent — they are controlled only by file presence/content.

---

## Quick Start

**Minimal setup (Python-only study on Linux):**

No config files needed — defaults work out of the box.

**Typical setup (Python + C++ on Linux):**

```bash
# Only needed if g++ is not on PATH
echo "CPPEXE=/usr/local/bin/g++-13" > $CONCOREPATH/concore.tools
```

**Windows setup (Python + C++):**

```
CPPWIN=C:\MinGW\bin\g++.exe
PYTHONWIN=C:\Python313\python.exe
```

**Docker without sudo:**

```bash
echo "docker" > $CONCOREPATH/concore.sudo
```

**Using Octave instead of MATLAB:**

```bash
touch $CONCOREPATH/concore.octave
```

---

## Diagnostic

Run `concore doctor` to see all detected tools, config file status, and environment variables in a single readiness report:

```
$ concore doctor
```

See the [CLI README](../concore_cli/README.md) for details.
