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
<tr>
  <td valign="top"><a id="ref-pira-2021"></a>[PI21]</td>
  <td>Peter Arzt, Yannic Fischler, Jan-Patrick Lehr, Christian Bischof. <a href="https://doi.org/10.1007/978-3-030-85665-6_2">Automatic Low-Overhead Load-Imbalance Detection in MPI Applications</a>. In <i>Euro-Par 2021: Parallel Processing. Lecture Notes in Computer Science, vol 12820</i>, pages 19-34, Springer, 2021.</td>
</tr>
</table>


## General Approach

PIRA runs the following four phases (2-4 are iterated):

1) Build the target application and perform a baseline measurement.
2) Generate an initial performance instrumentation, based on the statement aggregation selection strategy (cf. [this paper](https://ieeexplore.ieee.org/document/7530067)).
3) Run the instrumented target application to generate a profile in the cubex format.
4) Analyze the generated profile to find a new and improved instrumentation.

PIRA supports both *compile-time* and *run-time* filtering of functions, including runtime filtering of MPI functions through automatically generated wrappers.
In compile-time filtering, only the desired functions are instrumented at compile-time, reducing the overall measurement influence significantly.
In contrast, in runtime filtering, the compiler inserts instrumentation hooks into  *every* function of the target application, and the filtering happens at runtime.

## Requirements, obtain PIRA, build it, use it

### Requirements

PIRA requires CMake (>=3.16), Clang/LLVM 10, Python 3, Qt5 and OpenMPI 4.
It (or MetaCG) will further download (and build)

