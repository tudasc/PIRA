[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
# PIRA

The Performance Instrumentation Refinement Automation (PIRA) framework approaches the time-consuming task of generating a reasonable performance measurement for an unknown code base when using an instrumentation tool, e.g., Score-P.
However, the goal is to be as flexibel w.r.t. the used toolchain as possible.
We have published two papers about the functionality PIRA offers.
The initial paper can be found [here](https://dl.acm.org/citation.cfm?id=3281071) (ACM).
The follow-up paper will be linked as soon as it is available for download.

## Approach

The framework uses four or five phases to automatically:

* Build the target application and perform a baseline measurement.
* Generate an initial performance instrumentation, based on the statement aggregation selection strategy (cf. [this paper](https://ieeexplore.ieee.org/document/7530067)), and link to the Score-P measurement infrastructure.
* Run the target application to generate a profile in the CUBEX format.
* Analyze the generated profile to find a new and improved instrumentation.
* Iterate the latter two steps to find a well-suited instrumentation.

PIRA supports both *compile time* and *runtime* filtering of deselcted functions.
In compile-time filtering, the functions are not instrumented at compile-time, reducing the overall measurement influence significantly, but requiring the target to be built in each iteration.
In contrast, with runtime filtering, the compiler inserts instrumentation hooks in every function of the target application.
Whether a function event should actually be recorded is decided at runtime in the linked measurement library.

## Requirements, obtain PIRA, build it, use it

### Requirements

We require a recent version of CMake (>= 3.5) and test PIRA with a Clang/LLVM source build (release 9.0).

### Obtaining PIRA

To obtain PIRA, first, clone the PIRA repository and pull-in its dependencies
```{.sh}
git clone https://github.com/jplehr/pira
cd pira
git submodule init
git submodule update
```

### Building PIRA

Second, build the dependent submodules using the script we provide.
The example shows that you can pass additional flags, e.g., ```--without-mpi``` to the Score-P configure phase, to customize the build for particular needs.
During the build, also the required dependencies are added to the ```PATH``` variable to be available to PIRA and its components.

```{.sh}
cd resources
# Build the software using 8 compile jobs, and build Score-P w/o MPI support
./build_submodules.sh 8 --without-mpi
```

### Using PIRA

Thereafter, you can invoke PIRA with an example configuration that outputs the different stages and illustrates how it processes a target.

```{.sh}
python3 pira.py example_config.json
```

#### Configuration

PIRA requires the user to provide the configuration as a `json` file.
The file specifies the target codes and the necessary information to build the different flavors.
In addition, the configuration holds the paths and names to *functors*, i.e., Python files that implement a specified set of functions and are loaded at runtime.
In these *functors*, the user provides the recipes how to build the target software.
Also, the analysis framework to drive the process of finding a suitable instrumentation is loaded using a functor.
In a configuration, the user lists a base directory. This directory, holds, so called, items, which are built in different flavors.
Adding this additional layer of indirection, the user can perform multiple tests on the same target application within a single configuration file - maybe use two different measurement strategies.

#### Implementing Functors

Functors, generally, support two modes of invocation: *active* and *passive*.
The functor tells PIRA which mode it uses by setting the respective value to ```True``` in the dictionary returned by ```get_method()```.

In active mode, the functor itself invokes the required commands, for example to build the software.
When invoked, the functor is passed a `**kwargs` parameter holding, for example, the current directory, and an instance of a subprocess shell.

The passive mode solely returns the commands to execute, e.g., the string ```make``` to invoke a simple Makefile at the item's top-level directory.
The passive mode also is passed a `kwargs` parameter that holds specific information, like pre-defined values needed to add to CXXFLAGS or additional linker flags.
An example of a passive functor may be found in the `examples` and `test` directories.
Currently, all implemented functors use the passive mode.

PIRA passes the required flags for compiling C code in the flags `CC`, which should be used as the compiler, and `CLFLAGS` which lists additional linker flags and library dependencies. For C++, the respective variables are `CXX` and `CXXLFLAGS`.

#### List of Keyword Arguments Passed to Functors

PIRA passes these keyword arguments to all functors.
In addition, different PIRA components may pass additional arguments.

##### All Functors

* ***CC***: C compiler. For example, as used in $(CC) in Makefiles.
* ***CXX***: C++ compiler. For example, as used $(CXX) in Makefiles.
* ***PIRANAME***: The name of the executable that PIRA expects to be generated and callable.

##### Analysis Functor

* ***ANALYZER_DIR***: The directory in which the analysis, i.e., PGIS, is searched for.

##### Build Functor

* ***CLFLAGS***: Additionally needed linker flags for C.
* ***CXXLFLAGS***: Additionally needed linker flags for C++.

##### Run Functor

* ***util***: Reference to a PIRA *Utility* object.
