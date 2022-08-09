# CONTROL-CORE: A Framework for Simulationand Design of Closed-Loop Peripheral Neuromodulation Control Systems

[CONTROL-CORE](https://github.com/ControlCore-Project/) is a design and simulation framework for closed-loop peripheral neuromodulation control systems. At its center is _concore_, a lightweight protocol to simulate neuromodulation control systems. This repository consists of the implementation of _concore_ protocol and sample (demo and neuromodulation control systems) studies. In addition to its default standard Python implementation, _concore_ also supports developing studies in Matlab/Octave, Verilog, and C++. _concore_ also aims to support more language programs in the future.

# The CONTROL-CORE Framework

The CONTROL-CORE framework consists of the below projects.

* _concore_: The CONTROL-CORE protocol, known as _concore_, allows modular simulation of controller and PM nodes to run on different operating systems, computing platforms, and programming languages. [This repository](https://github.com/ControlCore-Project/concore/) consists of _concore_ source code. The _concore_ documentation can be found [here](https://control-core.readthedocs.io/en/latest/index.html). A _concore_ study can be developed from programss written in different languages. That means, _concore_ facilitates a seamless communication across codes developed in different languages that it supports, through its simple file-based data sharing between the programs.

* _concore_ Editor: This is the front-end for CONTROL-CORE. We forked [DHGWorkflow](https://github.com/ControlCore-Project/DHGWorkflow), a sibling project we developed, and extend it as the _concore_ Editor. Please check out the [dev branch](https://github.com/ControlCore-Project/DHGWorkflow/tree/dev) for the _concore_ Editor.

* _Mediator_: The [Mediator](https://github.com/ControlCore-Project/mediator) allows the CONTROL-CORE studies to be distributed and run, rather than having all the programs that construct a study to be run just from a centralized location. 

* _concore-lite_: The [_concore-lite_](https://github.com/ControlCore-Project/concore-lite) repository consists of a simple example version of a _concore_ study. Please check out and run this, if you like to learn the _concore_ protocol without having to clone this large _concore_ repository.

* documentation: The [source code repository](https://github.com/ControlCore-Project/documentation) of the ReadTheDocs documentation of CONTROL-CORE.


# The _concore_ Protocol

_concore_ enables composing studies from programs developed in different languages. Currently supported languages are, Python, Matlab/Octave, Verilog, and C++. The studies are designed through the visual _concore_ Editor (DHGWorkflow) and interpreted into _concore_ through its parser. Neural control systems consist of loops (dicycles). Therefore, they cannot be represented by classic workflow standards (such as CWL or WDL). Therefore, _concore_ addresses a significant research gap to model closed-loop neuromodulation control systems. The _concore_ protocol shares data between the programs through file sharing, with no centralized entity (a broker or an orchestrator) to arbitrate communications between the programs. (In the distributed executions, the CONTROL-CORE Mediator enables connecting the disjoint pieces of the study through REST APIs).


# Installation and Getting Started Guide

Please follow the [ReadTheDocs](https://control-core.readthedocs.io/en/latest/index.html) documentation and the [_concore-lite_](https://github.com/ControlCore-Project/concore-lite) repository to get started quick.

Installation instructions for concore can be found [here](https://control-core.readthedocs.io/en/latest/installation.html). Usage instructions can be found [here](https://control-core.readthedocs.io/en/latest/usage.html).

For a detailed and more scientific documentation, please read our extensive [open-access research paper on CONTROL-CORE](https://doi.org/10.1109/ACCESS.2022.3161471). This paper has a complete discussion on the CONTROL-CORE architecture and deployment, together with the commands to execute the studies in different programming languages and programming environments (Ubuntu, Windows, MacOS, Docker, and distributed execution).


# The _concore_ Repository

_concore contains programs (such as physiological models or more commonly called "PMs" and controllers) and studies (i.e., graphml files that represents the studies as workflows). The _wrappers_ enable seamlessly extending a study into a distributed one with the CONTROL-CORE Mediator.

_concore_ repository consists of several scripts at its root level. The demo folder consists of several sample programs and studies, mostly toy examples to learn the protocol. The ratc folder consists of the programs and studies of the rat cardiac experiments we developed with _concore_.

If you have a bug to report in one of the CONTROL-CORE projects, please report it through relevant Issue Tracker. Similarly, please feel free to contribute your studies and code enhancements using pull requests. Questions and discussions can be made through the relevant Discussions forum.

The _concore Issues can be reported [here](https://github.com/ControlCore-Project/concore/issues).

The _concore_ discussion forum can be found [here](https://github.com/ControlCore-Project/concore/discussions).

Please make sure to send your _concore_ pull requests to the [dev branch](https://github.com/ControlCore-Project/concore/tree/dev).

# Community Outreach

The CONTROL-CORE project has tremendously benefitted from open-source. We have been a part of the Google Summer of Code (GSoC), via the Department of Biomedical Informatics, Emory University as the mentoring organization. DHGWorkflow (which is adopted as the _concore_ Editor) was developed by the GSoC 2021 contributor. For GSoC 2022, we have 2 contributors - one working on _concore_ Editor and the other one on the _concore_ itself.

Please use the GitHub discussion forums for user-queries. For GSoC and similar open-source contributions, as well as for other real-time user queries, feel free to join the Emory BMI slack workspace using the link - http://bit.ly/emory-bmi and find the channel "concore."

# Citing _concore_

If you use _concore_ in your research, please cite the below paper:

* Kathiravelu, P., Arnold, M., Fleischer, J., Yao, Y., Awasthi, S., Goel, A. K., Branen, A., Sarikhani, P., Kumar, G., Kothare, M. V., and Mahmoudi, B. **CONTROL-CORE: A Framework for Simulation and Design of Closed-Loop Peripheral Neuromodulation Control Systems**. In IEEE Access. March 2022. https://doi.org/10.1109/ACCESS.2022.3161471 
