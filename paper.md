---
title: '_concore_ for Simulating Closed-Loop Peripheral Neuromodulation Control Systems'
tags:
  - Neuroscience
  - Control Systems
  - Python
  - Matlab
  - Verilog
  - C++
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
  - name: Parisa Sarikhani
    affiliation: 1
  - name: Yuyu Yao
    affiliation: 2
  - name: Jake Fleischer
    affiliation: 2
  - name:  Shubham Awasthi 
    orchid: 0000-0002-9913-9875
    affiliation: 3
  - name: Aviral Kumar Goel
    affiliation: 4
  - name: Nan Li
    affiliation: 1
  - name: Amit Kumar
    affiliation: 5
  - name: Andrew Branen
    affiliation: 6
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

The CONTROL-CORE framework is a flexible software platform for designing and implementing closed-loop Vagus Nerve Stimulation (VNS) [@romero2017closed] systems in programming languages in diverse software environments. Its modular workflow approach for closed-loop executions of the VNS simulations aims to facilitate modeling organ functions as physiological models (PMs) and therapeutic devices in their early stages in a software environment. 

The CONTROL-CORE framework consists of the _concore_ protocol at its core. The _concore_ protocol allows seamless synchronized communication between the programs (such as PMs and controllers) that compose a study as a workflow. _concore_ enables simulations to run on different operating systems, be developed in various programming languages (such as Matlab, Python, C++, and Verilog), and be run locally, in containers, and a distributed fashion. 

CONTROL-CORE also consists of a Mediator implementation that facilitates the distributed execution of _concore_ studies through REST calls over the Internet. The Mediator uses wrappers developed as part of _concore_ to communicate between programs at distributed sites. When the Mediator is deployed to enable inter-organization workflows with services spread across the Internet, access control and authentication mechanisms must be used to protect the shared data. The Mediator leverages the API key-based authentication provided by the Kong API gateway to enable such Internet deployment. Figure 1 shows an illustrative CONTROL-CORE deployment across 3 distributed sites, with a public instance of the Mediator.

![A sample CONTROL-CORE distributed deployment spanning multiple sites](figures/joss-concore.png)

CONTROL-CORE contains a lightweight browser-based visual _concore_ editor, which lets the users create studies from the programs in a drag-and-drop manner. It allows the creation of directed hypergraphs to represent the studies with closed-loop from modular programs and exporting the directed hypergraph workflows as GraphML files. _concore_ consists of a parser that parses and interprets the studies represented in the GraphML file and executes the studies seamlessly as modular workflows until a specified maximum time value for the study is met. This exit condition ensures the closed-loop workflow does not run forever, as closed-loop studies do not contain a predefined end step, unlike the classic workflows with an end step.

# Statement of need

Existing software ecosystems are not tailored for the modeling and simulation of closed-loop control systems developed in multiple programming languages. Containerization with frameworks such as Docker has become popular across the scientific community as containerization enables reproducible science with minimal effort. Workflow frameworks can execute a series of containerized programs without human-in-the-loop, with services/programs as predefined start and end steps. Workflows facilitate modular development as they enable the execution of a series of programs without manually managing each program individually. Typically, these programs are developed and shared across the users as containerized services. Such workflows do not have a cycle, by definition.

On the other hand, a neuromodulation control system comprises feedback loops represented by directed cycles (dicycles). The presence of a dicycle violates the core tenet of classic workflow frameworks, such as Common Workflow Language (CWL) [@amstutz2016common] and Workflow Description Language (WDL) [@miller2006method], which expect the studies to be represented by a directed acyclic graph (DAG) [@gupta2017generation]. Furthermore, control systems run the same program multiple times as part of the execution with feedback. Consequently, overheads imposed by workflow frameworks, significantly when handling implementations across diverse programming languages and execution environments, are magnified in the case of a closed-loop execution.

Interoperability plays a significant role in scientific research. Therefore, we should support the modeling and simulation of studies composed of programs developed in different programming languages, executing on different execution modes (local, distributed, or containerized). _concore_ is designed for efficiency in control systems' specific use cases, supporting interoperable communication and data exchange between programs from independent researchers. The simple file-based communication and synchronization of _concore_, without a centralized workflow orchestrator, enables interoperable executions with high performance.

# Research works enabled by _concore_

The _concore_ protocol has been used to simulate closed-loop control of cardiac physiological models, with various controllers such as Model Predictive Control and Long-Short-Term Memory-based controllers. The scientific contributions of _concore_ protocol and the CONTROL-CORE framework, along with these sample closed-loop neuromodulation control systems use cases, have been extensively discussed in our previous work [@kathiravelu2022control].


# Acknowledgment

This work was supported in part by the National Institutes of Health under Grant OT2OD030535 and Google Summer of Code (GSoC) 2021 and 2022 projects. The authors acknowledge the guidance from Tyler Best and Herbert Sauro. The authors appreciate the assistance that they received from the staff at IT'IS, especially Sylvain Anderegg, Pedro Crespo-Valero, Elisabetta Iavarone, Andrei Neagu, Esra Neufeld, and Katie Zhuang.

# References
