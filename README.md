[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
# PIRA

The Performance Instrumentation Refinement Automation (PIRA) framework approaches the time-consuming task of generating a reasonable performance measurement for an unknown code base when using an instrumentation tool, e.g., Score-P.
For more information please see our papers [1](https://dl.acm.org/citation.cfm?id=3281071) and [2](https://www.researchgate.net/publication/337831656_Automatic_Instrumentation_Refinement_for_Empirical_Performance_Modeling).

## General Approach

PIRA runs the following four phases (2-4 are iterated):

1) Build the target application and perform a baseline measurement.
2) Generate an initial performance instrumentation, based on the statement aggregation selection strategy (cf. [this paper](https://ieeexplore.ieee.org/document/7530067)), and link to the Score-P measurement infrastructure.
3) Run the instrumented target application to generate a profile in the CUBEX format.
4) Analyze the generated profile to find a new and improved instrumentation.

PIRA supports both *compile time* and *runtime* filtering of deselcted functions, including runtime filtering of MPI functions through automatically generated wrappers.
In compile-time filtering, the functions are not instrumented at compile-time, reducing the overall measurement influence significantly, but requiring the target to be built in each iteration.
In contrast, with runtime filtering, the compiler inserts instrumentation hooks in every function of the target application.
Whether a function event should actually be recorded is decided at runtime in the linked measurement library.

## Requirements, obtain PIRA, build it, use it

### Requirements

We require a recent version of CMake (>= 3.5) and test PIRA with a Clang/LLVM source build (release 9.0.1).

### Obtaining PIRA

To obtain PIRA, first, clone the PIRA repository and pull-in its dependencies.

```{.sh}
git clone https://github.com/jplehr/pira
cd pira
./resources/get_externals.sh
```

### Building PIRA

Second, build the dependent submodules using the script we provide.
The two example commands show that you can pass additional flags, e.g., ```--without-mpi``` to the Score-P configure phase, to customize the build for particular needs.

```{.sh}
cd resources
# Example 1: build the dependencies using 8 compile processes, and build Score-P w/o MPI support
./build_submodules.sh 8 --without-mpi
# Example 2: build the dependencies using 24 compile processes, build Score-p w/ MPI support (requires an MPI version to be available)
./build_submodules.sh 24
```

### Using PIRA

To use PIRA, first, set up the required paths, using the script in the `resources` folder.

```{.sh}
cd resources/
. setup_paths.sh
```

Then, you can run an example application of PIRA on a very simple implementation of Conway's Game of Life by using the provided `run.sh` script in the `./test/integration/GameOfLife` folder.

```{.sh}
cd ./test/integration/GameOfLife
./run.sh
```

The scripts performs all steps required from the start, i.e., preparing all components for a new target code, to finally invoke PIRA.
In the subsequent sections, we explain the steps in more detail.
These steps are:

1. Construct a whole-program call graph that contains the required meta information. This needs to be done for a target application whenever the code base changed.
2. Implement the PIRA configuration. For the example, we provide an example configuration.
3. Implement the required PIRA functors. For the example, we provide simple example functors, which may also work for other applications.
4. Invoke PIRA with the respective configuration.

#### Whole Program Call Graph

PIRA uses source code information to construct initial instrumentations and, decide which functions to add to an instrumentation during the iterative refinement.
We provide a Clang-based call-graph tool that collects all required information and outputs the information in a `.json` file.
You can find the `cgcollector` tool in the subdirectory `./extern/src/cgcollector`.

The final graph (currently) needs to be placed into the directory of the **PGIS** that is used for the CG analysis, i.e., copy the generated whole program file into the PGIS directory.
Currently, it is important that the file in the PGIS directory is named following the pattern `flavor-item.ipcg`, more on the terms flavor and item in the next section.

~~~{.sh}
# Assuming $PIRA holds the top-level PIRA directory
cp my-app.ipcg $PIRA/extern/install/pgis/bin/flavor-target.ipcg
~~~

#### Configuration

The PIRA configuration contains all the required information for PIRA to run the automatic process.
The various directories that need to be specified in the configuration can either be *absolute* paths, or *paths, relative to the location of the configuration file*.
The examples are taken from the GameOfLife example in `./test/integration/GameOfLife`.

The user specifies: *the directory* in which to look for subsequently defined *items*, in the example, the directory is `./gol/serial_non_template`.
These directories are given aliases, which are dereferened using the '%' sign.
An item in that regard is a target application, built in a specifically defined way, which is why it is grouped in the configuration under *builds*.

