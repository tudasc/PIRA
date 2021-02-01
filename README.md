[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

# PIRA

The **P**erformance **I**nstrumentation **R**efinement **A**utomation framework *PIRA* approaches the time-consuming task of generating a reasonable performance measurement for an unknown code base when using Score-P.
For more information please see our papers:

<table style="border:0px">
<tr>
  <td valign="top"><a name="ref-pira-2018"></a>[PI18]</td>
  <td>Jan-Patrick Lehr, Alexander Hück, Christian Bischof. <a href="https://doi.org/10.1145/3281070.3281071">PIRA: performance instrumentation refinement automation</a>. In <i>5th ACM SIGPLAN International Workshop on Artificial Intelligence and Empirical Methods for Software Engineering and Parallel Computing Systems (AI-SEPS)</i>, pages 1-10, ACM, 2018.</td>
</tr>
<tr>
  <td valign="top"><a name="ref-pira-2019"></a>[PI19]</td>
  <td>Jan-Patrick Lehr, Alexandru Calotoiu, Christian Bischof, Felix Wolf. <a href="https://doi.org/10.1109/ProTools49597.2019.00011">Automatic Instrumentation Refinement for Empirical Performance Modeling</a>. In <i>International Workshop on Programming and Performance Visualization Tools (ProTools)</i>, pages 40-47, IEEE, 2019.</td>
</tr>
</table>


## General Approach

PIRA runs the following four phases (2-4 are iterated):

1) Build the target application and perform a baseline measurement.
2) Generate an initial performance instrumentation, based on the statement aggregation selection strategy (cf. [this paper](https://ieeexplore.ieee.org/document/7530067)).
3) Run the instrumented target application to generate a profile in the cubex format.
4) Analyze the generated profile to find a new and improved instrumentation.

PIRA supports both *compile-time* and *run-time* filtering of functions, including runtime filtering of MPI functions through automatically generated wrappers.
In compile-time filtering, only the desired functions are instrumented at compile-time, reducing the overall measurement influence significantly
In contrast, in runtime filtering, the compiler inserts instrumentation hooks into  *every* function of the target application, and the filtering happens at runtime.

## Requirements, obtain PIRA, build it, use it

### Requirements

PIRA requires CMake (>=3.5), Clang/LLVM 10, Python 3, Qt5 and OpenMPI 4.

### Obtaining PIRA

Clone the PIRA repository and initialize the submodules.

```{.sh}
git clone https://github.com/tudasc/pira
cd pira
git submodule update --init
```

### Building PIRA

Second, build the dependent submodules using the script provided.
Specify the number of compile processes to be spawned for the compilation of PIRA's externals.

```{.sh}
cd resources
./build_submodules.sh <ncores>
```

### PIRA Docker

We provide a (early work) `Dockerfile` to build PIRA to try it out.

### Using PIRA

For a full example how to use PIRA, checkout the `run.sh` scripts the `/test/integration` folder.

First, set up the required paths by sourcing the script in the `resources` folder.

```{.sh}
cd resources/
. setup_paths.sh
```

Then, you can run an example application of PIRA on a very simple implementation of Conway's Game of Life by using the provided `run.sh` script in the `./test/integration/GameOfLife` folder.

```{.sh}
cd ./test/integration/GameOfLife
./run.sh
```

The script performs all steps required from the start, i.e., preparing all components for a new target code, to finally invoke PIRA.
In the subsequent sections, the steps are explained in more detail.
The steps are:

1. Construct a whole-program call graph that contains the required meta information. This needs to be done for a target application whenever the code base changed.
2. Implement the PIRA configuration. For the example, the integration tests provide example configurations.
3. Implement the required PIRA functors. For the example, simple example functors are provided, which may also work for other applications.
4. Invoke PIRA with the respective configuration.

#### Arguments for Invoking PIRA

