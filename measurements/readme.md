# Project Measurements
This repository contains the source code and studies for various system performance measurements. All studies are organized into dedicated folders for easy navigation and execution.

# Running the Measurement Studies
To run any of the studies, navigate to the respective folder and execute the provided source code using concore.

For example, to run a CPU measurement study:

1. Navigate to the CPU directory.

2. Execute the relevant script(s) within that folder using concore.

The output will provide the measured results specific to each study.

# Study Folders and Their Focus
* CPU
This folder contains studies and source code for measuring CPU resource usage. Running these will help you understand how much processing power is consumed by the application under test.

* Latency
This folder houses studies and source code dedicated to measuring communication latency. These studies are designed to quantify the delay in data transfer between systems.

* Throughput
Within this folder, you'll find studies and source code for measuring data throughput. These will help assess the rate at which data can be processed or transferred over a given period.

# Communication Measurement Studies (Single System)
The following studies are designed for measurements within a single system, allowing for direct comparison of their round-trip times:

* fileOnlyCommunication
This folder contains studies and source code specifically for measuring communication times that involve only file-based interactions on a single machine.

* ZeroMQOnlyCommunication
Here you will find studies and source code focused on measuring communication times using ZeroMQ within a single system setup.

# Network Communication Measurements (Two Systems Required)
For the Latency, Throughput, and CPU Usage measurements, two different systems are required. These systems should be connected to the same network to ensure efficient, accurate communication between them. This setup is crucial for effectively evaluating network-dependent performance metrics.

# Important Note on Port Variables
The measurement benchmark scripts (A.py, B.py, C.py) expect port variables such as `PORT_NAME_F1_F2`, `PORT_F1_F2`, `PORT_NAME_F2_F3`, and `PORT_F2_F3` to be injected by `copy_with_port_portname.py` during study generation. Running these scripts directly will use safe fallback defaults and may not reflect full study behavior. For accurate results, always run measurements through the study generation workflow (e.g., `makestudy`).