```{.json}
{
    "builds": {
        "%gol": {
            "items": {
                "gol": {
                    ...
                }
            }
        }
    }
    "directories": {
        "gol": "./gol/serial_non_template"
    }
    }
}
```

Every item specifies which *analyzer* should be used.
The default is the analyzer that ships with PIRA, and which can be found in `./extern/src/pgis`.
The particular analyzer is responsible for steering the instruementation refinement, and is, therefore, an essential part of the PIRA framework.

The *argmap* field specifies the different arguments that are passed to the target application when running the performance experiments.
How the arguments are passed to the target application is defined by the different *mappers*.
In the example, a *Linear* mapper is used, which simply iterates the values of the parameter *size* in the order given in the list.

```{.json}
"argmap": {
    "mapper": "Linear",
    "size": [50, 80, 110, 150, 300, 500]
}
```

The *cubes* field is the location where PIRA should store the obtained Score-P profiles.
It will construct a directory tree in that location, so the user can, after PIRA finished, also easily invoke the Extra-P modeling tool by simply passing it the respective location, i.e., */tmp/pira* in the example.

```{.json}
"cubes": "/tmp/pira"
```

The *flavors* field adds another level of possible distinction, as target applications could be built in different *flavors*.
An example would be to specify different math libraries that the target application should link against.

Finally, the *functors* directory points PIRA to the location where it should look for the user-provided Python functions that ultimately tell PIRA how to build, run, and analyze the target application.
In the example, PIRA is pointed to a directory called *functors* relative to the location of the configuration.

```{.json}
"flavors": [
    "ct"
    ],
"functors": "./functors",
"mode": "CT"
```

The *mode* field, currently, is ignored.

#### Implementing Functors

As of now, the user needs to implement five different functors:

* `analyse_<ITEM>_<FLAVOR>.py`: invokes the analyzer.
* `clean_<ITEM>_<FLAVOR>.py`: cleans the build directory.
* `<ITEM>_<FLAVOR>.py`: build the instrumented version.
* `no_instr_<ITEM>_<FLAVOR>.py`: builds the vanilla version.
* `runner_<ITEM>_<FLAVOR>.py`: runs the target application.

Functors, generally, support two modes of invocation: *active* and *passive*.
The functor tells PIRA which mode it uses by setting the respective value to `True` in the dictionary returned by `get_method()`.

In active mode, the functor itself invokes the required commands, for example to build the software.
When invoked, the functor is passed a `**kwargs` parameter holding, for example, the current directory, and an instance of a subprocess shell.

The passive mode solely returns the commands to execute, e.g., the string `make` to invoke a simple Makefile at the item's top-level directory.
The passive mode also is passed a `kwargs` parameter that holds specific information, like pre-defined values needed to add to CXXFLAGS or additional linker flags.
An example of a passive functor may be found in the `examples` and `test` directories.
Currently, all implemented functors use the passive mode.

PIRA passes the required flags for compiling C code in the flags `CC`, which should be used as the compiler, and `CLFLAGS` which lists additional linker flags and library dependencies. For C++, the respective variables are `CXX` and `CXXLFLAGS`.

#### List of Keyword Arguments Passed to Functors

PIRA passes these keyword arguments to all functors.
In addition, different PIRA components may pass additional arguments.

*Important*: This is currently under active development, as we now ship our own Score-P version.
This removes the burden of adjusting compilation flags ourselves.
As a result, some of the additionally passed arguments might go away, or are deprecated.
This can be seen in the `./test/integration/GameOfLife` example functors.

##### All Functors

* ***CC***: C compiler. For example, as used in $(CC) in Makefiles.
* ***CXX***: C++ compiler. For example, as used $(CXX) in Makefiles.
* ***PIRANAME***: The name of the executable that PIRA expects to be generated and callable.

##### Analysis Functor

* ***ANALYZER_DIR***: The directory in which the analysis, i.e., PGIS, is searched for.

##### Build Functor

* ***CLFLAGS***: Additionally needed linker flags for C.
* ***CXXLFLAGS***: Additionally needed linker flags for C++.
* ***filter-file***: The path to the generated white list filter file (to be passed to scorep).

##### Run Functor

* ***util***: Reference to a PIRA *Utility* object.
* ***args***: The arguments passed to the target application as a list, i.e., `[0]` accesses the first argument, `[1]` the second, and so on.
* ***LD_PRELOAD***: The path to the `.so` file implementing the MPI wrapper functions (crucial for MPI filtering).
