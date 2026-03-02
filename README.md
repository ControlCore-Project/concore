# CONTROL-CORE: Integrated Development Environment for Closed-loop Neuromodulation Control Systems.

[CONTROL-CORE](https://github.com/ControlCore-Project/) is a design and simulation framework, functioning as a visual Integrated Development Environment (IDE) for Closed-loop Neuromodulation Control Systems. At its center is _concore_, a lightweight protocol to simulate neuromodulation control systems. This repository consists of the implementation of _concore_ protocol and sample (demo and neuromodulation control systems) studies. In addition to its default standard Python implementation, _concore_ also supports developing studies in Matlab/Octave, Verilog, and C++. _concore_ also aims to support more language programs in the future.

# The CONTROL-CORE Framework

The CONTROL-CORE framework consists of the below projects.

* _concore_: The CONTROL-CORE protocol, known as _concore_, allows modular simulation of controller and PM nodes to run on different operating systems, computing platforms, and programming languages. [This repository](https://github.com/ControlCore-Project/concore/) consists of _concore_ source code. The _concore_ documentation can be found [here](https://control-core.readthedocs.io/en/latest/index.html). A _concore_ study can be developed from programs written in different languages. That means, _concore_ facilitates a seamless communication across codes developed in different languages that it supports, through its simple file-based data sharing between the programs.

* _concore_ Editor: This is the front-end for CONTROL-CORE. We forked [DHGWorkflow](https://github.com/ControlCore-Project/DHGWorkflow), a sibling project we developed, and extend it as the _concore_ Editor. 

* _Mediator_: The [Mediator](https://github.com/ControlCore-Project/mediator) allows the CONTROL-CORE studies to be distributed and run, rather than having all the programs that construct a study to be run just from a centralized location. 

* _concore-lite_: The [_concore-lite_](https://github.com/ControlCore-Project/concore-lite) repository consists of a simple example version of a _concore_ study. Please check out and run this, if you like to learn the _concore_ protocol without having to clone this large _concore_ repository.

* documentation: The [source code repository](https://github.com/ControlCore-Project/documentation) of the ReadTheDocs documentation of CONTROL-CORE.


# The _concore_ Protocol

_concore_ enables composing studies from programs developed in different languages. Currently supported languages are, Python, Matlab/Octave, Verilog, and C++. The studies are designed through the visual _concore_ Editor (DHGWorkflow) and interpreted into _concore_ through its parser. Neural control systems consist of loops (dicycles). Therefore, they cannot be represented by classic workflow standards (such as CWL or WDL). Therefore, _concore_ addresses a significant research gap to model closed-loop neuromodulation control systems. The _concore_ protocol shares data between the programs through file sharing, with no centralized entity (a broker or an orchestrator) to arbitrate communications between the programs. (In the distributed executions, the CONTROL-CORE Mediator enables connecting the disjoint pieces of the study through REST APIs).


# Installation and Getting Started Guide

Please follow the [ReadTheDocs](https://control-core.readthedocs.io/en/latest/index.html) documentation and the [_concore-lite_](https://github.com/ControlCore-Project/concore-lite) repository to get started quick.

Installation instructions for concore can be found [here](https://control-core.readthedocs.io/en/latest/installation.html). Usage instructions can be found [here](https://control-core.readthedocs.io/en/latest/usage.html).

## Command-Line Interface (CLI)

_concore_ now includes a command-line interface for easier workflow management. Install it with:

```bash
pip install -e .
```

Quick start with the CLI:

```bash
# Create a new project
concore init my-project

# Validate your workflow
concore validate workflow.graphml

# Run your workflow
concore run workflow.graphml --auto-build

# Monitor running processes
concore status

# Stop all processes
concore stop
```

For detailed CLI documentation, see [concore_cli/README.md](concore_cli/README.md).

## Configuration

_concore_ supports customization through configuration files in the `CONCOREPATH` directory (defaults to the _concore_ installation directory):

- **concore.tools** - Override tool paths (one per line, `KEY=value` format):
  ```
  CPPEXE=/usr/local/bin/g++-12
  PYTHONEXE=/usr/bin/python3.11
  VEXE=/opt/iverilog/bin/iverilog
  OCTAVEEXE=/snap/bin/octave
  ```
  Supported keys: `CPPWIN`, `CPPEXE`, `VWIN`, `VEXE`, `PYTHONEXE`, `PYTHONWIN`, `MATLABEXE`, `MATLABWIN`, `OCTAVEEXE`, `OCTAVEWIN`

- **concore.octave** - Treat `.m` files as Octave instead of MATLAB (presence = enabled)
- **concore.mcr** - MATLAB Compiler Runtime path (single line)
- **concore.sudo** - Docker command override (e.g., `docker` instead of `sudo docker`)
- **concore.repo** - Docker repository override

Tool paths can also be set via environment variables (e.g., `CONCORE_CPPEXE=/usr/bin/g++`). Priority: config file > env var > defaults.

### Docker Executable Configuration

The Docker executable used by generated scripts (`build`, `run`, `stop`, `maxtime`, `params`, `unlock`) is controlled by the `DOCKEREXE` variable. It defaults to `docker` and can be overridden in three ways (highest priority first):

1. **Config file** — Write the desired command into `concore.sudo` in your `CONCOREPATH` directory:
   ```
   docker
   ```
   This remains the highest-priority override, preserving backward compatibility.

2. **Environment variable** — Set `DOCKEREXE` before running `mkconcore.py`:
   ```bash
   # Rootless Docker / Docker Desktop (macOS, Windows)
   export DOCKEREXE="docker"

   # Podman
   export DOCKEREXE="podman"

   # Traditional Linux with sudo
   export DOCKEREXE="sudo docker"
   ```

3. **Default** — If neither the config file nor the environment variable is set, `docker` is used.

> **Note:** Previous versions defaulted to `sudo docker`, which failed on Docker Desktop (macOS/Windows), rootless Docker, and Podman. The new default (`docker`) works out of the box on those platforms. If you still need `sudo`, set `DOCKEREXE="sudo docker"` via the environment variable or `concore.sudo` config file.

### Security Configuration

Set a secure secret key for the Flask server before running in production:

```bash
export FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

Do **NOT** commit your secret key to version control. If `FLASK_SECRET_KEY` is not set, a temporary random key will be generated automatically (suitable for local development only).

For a detailed and more scientific documentation, please read our extensive [open-access research paper on CONTROL-CORE](https://doi.org/10.1109/ACCESS.2022.3161471). This paper has a complete discussion on the CONTROL-CORE architecture and deployment, together with the commands to execute the studies in different programming languages and programming environments (Ubuntu, Windows, MacOS, Docker, and distributed execution).

## C++ ZMQ Transport

`concore.hpp` supports ZMQ-based communication as an opt-in transport alongside the default file-based I/O.

To enable it, compile with `-DCONCORE_USE_ZMQ` and link against cppzmq:

```bash
g++ -DCONCORE_USE_ZMQ my_node.cpp -lzmq -o my_node
```

In your C++ node, register a ZMQ port before reading or writing:

```cpp
#include "concore.hpp"

Concore c;
c.init_zmq_port("in1", "bind", "tcp://*:5555", "REP");
c.init_zmq_port("out1", "connect", "tcp://localhost:5556", "REQ");

vector<double> val = c.read("in1", "", "0.0");
c.write("out1", "", val, 0);
```

Builds without `-DCONCORE_USE_ZMQ` are unaffected.


# The _concore_ Repository

_concore_ contains programs (such as physiological models or more commonly called "PMs" and controllers) and studies (i.e., graphml files that represents the studies as workflows). The _wrappers_ enable seamlessly extending a study into a distributed one with the CONTROL-CORE Mediator.

_concore_ repository consists of several scripts at its root level. The demo folder consists of several sample programs and studies, mostly toy examples to learn the protocol. The ratc folder consists of the programs and studies of the rat cardiac experiments we developed with _concore_.

If you have a bug to report in one of the CONTROL-CORE projects, please report it through relevant Issue Tracker. Similarly, please feel free to contribute your studies and code enhancements using pull requests. Questions and discussions can be made through the relevant Discussions forum.

The _concore_ Issues can be reported [here](https://github.com/ControlCore-Project/concore/issues).

The _concore_ discussion forum can be found [here](https://github.com/ControlCore-Project/concore/discussions).

Please make sure to send your _concore_ pull requests to the [dev branch](https://github.com/ControlCore-Project/concore/tree/dev).


# Citing _concore_

If you use _concore_ in your research, please cite the below papers:

* Kathiravelu, P., Arnold, M., Vijay, S., Jagwani, R., Goyal, P., Goel, A.K., Li, N., Horn, C., Pan, T., Kothare, M. V., and Mahmoudi, B. **Distributed Executions with CONTROL-CORE Integrated Development Environment (IDE) for Closed-loop Neuromodulation Control Systems.** In Cluster Computing – The Journal of Networks Software Tools and Applications (CLUSTER). May 2025. Accepted. Springer.
* Kathiravelu, P., Arnold, M., Fleischer, J., Yao, Y., Awasthi, S., Goel, A. K., Branen, A., Sarikhani, P., Kumar, G., Kothare, M. V., and Mahmoudi, B. **CONTROL-CORE: A Framework for Simulation and Design of Closed-Loop Peripheral Neuromodulation Control Systems**. In IEEE Access. March 2022. https://doi.org/10.1109/ACCESS.2022.3161471 