* ```config``` Path to the config-file (required argument)
* ```--config-version [1,2]``` Version of PIRA configuration, 2 is the default and encouraged; 1 is deprecated.
* ```--runtime-filter``` Use run-time filtering, the default is false. In compile-time filtering, the functions are not instrumented at compile-time, reducing the overall measurement influence significantly, but requiring the target to be rebuilt in each iteration.
In contrast, with runtime filtering, the compiler inserts instrumentation hooks in every function of the target application.
* ```--iterations [number] ``` Number of Pira iterations, the default value is 3.
* ```--repetitions [number]``` Number of measurement repetitions, the default value is 3.
* ```--tape``` Location where an (somewhat extensive) logging tape should be written to.
* ```--extrap-dir``` The base directory where the extra-p folder structure is placed.
* ```--extrap-prefix``` Extra-P prefix, should be a sequence of characters.
* ```--version``` Prints the version number of the PIRA installation

#### Highly Experimental Arguments to PIRA

* ```--hybrid-filter-iters [number]``` Re-compile after [number] iterations, in between use runtime filtering.
* ```--export``` Attaches the generated Extra-P models and data set sizes into the target's IPCG file.
* ```--export-runtime-only``` Requires `--export`; Attaches only the median runtime value of all repetitions to the functions. Single data set.
* ```--load-imbalance [path to cfg file]``` Enables and configures load imbalance detection mode. Please read [this section](#load-imbalance-detection) for more information.


#### Whole Program Call Graph

PIRA uses source-code information to construct initial instrumentations and decide which functions to add to an instrumentation during the iterative refinement.
It provides a Clang-based call-graph tool that collects all required information and outputs the information in a `.json` file.
You can find the `cgcollector` tool in the subdirectory `./extern/src/metacg/cgcollector`.

More information on the CGCollector and its components can be found in the [MetaCG](https://github.com/tudasc/MetaCG) documentation.

Applying the CGCollector usually happens in two steps.

1. At first, `cgc` is invoked on every source file in the project. e.g.:

    ~~~{.sh}
    for f in $(find ./src -type f \( -iname  "*.c" -o -iname "*.cpp" \) ); do
        cgc $f
    done
    ~~~
2. The `.ipcg`-files created in step 1 are then merged to a general file using `cgmerge`.
    1. Create an output file, solely containing the string `"null"`
		2. If your project contains more than one `mein` function, please only merge the file with the correct `main` function.
   
    ~~~{.sh}
    echo "null" > $IPCG_FILENAME
    find ./src -name "*.ipcg" -exec cgmerge $IPCG_FILENAME $IPCG_FILENAME {} +
    ~~~

The final graph (currently) needs to be placed into the directory of the **PGIS** that is used for the CG analysis, i.e., copy the generated whole program file into the PGIS directory.
Currently, it is important that the file in the PGIS directory is named following the pattern `item_flavor.ipcg`. An item stands for a target application. More on the terms flavor and item in the next section.

~~~{.sh}
# Assuming $PIRA holds the top-level PIRA directory
cp my-app.ipcg $PIRA/extern/install/pgis/bin/item_flavor.ipcg
~~~

#### Configuration

The PIRA configuration contains all the required information for PIRA to run the automatic process.
The various directories that need to be specified in the configuration can either be *absolute* paths, or *paths, relative to the execution path of pira*. Paths may contain environment variables, e.g., `$HOME`.
The examples are taken from the GameOfLife example in `./test/integration/GameOfLife`.

##### Directory and items

The user specifies: *the directory* in which to look for subsequently defined *items*, in the example, the directory is `./gol/serial_non_template`.
These directories are given aliases, which are dereferenced using the '%' sign.
An item in PIRA is a target application, built in a specific way, which is the reason for it being grouped in the configuration under *builds*.

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

##### Analyzer

Every item specifies which *analyzer* should be used.
The default is the analyzer that ships with PIRA, and which can be found in `./extern/src/metacg/pgis`.
The particular analyzer is responsible for steering the instrumentation refinement, and is, therefore, an essential part of the PIRA framework.

##### Argmap

The *argmap* field specifies the different arguments that are passed to the target application when running the performance experiments.
How the arguments are passed to the target application is defined by different *mappers*.
In the example, a *linear* mapper is used, which simply iterates the values of the parameter named *size* in the order given in the list.

```{.json}
"argmap": {
    "mapper": "Linear",
    "size": [50, 80, 110, 150, 300, 500]
}
```
##### Cubes

The *cubes* field is the location where PIRA should store the obtained Score-P profiles.
It will construct a directory tree in that location, so the user can, after PIRA finished, also easily invoke the Extra-P modeling tool by simply passing it the respective location, i.e., */tmp/pira* in the example.

```{.json}
"cubes": "/tmp/pira"
```
##### Flavors

The *flavors* field adds another level of possible distinction, as target applications can be built in different *flavors*.
An example would be to specify different math libraries that the target application should link against.

##### Functors

Finally, the *functors* directory points PIRA to the location where it looks for the user-provided Python functions that ultimately tell PIRA how to build, run, and analyze the target application.
In the example, PIRA is pointed to a directory called *functors* relative to the location of the configuration.

```{.json}
"flavors": [
    "ct"
    ],
"functors": "./functors",
"mode": "CT"
```
##### Mode

The *mode* field, in this version of PIRA, is ignored.

#### Implementing Functors

As of now, the user needs to implement five different functors:

* `analyze_<ITEM>_<FLAVOR>.py`: invokes the analyzer.
* `clean_<ITEM>_<FLAVOR>.py`: cleans the build directory.
* `<ITEM>_<FLAVOR>.py`: build the instrumented version.
* `no_instr_<ITEM>_<FLAVOR>.py`: builds the vanilla version.
* `runner_<ITEM>_<FLAVOR>.py`: runs the target application.

Functors, generally, support two modes of invocation: *active* and *passive*.
The functor tells PIRA which mode it uses by setting the respective value to `True` in the dictionary returned by `get_method()`.

In active mode, the functor itself invokes the required commands, for example, to build the software.
When invoked, the functor is passed a `**kwargs` parameter holding, for example, the current directory, and an instance of a subprocess shell.

The passive mode solely returns the commands to execute, e.g., the string `make` to invoke a simple Makefile at the item's top-level directory.
It is also passed a `kwargs` parameter that holds specific information, like pre-defined values needed to add to CXXFLAGS or additional linker flags.
An example of a passive functor may be found in the `examples` and `test` directories.
Currently, all implemented functors use the passive mode.

#### List of Keyword Arguments Passed to Functors

PIRA passes the following keyword arguments to all functors.
In addition, different PIRA components may pass additional arguments.

*Important*: We now ship our own Score-P version, thus, it is no longer required to adjust compile commands in PIRA.
As a result, some of the additionally passed functor arguments might go away, or are deprecated.
Check out the functors in `test/integration/AMG2013` for example usages of the different information.

##### All Functors

Currently, no information is passed to all functors

##### Analysis Functor

* ***ANALYZER_DIR***: The directory in which the analysis, i.e., PGIS, is searched for.

##### Build Functor

* ***filter-file***: The path to the generated white list filter file (to be passed to scorep).

##### Run Functor

* ***util***: Reference to a PIRA *Utility* object.
* ***args***: The arguments passed to the target application as a list, i.e., `[0]` accesses the first argument, `[1]` the second, and so on.
* ***LD_PRELOAD***: The path to the `.so` file implementing the MPI wrapper functions (crucial for MPI filtering).

### Load imbalance detection
To enable PIRA's load imbalance detection feature, provide the PIRA invocation with a path to a configuration file using the `--load-imbalance`-parameter. This JSON-file is required to have the following structure:

```{.json}
{
    "metricType": "ImbalancePercentage",
    "imbalanceThreshold": 0.05,
    "relevanceThreshold": 0.05,
    "contextStrategy": "None",
    "contextStepCount": 5,
    "childRelevanceStrategy": "RelativeToMain",
    "childConstantThreshold": 1,
    "childFraction": 0.001
}
```