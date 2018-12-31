# PIRA

The Performance Instrumentation Refinement Automation (PIRA) framework approaches the time-consuming task of generating a reasonable performance measurement for an unknown code base.
Currently, the framework assumes a Score-P driven toolchain. 
However, the goal is to be as flexibel w.r.t. the used toolchain as possible.
The full paper can be found [here](https://dl.acm.org/citation.cfm?id=3281071).

## Approach
The framework uses four/five phases to automatically:
* Build the target application and perform a baseline measurement.
* Generate an initial performance instrumentation, based on the statement aggregation selection strategy (cf. [this paper](https://ieeexplore.ieee.org/document/7530067)).
* Run the target application to generate a profile.
* Analyze the generated profile to find a new and improved instrumentation.
* Iterate the latter two steps to find a well suited instrumentation.

## Configuration
PIRA takes a configuration file in `json` format as input. 
This file specifies the target codes.
In addition, the configuration holds the paths and names to *functors*, i.e., Python files that implement a specified set of functions and are loaded at runtime.
In these *functors*, the user provides the recipes how to build the target software.
Also, the analysis framework to drive the process of finding a suitable instrumentation is loaded using a functor.
In a configuration, the user lists a base directory. This directory, holds, so called, items, which are built in different flavors.
Adding this additional layer of indirection, the user can perform multiple tests on the same target application within a single configuration file - maybe use two different measurement strategies.

## Writing a functor
Functors support two modes of invocation: *active* and *passive*.

In the active mode, the functor itself invokes the required commands, for example to build the software.
When invoked, the functor is passed a keyword args parameter holding, for example, the current directory, and an instance of a subprocess shell.

The passive mode solely returns the commands to execute, e.g., the string ```make``` to invoke a simple Makefile at the item's top-level directory.
