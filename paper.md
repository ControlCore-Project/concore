---
title: '_concore_ for Simulating Closed-Loop Peripheral Neuromodulation Control Systems'
tags:
  - Neuroscience
  - Control Systems
  - Python
  - Interoperability
  - Workflows
authors:
  - name: Pradeeban Kathiravelu
    orcid: 0000-0002-0335-0458
    equal-contrib: true
    corresponding: true 
    affiliation: 1
  - name: Mark Arnold
    orchid: 0000-0001-5175-2374
    equal-contrib: true
    affiliation: 2
  - name: Yuyu Yao
    affiliation: 2
  - name: Jake Fleischer
    affiliation: 2
  - name:  Shubham Awasthi 
    orchid: 0000-0002-9913-9875
    affiliation: 3
  - name: Aviral Kumar Goel
    affiliation: 4
  - name: Amit Kumar
    affiliation: 5
  - name: Andrew Branen
    affiliation: 6
  - name: Parisa Sarikhani
    affiliation: 1
  - name: Gautam Kumar
    affiliation: 6
  - name: Mayuresh V. Kothare
    orchid: 0000-0001-7681-7445
    affiliation: 2
  - name: Babak Mahmoudi
    affiliation: "1, 7"

affiliations:
 - name: Department of Biomedical Informatics, Emory University, Atlanta, GA 30322, USA
   index: 1
 - name: Department of Chemical \& Biomolecular Engineering, Lehigh University, Bethlehem, PA 18015, USA
   index: 2
 - name: School of Information Technology and Engineering, Vellore Institute of Technology, Vellore, TN 632014, India
   index: 3
 - name: Department of Computer Science and Information Systems, Birla Institute of Technology and Science, Pilani, K. K. Birla Goa Campus, Sancoale, GA 403726, India.
   index: 4
 - name: School of Engineering, Jawaharlal Nehru University, New Delhi, 110067, India.
   index: 5
 - name: Department of Chemical and Materials Engineering, San José State University, San José, CA, 95192, USA.
   index: 6
 - name: Department of Biomedical Engineering, Georgia Institute of Technology, Atlanta, GA 30332, USA
   index: 7
date: 9 August 2022
bibliography: paper.bib

---
# Summary
Closed-loop Vagus Nerve Stimulation (VNS) based on physiological feedback signals is a promising approach to regulating organ functions and developing therapeutic devices. Designing closed-loop neurostimulation systems requires simulation environments and computing infrastructures that support i) modeling the physiological responses of organs under neuromodulation, also known as physiological models (PMs), and ii) the interaction between the PMs and the neuromodulation control algorithms. However, existing simulation platforms do not support closed-loop VNS control systems modeling without extensive rewriting of computer code and manual deployment and configuration of programs.

The CONTROL-CORE framework aims to develop a flexible software platform for designing and implementing closed-loop VNS systems. The CONTROL-CORE framework consists of the _concore_ protocol at its core. In addition, it contains a visual _concore_ editor and a Mediator architecture that facilitates a distributed execution of _concore_ studies.


This paper presents the _concore_ protocol, which allows seamless communication between the programs (such as PMs and controllers) that compose a study. _concore_ allows simulations to run on different operating systems, be developed in various programming languages (such as Matlab, Python, C++, and Verilog), and be run locally, in containers, and in a distributed fashion. The _concore_ Editor lets the users to create studies from the programs in a visual drag-and-drop manner and store them as a GraphML file. _concore_ consists of a parser that parses the studies represented in the GraphML file and start the execution of the studies until the specified maxtime value is met.


We tested _concore_ in the context of closed-loop control of cardiac physiological models, including pulsatile and nonpulsatile rat models. These were tested using various controllers such as Model Predictive Control and Long-Short-Term Memory-based controllers. Our wide range of use cases and evaluations show the performance, flexibility, and usability of _concore_. The scientific contributions of _concore_ protocol and the CONTROL-CORE framework, along with these sample closed-loop neuromodulation control systems studies have been extensively discussed in our previous work [@kathiravelu2022control].


# Statement of need

Workflow frameworks can run a series of containerized programs, with predefined start and end steps, as a modular workflow. Such workflows do not have a cycle, by definition. A neuromodulation control system comprises feedback loops represented by directed cycles (dicycles). The presence of a dicycle violates the core tenet of classic workflow frameworks, such as Common Workflow Language (CWL) and Workflow Description Language (WDL), which expect the studies to be represented by a directed acyclic graph (DAG). Furthermore, control systems run the same program multiple times as part of the execution with feedback. Consequently, overheads imposed by workflow frameworks, significantly when handling implementations across diverse programming languages and execution environments, are magnified in the case of a closed-loop execution.

Interoperability plays a significant role in scientific research. Therefore, we should support the modeling and simulation of studies composed of programs (such as the controllers and PMs) developed in different programming languages, executing on different execution modes (local, distributed, or containerized). _concore_ is designed for efficiency in control systems' specific use cases, supporting interoperable communication and data exchange between programs from independent researchers. The simple file-based communication and synchronization, without a centralized workflow orchestrator, enables interoperable executions with high performance.
# Acknowledgment

This work was supported in part by the National Institutes of Health under Grant OT2OD030535 and Google Summer of Code (GSoC) 2021 and 2022 projects. The authors acknowledge the guidance from Tyler Best and Herbert Sauro. The authors appreciate the assistance with OSPARC that they received from the staff at IT'IS, especially Sylvain Anderegg, Pedro Crespo-Valero, Elisabetta Iavarone, Andrei Neagu, Esra Neufeld, and Katie Zhuang.

# References