- [MetaCG](https://github.com/tudasc/MetaCG)
- [Modified Score-P 6.0](https://github.com/jplehr/score-p-v6)
- [Extra-P (version 3.0)](https://www.scalasca.org/software/extra-p/download.html)
- [LLNL's wrap](https://github.com/LLNL/wrap)
- [bear (version 2.4.2)](https://github.com/rizsotto/Bear)
- [cxxopts (version 2.2.1)](https://github.com/jarro2783/cxxopts)
- [nlohmann json (version 3.10.5)](https://github.com/nlohmann/json)
- [spdlog (version 1.8.2)](https://github.com/gabime/spdlog)

If you want to build PIRA in an environment without internet access, please see the `resources/build_submodules.sh` script, and adjust it to your needs.

### Obtaining PIRA

Clone the PIRA repository.

```{.sh}
$> git clone https://github.com/tudasc/pira
$> cd pira
```

### Building PIRA

Second, build the dependent submodules using the script provided, or pass values for the different options (see usage info via `-h` for options available).
All downloaded and built files will be placed into `external/src/` while all installations will be placed into `external/install/`.
Specify the number of compile processes to be spawned for the compilation of PIRA's externals.
The script will download PIRA's dependencies in their default version.
These versions are also tested in our CI and are expected to work.

```{.sh}
$> cd resources
$> ./build_submodules.sh -p <ncores>
```

As final step, the build script will write the install paths of the submodules into the file `resources/setup_paths.sh`.
Should you wish to rebuild PIRA, please remember to `git restore` this file.

#### PIRA Docker

We also provide an (experimental) `Dockerfile` to build PIRA and try it.

```{.sh}
$> podman build -t pira:master -f docker/Dockerfile .
```

When running inside the container, e.g., the integration tests, please invoke the scripts as follows.

```{.sh}
$> cd resources
$> . setup_paths.sh
$> cd ../test/integration/GameOfLife # Example test case
# By default PIRA will look into $HOME/.local, which is not currently existent in the docker
# XDG_DATA_HOME signals where to put the profiling data PIRA generates
$> XDG_DATA_HOME=/tmp ./run.sh 
```

### Using PIRA

For a full example how to use PIRA, checkout the `run.sh` scripts in the `/test/integration/*` folder.
A potentially good starting point is the `GameOfLife` folder and its test case.

First, set up the required paths by sourcing the script in the `resources` folder.

```{.sh}
$> cd resources/
$> . setup_paths.sh
```

Then, you can run an example application of PIRA on a very simple implementation of Conway's Game of Life by using the provided `run.sh` script in the `./test/integration/GameOfLife` folder.

```{.sh}
$> cd ./test/integration/GameOfLife
$> ./run.sh
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
* ```--tape``` Location where a (somewhat extensive) logging tape should be written to.
* ```--extrap-dir``` The base directory where the Extra-p folder structure is placed.
* ```--extrap-prefix``` Extra-P prefix, should be a sequence of characters.
* ```--version``` Prints the version number of the PIRA installation
* ```--analysis-parameters``` Path to configuration file containing analysis parameters for PGIS. Required for both Extra-P and LIDe mode.
* ```--slurm-config [path to slurm cfg file]``` Enables running the target code on a slurm cluster. A slurm config file is needed. Please see [this section](#run-pira-on-a-slurm-cluster) for more information.

#### Highly Experimental Arguments to PIRA

* ```--hybrid-filter-iters [number]``` Re-compile after [number] iterations, use runtime filtering in between.
* ```--export``` Attaches the generated Extra-P models and data set sizes into the target's IPCG file.
* ```--export-runtime-only``` Requires `--export`; Attaches only the median runtime value of all repetitions to the functions. Only available when not using Extra-P.
* ```--load-imbalance-detection [path to cfg file]``` Enables and configures the load imbalance detection mode. Please read [this section](#load-imbalance-detection) for more information.


#### Whole Program Call Graph

PIRA uses source-code information for constructing an initial instrumentation and deciding which functions to add to an instrumentation during the iterative refinement.
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
		2. If your project contains more than one `main` function, please only merge the file with the correct `main` function.
   
    ~~~{.sh}
    echo "null" > $IPCG_FILENAME
    find ./src -name "*.ipcg" -exec cgmerge $IPCG_FILENAME $IPCG_FILENAME {} +
    ~~~

The final graph needs to be placed into the directory of the callgraph-analyzer. Since **PGIS** is currently used for the CG analysis, the generated whole program file is copied into the PGIS directory.
Currently, it is important that the file in the PGIS directory is named following the pattern `item_flavor.ipcg`. An item stands for a target application. More on the terms flavor and item in the next section.

~~~{.sh}
# Assuming $PIRA holds the top-level PIRA directory
$> cp my-app.ipcg $PIRA/extern/install/pgis/bin/item_flavor.ipcg
~~~

#### Configuration

The PIRA configuration contains all the required information for PIRA to run the automatic process.
The various directories that need to be specified in the configuration-file can either be *absolute* paths, or *paths, relative to the execution path of pira*. Paths may contain environment variables, e.g., `$HOME`.
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
```

##### Analyzer

Every item specifies which *analyzer* should be used.
The **default** analyzer ships with PIRA, and the sources can be found in `./extern/src/metacg/pgis` or the installation in `./extern/install/pgis/bin`, respectively.
The analyzer is responsible for steering the instrumentation refinement, and is, therefore, an essential part of the PIRA framework.

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

Finally, the *functors* directory points PIRA to the location where it looks for the user-provided Python functions that ultimately tells PIRA how to build, run, and analyze the target application.
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
The functor tells PIRA which mode it uses by setting the respective value to `True` in the dictionary returned by the function `get_method()`.

In active mode, the functor itself invokes the required commands, for example, to build the software.
When invoked, the functor is passed a `**kwargs` parameter holding, for example, the current directory and an instance of a subprocess shell.

The passive mode solely returns the commands to execute, e.g. the string `make` to invoke a simple Makefile at the item's top-level directory.
It is also passed a `kwargs` parameter that holds specific information, like pre-defined values needed to add to CXXFLAGS or additional linker flags.
An example of a passive functor may be found in the `examples` and `test` directories.
Currently, all implemented functors use the passive mode.

#### List of Keyword Arguments Passed to Functors

PIRA passes the following keyword arguments to all functors.
In addition, different PIRA components may pass additional arguments.

*Important*: We now ship our own Score-P version. Thus, it is no longer required to adjust compile commands in PIRA.
Check out the functors in `test/integration/AMG2013` for example usages of the different information.

##### All Functors

Currently, no information is passed to all functors

##### Analysis Functor

* ***ANALYZER_DIR***: The directory in which the analyzer i.e. PGIS, is searched for.

##### Build Functor

* ***filter-file***: The path to the generated white list filter file (to be passed to Score-p).

##### Run Functor

* ***util***: Reference to a PIRA *Utility* object.
* ***args***: The arguments passed to the target application as a list, i.e., `[0]` accesses the first argument, `[1]` the second, and so on.
* ***LD_PRELOAD***: The path to the `.so` file implementing the MPI wrapper functions (crucial for MPI filtering).

#### Analyzer parameters
Additional parameters are required for some analysis modes. Specifically, PIRA LIDe (see below) and Extra-P modeling analysis require user provided parameters. Create a JSON file and provide its path to PIRA using the `--analysis-parameters`-switch. The following example contains parameters for the Extra-P modeling mode. The available strategies to aggregate multiple Extra-P models (when a function is called in different contexts) are: `FirstModel`, `Sum`, `Average`, `Maximum`.
```{.json}
{
  "Modeling": {
    "extrapolationThreshold": 2.1,
    "statementThreshold": 200,
    "modelAggregationStrategy": "Sum"
  }
}
```

### Load imbalance detection (PIRA LIDe)
For more details about the load imbalance detection feature, please refer to <a href="#ref-pira-2021">[PI21]</a>. Provide the PIRA invocation with a path to a configuration file using the `--load-imbalance-detection`-parameter. This JSON-file is required to have the following structure:

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
* ***metricType***: Metric which is used to quantify load imbalance in function runtimes. If unsure, use *Imbalance Percentage*. (Other experimental options: *Efficiency*, *VariationCoeff*)
* ***imbalanceThreshold***: Minimum metric value to be rated as imbalanced. For *Imbalance Percentage*, 5% can be used a starting value.
* ***relevanceThreshold***: Minimum runtime fraction a function is required to surpass in order to be rated as relevant.
* ***contextStrategy***: Optional context handling strategy to expand instrumentation with further functions. Use *MajorPathsToMain* for profile creation and *FindSynchronizationPoints* for tracing experiments. Use *None* to disable context handling. (Other experimental option: *MajorParentSteps* with its suboption *contextStepCount*)
* ***childRelevanceStrategy***: Strategy to calculate statement threshold for the iterative descent. If unsure, use *RelativeToMain* which will calculate the threshold as max(*childConstantThreshold*, *childFraction* * (main's inclusive statement count))

### Run PIRA on a SLURM cluster

To run PIRA on a cluster with the SLURM workload manager, invoke it with the `--slurm-config` flag. Give the path to your batch system configuration file with it. See the integration tests suffixed with `_Slurm` (`test/integration/*_Slurm/`). PIRA currently supports batch systems with the [SLURM workload manager](https://slurm.schedmd.com/overview.html). PIRA supports the use of a `module`-system, which may be found on slurm clusters.

The batch system configuration file is a JSON-file, which is structured as follows:

```{.json}
{
  "general": {
    "backend": "slurm",
    "interface": "pyslurm",
    "timings": "subprocess"
  },
  "module-loads": [
    {
      "name": "gcc",
      "version": "8.5"
    },
    {
      "name": "llvm",
      "version": "10.0.0",
      "depends-on": [
        {
          "name": "gcc",
          "version": "8.5"
        }
      ]
    }
  ],
  "batch-settings": {
    "time_str": "00:10:00",
    "mem_per_cpu": 3800,
    "number_of_tasks": 1,
    "partition": null,
    "reservation": null,
    "account": "your_account_here",
    "cpus_per_task": 96
  }
}
```

Breakdown:

- `general` section: Lets you choose in which way PIRA will execute your code on the batch system. Since every option in this section is optional, you can omit the whole section, if you are fine with using the defaults:
    + `backend`: What workload manager to use. Choices: `slurm`, for the slurm workload manager. Default: `slurm`, therefor optional.
    + `interface`: In which way PIRA should interact with your batch system manager. For the SLURM backend, these are: `pyslurm`, to use [PySlurm](https://github.com/pyslurm/pyslurm) (this requires PySlurm to be installed, see [this section](#notes-on-installing-pyslurm); `sbatch-wait`, to use standard `sbatch` with the `--wait` flag; `os`, for standard `sbatch` and `squeue` interaction calls. Default: `pyslurm`, therefor optional.
    + `timings`: How timing of the target code should be done. Choices: `subprocess`, for timing with a python wrapper and `os.times` in a subprocess (exactly like PIRA does it if ran local); `os`, to use `/usr/bin/time`. Default: `subprocess`, therefor optional.
    + `force-sequential`: Default `false`. Set to `true` to force PIRA/your batch system to do all runs in sequential order (only one execution of the target code at a time). This means PIRA will take care that your batch system runs repetitions, as well as different jobs in scaling experiments in sequential order. If set to/left on `false` PIRA will try to instruct the batch system to do as many executions as possible within every iteration in parallel. 
- `module-loads` section: *Currently not in use in PIRA, work in progress! Currently, you need to load all modules manually, before starting PIRA!* Meant for which modules should be loaded with the `module` system. This requires one to be in place (commands `module load` and `module purge` may be used by PIRA). If you do not have a `module` system in place, or do not want to use it, either omit this section completely, or set `"module-loads": null`. To specify modules PIRA should load, specify a list of modules, as in the example above. 
    + Each module have to have a `name`. 
    + The `version` is optional, if not given, it will depend on what the `module` system loads as default module version. It is recommended to always give versions explicitly.
    + `depends-on` is also optional. Give a list of modules on which this module depends. These modules have to have a `name` and can optional have a `version` given. The dependencies defined here are used by PIRA to determine the order in which modules should be loaded
        - If you do not give a version, it will only check that *some* version of this module was loaded. It is recommended to always give versions explicitly.
        - If you do not specify this, or set it to `null`, it is assumed, this module has no dependencies. 
        - Be aware that PIRA will crash with a corresponding error, if you define dependency cycles here. 
        - Note that you can care about dependency management on your own: If not given any `depends-on` PIRA will (try to) load the modules in exactly that order that was given in the config file. 
- `batch-setting` section: The actual hardware and job options for the batch system. Some options in the section are mandatory, you cannot omit this section.
    + `time`: The `sbatch --time` option, mandatory. 
    + `mem-per-cpu`: The `sbatch --mem-per-cpu` option, mandatory.
    + `ntasks`: The `sbatch --ntasks` option, mandatory.
    + You can optionally further specify the following options: `partition`, `reservation`, `account` (all default to `null`=not given), `cpus-per-task` (defaults to `4`), `exclusive` (defaults to `true`; not supported with `pyslurm`), and `cpu-freq` (defaults to `null`).
    + Note that there are some `sbatch` options you cannot define in this config. This is due to some options used by PIRA internally, for example the `--array` option, to map the repetitions to job arrays.
	
#### Notes on installing PySlurm

How and which version of PySlurm to install on your cluster, highly depends on your SLURM version, and your SLURM installation. The installation and packaging solution for pyslurm with PIRA is work in progress. Refer to their [README](https://github.com/PySlurm/pyslurm#readme). You might try some of the following:

- If your SLURM version is XX.YY.\*, you want to look for a release/brach of pyslurm with the version XX.YY.\* (Note that \* does not have to be identical).
- Determine where SLURM is set up, look for a `include` and a `lib` dir. 
- Build pyslurm with these options, e.g. `python3 setup.py build --slurm-lib=/opt/slurm/21.08.6/lib --slurm-inc=/opt/slurm/21.08.6/include`
- Install it: `python3 setup.py install --slurm-lib=/opt/slurm/21.08.6/lib --slurm-inc=/opt/slurm/21.08.6/include`.
