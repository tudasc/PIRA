# PIRA

The Python Instrumentation Refinement Automation (PyIRA) framework approaches the time-consuming task of generating a reasonable performance measurement for an unknown code base.
Currently, the framework assumes a Score-P driven toolchain. However, the goal is to be as flexibel w.r.t. the used toolchain as possible.

## Approach
The framework uses four/five phases to automatically:
* Build the target application and perform baseline measurement.
* Generate an initial performance instrumentation, based on the statement aggregation selection strategy.
* Run the target application to generate a profile.
* Analyze the generated profile to find a new and (hopefully) improved instrumentation.
* Iterate the latter two steps to find a well suited instrumentation.

## Configuration
The framework takesa configuration file in `json` format as input. This file specifies the target codes.
In addition, the configuration holds the paths and names to ~functors~ - Python files that implement a specified set of functions and are loaded at runtime. Within the Python function, the user can implement her own commands to build the target software. Also, the analysis framework to drive the process of finding a suitable instrumentation is loaded using a functor.
In a configuration, the user lists a base directory. This directory, holds, so called, items, which are built in different flavors.
Adding this additional layer of indirection, the user can perform multiple tests on the same target application within a single configuration file - maybe use two different measurement strategies.
