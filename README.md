# The CONTROL-CORE Framework
[CONTROL-CORE](https://github.com/ControlCore-Project/) is a framework for closed-loop peripheral neuromodulation control systems. At its center is _concore_, a lightweight Python-based protocol to simulate neuromodulation control systems. This repository consists of the implementation of _concore_ protocol and sample (demo and neuromodulation control systems) studies. In addition to its standard Python implementation, _concore_ also supports developing studies in Matlab/Octave, Verilog, and C++.


The CONTROL-CORE framework consists of the below projects.

* _concore_: The CONTROL-CORE protocol, known as _concore_, allows modular simulation of controller and PM nodes to run on different operating systems, computing platforms, and programming languages. [This repository](https://github.com/ControlCore-Project/concore/) consists of _concore_ source code. The _concore_ documentation can be found [here](https://control-core.readthedocs.io/en/latest/index.html). For a more scientific documentation, please read our extensive [open-access research paper](https://doi.org/10.1109/ACCESS.2022.3161471).

* _concore_ Editor: This is the front-end for CONTROL-CORE. We forked [DHGWorkflow](https://github.com/ControlCore-Project/DHGWorkflow), a sibling project we developed, and extend as the _concore_ Editor. Please check out the [dev branch](https://github.com/ControlCore-Project/DHGWorkflow/tree/dev) for the _concore_ Editor.

* _Mediator_: The [Mediator](https://github.com/ControlCore-Project/mediator) allows the CONTROL-CORE studies to be distributed and run, rather than having all the programs that construct a study to be run just from a centralized location. 

* _concore-lite_: The [_concore-lite_](https://github.com/ControlCore-Project/concore-lite) repository consists of a simple example version of a _concore_ study. Please check out and run this, if you like to learn the _concore_ protocol without having to clone this large _concore_ repository.

* documentation: The [source code repository](https://github.com/ControlCore-Project/documentation) of the ReadTheDocs documentation of CONTROL-CORE.


# The _concore_ Protocol

Please follow the [ReadTheDocs](https://control-core.readthedocs.io/en/latest/index.html) documentation and the [_concore-lite_](https://github.com/ControlCore-Project/concore-lite) repository to get started quick.

Installation instructions for concore can be found [here](https://control-core.readthedocs.io/en/latest/installation.html). Usage instructions can be found [here](https://control-core.readthedocs.io/en/latest/usage.html).


# Citing _concore_

If you use _concore_ in your research, please cite the below paper:

* Kathiravelu, P., Arnold, M., Fleischer, J., Yao, Y., Awasthi, S., Goel, A. K., Branen, A., Sarikhani, P., Kumar, G., Kothare, M. V., and Mahmoudi, B. **CONTROL-CORE: A Framework for Simulation and Design of Closed-Loop Peripheral Neuromodulation Control Systems**. In IEEE Access. March 2022. https://doi.org/10.1109/ACCESS.2022.3161471 
