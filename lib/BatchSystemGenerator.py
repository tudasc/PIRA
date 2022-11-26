"""
File: BatchSystemGenerator.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description:
"""

import math
import os
import subprocess
import time
from typing import Optional, List, Union, Dict

import lib.Logging as L
import lib.Utility as U
from lib.Exception import PiraException
from lib.Configuration import BatchSystemHardwareConfig, SlurmConfig


# Exceptions:
class SlurmBaseException(PiraException):
  """
  Base exception for SLURM errors.
  """

  def __init__(self, message):
    super().__init__(message)

  def __str__(self):
    return self._message


class ModuleDependencyConflict(SlurmBaseException):
  """
  Exception for module system modules, if there are dependency conflicts.
  """

  def __init__(self, message):
    super().__init__(message)


class ScriptNotFoundException(SlurmBaseException):
  """
  Exception for failed referencing scripts on disk.
  """

  def __init__(self, message):
    super().__init__(message)


class CommandExecutionException(SlurmBaseException):
  """
  Exception for execution of commands.
  """

  def __init__(self, command, invalid=False, non_zero=True):
    if invalid:
      super().__init__(f"Error while command execution of '{command}': Command not found.")
    elif non_zero:
      super().__init__(
          f"Error while command execution of '{command}': Returned non-zero exit code.")


# Helper enum class
class MailType:
  """
  Enum for SLURM Mail types (--mail-type setting).
  """
  BEGIN = "BEGIN"
  END = "END"
  FAIL = "FAIL"
  ALL = "ALL"
  NONE = "NONE"


# Helper classes
class _Module:
  """
  Helper class for module system modules.
  """

  def __init__(self,
               name: str,
               version: Optional[str] = None,
               depends_on: Optional[List[str]] = None) -> None:
    """
    Constructor.
    :param name: The modules name.
    :param version: The modules version.
    :param depends_on: List of module names the modules depends on. These will be loaded bevor this module.
    """
    self.name = name
    self.version = version
    self.depends_on = depends_on

  def check_dependency_conflicts(self, other_modules) -> None:
    """
    Checks if there are circular conflicts in dependencies. It only checks on circular imports of two modules.
    :param other_modules: List of other modules to check with.
    :return: void, raises ModuleDependencyConflict exception if a conflict was detected.
    """
    if self.depends_on:
      for dependency in self.depends_on:
        for compare_module in other_modules:
          # if compare module in general is a dependency, or the compare module in its version.
          if compare_module.name == dependency or \
               (compare_module.version is not None and compare_module.name + "/" + compare_module.version == dependency):
            if compare_module.depends_on:
              # if either general module or module with version depends back on this module
              if self.name in compare_module.depends_on or \
                   (self.version is not None and self.name + "/" + self.version in compare_module.depends_on):
                L.get_logger().log(
                    f"_Module::check_dependency_conflicts: Dependency conflict: Module {self.name} "
                    f"depends on {dependency}, but {compare_module.name} "
                    f"depends on {self.name}.",
                    level="error")
                raise ModuleDependencyConflict(
                    f"Dependency conflict: Module {self.name} depends on "
                    f"{dependency}, but {compare_module.name} "
                    f"depends on {self.name}.")

  def deps_satisfied_with(self, others) -> bool:
    """
    Return if these modules dependencies are satisfied with the given list of other ones.
    :param others: List of modules to compare to.
    """
    # If this module has no dependencies it is satisfied with any other list of modules
    if not self.depends_on:
      return True
    all_fulfilled = True
    for dependency in self.depends_on:
      this_fulfilled = False
      for other in others:
        if "/" in dependency:
          if other.version and dependency == f"{other.name}/{other.version}":
            this_fulfilled = True
        else:
          if dependency == other.name:
            this_fulfilled = True
      if not this_fulfilled:
        all_fulfilled = False
    return all_fulfilled

  def __str__(self):
    """
    Return the module as string.
    That is either <name>, or if version given <name/version>.
    """
    if self.version is not None:
      return f"{self.name}/{self.version}"
    else:
      return self.name


class BatchSystemGenerator:
  """
  Base class for generators for batch system configs.
  This is meant to be the base class for all workload managers to derive from.
  A generator will take in the configuration for the batch system, and prepare
  everything according to the workload managers specifications to dispatch a job to it.
  E.g. for the SLURM workload manager there is the SlurmGenerator class, which will care
  about generating arguments, options and scripts to be used with the slurm workload manager.
  """

  def __init__(self, config: BatchSystemHardwareConfig) -> None:
    """
    Constructor.
    :param config: The batch system config.
    """
    self.config = config


class SlurmGenerator(BatchSystemGenerator):
  """
  Generates options, arguments and scripts for the SLURM workload manager. It mainly offers:
  - Generating sbatch options for the command line in various formats.
  - Generating a sbatch alike option dict to be used with pyslurm
  - Generating and saving a slurm script to disk.
  - Passively generating and returning, or actively sbatch-ing the options to the machine.
  - to do the same with the srun command for interactive jobs.
  - Checking with squeue if your job is finished.
  - Support of a module system, with module dependencies and sorting.
  - Convenience options like checking the output directories exist.
  """

  def __init__(self, slurm_config: SlurmConfig) -> None:
    """
    Constructor.
    """
    super().__init__(slurm_config)
    self.job_id = None
    self.modules = []
    self.commands = []
    self.slurm_options = None

  def add_module(self,
                 name: str,
                 version: str = None,
                 depends_on: Optional[List[str]] = None) -> None:
    """
    Adds a module to be loaded from the module system. If this module (same name) was already added, this will
    only override the version, or do nothing.
    This is just like adding a commands "module load <name>",
    just for more convince on systems with a module system in place.
    :param name: The name of the module to load.
    :param version: The version of the module. If not give it will be loaded without a specific version,
    therefore it will be the default version of the module system.
    :param depends_on: List of module names the modules depends on. These will be loaded bevor this module.
    :return: void.
    """
    module = _Module(name, version, depends_on)
    try:
      module.check_dependency_conflicts(self.modules)
    except ModuleDependencyConflict as e:
      print(e)
      raise RuntimeError(e)
    self.modules.append(module)

  def add_modules(self) -> None:
    """
    Wrapper for add_module. Will call add_module for
    every module that comes with the SlurmConfiguration.
    """
    for mod in self.config.modules:
      depends_on = None
      if "depends_on" in mod and mod["depends_on"] is not None:
        depends_on = []
        for dep in mod["depends_on"]:
          d = dep["name"]
          if "version" in dep:
            d = f"{d}/{dep['version']}"
          depends_on.append(d)
      if "version" in mod:
        self.add_module(mod["name"], mod["version"], depends_on)
      else:
        self.add_module(mod["name"], depends_on=depends_on)

  def load_modules(self):
    """
    Actively load all modules on the machine. Uses add_modules to
    initialize the modules. This is meant for use in cases where you cannot
    load the modules toghter with the method you use to interface to slurm.
    E.g. with pyslurm, you have to load modules separately, but in a slurm script
    you can put the module loads in there.
    """
    self.add_modules()
    self.__sort_module_loads()
    if self.config.purge_modules_at_start:
      U.shell("module purge")
    for mod in self.modules:
      U.shell(f"module load {str(mod)}")

  def clear_modules(self):
    """
    Clears the modules.
    """
    self.modules = []

  def add_command(self, command: str) -> None:
    """
    Adds a commands to run from inside the sbatch job. These are the actual run commands,
    not the SLURM config comments.
    :param command: The command to add.
    :return: void.
    """
    self.commands.append(command)

  def clear_commands(self) -> None:
    """
    Clears commands.
    :return: void.
    """
    self.commands.clear()

  def __sort_module_loads(self) -> None:
    """
    Sorts the module loads, by dependencies.

    A simple/'stupid' implementation. It just tries to sort the modules correctly, and gives up
    if no correct way can be found after n! tries (all permutations theoretically). No fancy
    cyclic graph detection or similar. It at least should be enough for the most simple cases
    (such as tested in the unit tests).

    :return: void.
    """
    modules_sorted = []
    modules_with_deps = []
    # move modules without dependencies to the front
    for module in self.modules:
      if module.depends_on is None:
        modules_sorted.append(module)
      else:
        modules_with_deps.append(module)
    modules_with_deps = sorted(modules_with_deps, key=lambda mod: len(mod.depends_on))
    max_tries = math.factorial(len(modules_with_deps))
    tries = 0
    while len(modules_with_deps) > 0:
      module = modules_with_deps.pop(0)
      if module.deps_satisfied_with(modules_sorted):
        modules_sorted.append(module)
      else:
        modules_with_deps.append(module)
        tries = tries + 1
      if tries > max_tries:
        conflicts_on = [
            f"{mod.name} (depends on {mod.depends_on})"
            if mod.version is None else f"{mod.name}/{mod.version} (depends on {mod.depends_on})"
            for mod in modules_with_deps
        ]
        # delete duplicates
        conflicts_on = list(set(conflicts_on))
        # raise error
        L.get_logger().log(
            f"SlurmGenerator::__sort_module_loads: Modules could not be sorted in a way they do not "
            f"conflict each other or some module dependencies cannot be fulfilled. "
            f"Modules that cannot be sorted in are: {conflicts_on}.",
            level="error")
        raise ModuleDependencyConflict(
            f"Modules could not be sorted in a way they do not conflict each other "
            f"or some module dependencies cannot be fulfilled. "
            f"Modules that cannot be sorted in are: {conflicts_on}.")
    self.modules = modules_sorted

  def to_slurm_options(self) -> None:
    """
    Save the contents of the config of the slurm args in key-value format.
    This resembles the sbatch options corresponding to the config.
    """
    self.slurm_options = {}
    if self.config.account:
      self.slurm_options["--account"] = self.config.account
    if self.config.reservation:
      self.slurm_options["--reservation"] = self.config.reservation
    if self.config.partition:
      self.slurm_options["--partition"] = self.config.partition
    if self.config.job_name:
      self.slurm_options["--job-name"] = self.config.job_name
    if self.config.std_out_path:
      if self.config.job_array_start is not None and self.config.job_array_end is not None:
        self.slurm_options["--output"] = f"{self.config.std_out_path}.%A_%a"
      else:
        self.slurm_options["--output"] = f"{self.config.std_out_path}.%j"
    if self.config.std_err_path:
      if self.config.job_array_start is not None and self.config.job_array_end is not None:
        self.slurm_options["--error"] = f"{self.config.std_err_path}.%A_%a"
      else:
        self.slurm_options["--error"] = f"{self.config.std_err_path}.%j"
    if self.config.time_str:
      self.slurm_options["--time"] = self.config.time_str
    if self.config.mem_per_cpu:
      self.slurm_options["--mem-per-cpu"] = self.config.mem_per_cpu
    if self.config.number_of_tasks:
      self.slurm_options["--ntasks"] = self.config.number_of_tasks
    if self.config.number_of_cores_per_task:
      self.slurm_options["--cpus-per-task"] = self.config.number_of_cores_per_task
    if self.config.exclusive:
      self.slurm_options["--exclusive"] = None
    if self.config.wait:
      self.slurm_options["--wait"] = None
    if self.config.job_array_start is not None and self.config.job_array_end is not None:
      self.slurm_options["--array"] = f"{self.config.job_array_start}-" \
                                      f"{self.config.job_array_end}:{self.config.job_array_step}"
      if self.config.force_sequential:
        # "%1" means maximal 1 job in parallel
        self.slurm_options["--array"] += "%1"
    if self.config.cpu_frequency_str:
      self.slurm_options["--cpu-freq"] = self.config.cpu_frequency_str
    if self.config.dependencies:
      self.slurm_options["--dependency"] = self.config.dependencies
    if self.config.mail_address:
      self.slurm_options["--mail-user"] = self.config.mail_address
    if self.config.mail_types:
      self.slurm_options["--mail-type"] = ",".join(self.config.mail_types)

  def to_arg_strings(self) -> List[str]:
    """
    Generate SLURM flags from key-value config.
    """
    self.to_slurm_options()
    args = []
    for flag, value in self.slurm_options.items():
      if value:
        args.append(f"{flag}={value}")
      else:
        # if value is None, it is a flag, without a variable to it
        # essentially for the exclusive flag
        args.append(f"{flag}")
    return args

  def get_pyslurm_args(self) -> Dict[str, Union[str, int]]:
    """
    Returns the slurm arguments as dict for pyslurm.
    To dispatch jobs with pyslurm, there is a need to re-format some data.
    (It would be best, if the method is not necessary, but at the moment it is)

    Changes needed for pyslurm:
    (0. All the leading "--" need to be removed)
    1. There is no "--time" for pyslurm. Instead, you can set "time_limit": <minutes as int>.
    2. There is no "--array" for pyslurm. Instead, you specify "array_inx": "0,1,2" (a comma separated
    list of task/array ids as a string - e.g. this is the same as "--array=0-2[:1]").
    3. "job-name" needs to be "job_name".
    4. "mem-per-cpu" needs to be "mem_per_cpu".
    5. "cpus-per-task" needs to be "cpus_per_task".
    6. "cpu-freq" needs to be split into min and max, named "cpu_freq_min" and "cpu_freq_max".
    7. List of options, that are not supported by pyslurm. For now, we need to exclude them, because
    otherwise the dispatching will fail: "wait", "exclusive"
    8. Last but not least, put in the commands as "wrap".
    """
    res = {}
    self.to_slurm_options()
    for flag, value in self.slurm_options.items():
      flag = flag[2:]  # fixes 1.
      if flag == "time":
        s = value
        had_days = False
        # calculate number of minutes from time_str
        minutes = 0
        # See: https://slurm.schedmd.com/sbatch.html: "Acceptable time formats include "minutes",
        # "minutes:seconds", "hours:minutes:seconds", "days-hours", "days-hours:minutes"
        # and "days-hours:minutes:seconds"."
        if "-" in s:
          had_days = True
          # days in format
          days, s = s.split("-", 1)
          minutes = minutes + (int(days) * 60 * 24)
        if s.count(":") == 2:
          # hh:mm:ss layout
          hours, mins, secs = s.split(":")
          # add a minute if it had seconds not 0 ("ceil")
          mins = int(mins) + 1 if int(secs) > 0 else int(mins)
          minutes = minutes + (int(hours) * 60 + mins)
        elif s.count(":") == 1:
          # mm:ss layout - or hh:mm if it had days in it
          if had_days:
            hours, mins = s.split(":")
            minutes = minutes + (int(hours) * 60 + int(mins))
          else:
            mins, secs = s.split(":")
            mins = int(mins) + 1 if int(secs) > 0 else int(mins)
            minutes = minutes + mins
        elif s.count(":") == 0:
          # just minutes - or hours if it had days in it
          if had_days:
            minutes = minutes + (60 * int(s))
          else:
            minutes = minutes + int(s)
        res["time_limit"] = minutes
      elif flag == "array":
        rest = value
        if "%" in value:
          # TODO max_parr jobs not supported by pyslurm
          L.get_logger().log(
              "SlurmGenerator::get_pyslurm_args: 'force-sequential' cannot be enforced "
              "with interface 'pyslurm' for repetitions. They may run in parallel.",
              level="warn")
          value = value.split("%")[0]
        step = 1
        if ":" in value:
          rest, step = value.split(":")
        begin, end = rest.split("-")
        ids = []
        for i in range(int(begin), int(end) + 1, int(step)):
          ids.append(str(i))
        res["array_inx"] = ",".join(ids)
      elif flag == "job-name":
        res["job_name"] = value
      elif flag == "cpu-freq":
        freq_min, freq_max = value.split("-")
        res["cpu_freq_min"] = freq_min
        res["cpu_freq_max"] = freq_max
      elif flag == "mem-per-cpu":
        res["mem_per_cpu"] = value
      elif flag == "cpus-per-task":
        res["cpus_per_task"] = value
      # TODO: wait is not supported by pyslurm
      elif flag == "wait":
        L.get_logger().log(
            "SlurmGenerator::get_pyslurm_args: You try to use SLURMs 'wait' option "
            "with interface 'pyslurm', which is not supported by pyslurm.",
            level="warn")
        continue
      # TODO: exclusive is not supported by pyslurm
      elif flag == "exclusive":
        L.get_logger().log(
            "SlurmGenerator::get_pyslurm_args: You try to use SLURMs 'exclusive' option "
            "with interface 'pyslurm', which is not supported by pyslurm.",
            level="warn")
        continue
      else:
        # put everything else in as is
        res[flag] = value
    # put in the command(s)
    res["wrap"] = ";".join(self.commands)
    return res

  def get_slurm_cmd_line_args(self) -> str:
    """
    Return the plain command line slurm arguments.
    """
    self.to_slurm_options()
    return " ".join(self.to_arg_strings())

  def write_slurm_script(self, script_path: str, load_modules=False) -> None:
    """
    Generates a slurm script and writs it to disk.
    """
    # sort modules
    try:
      self.__sort_module_loads()
    except ModuleDependencyConflict as e:
      print(e)
      raise RuntimeError(f"Conflict while module sorting: {e}")
    # slurm script
    try:
      with open(script_path, "w") as f:
        # write slurm options
        f.write(f"#!{self.config.shell}\n")
        for slurm_opt in self.to_arg_strings():
          f.write(f"#SBATCH {slurm_opt}\n")
        if load_modules:
          # write module loads
          if self.config.uses_module_system:
            if self.config.purge_modules_at_start:
              f.write("module purge\n")
            for module in self.modules:
              if module.version:
                f.write(f"module load {module.name}/{module.version}\n")
              else:
                f.write(f"module load {module.name}\n")
        # write commands
        for command in self.commands:
          f.write(f"{command}\n")
    except FileNotFoundError as e:
      L.get_logger().log(f"Slurm script file cannot be found or created: {e}", level="error")
      raise ScriptNotFoundException(f"Slurm script file cannot be found or created: {e}.")

  def make_dirs(self):  # TODO: No usages anymore!
    """
    Checks if directories to out- and err directory are in place.
    Create the necessary directories that are missing.
    """
    err_dir = "/".join(self.config.std_err_path.split("/")[:-1])
    out_dir = "/".join(self.config.std_out_path.split("/")[:-1])
    if not os.path.isdir(err_dir):
      res = subprocess.run(["mkdir", "-p", err_dir])
      if not res.returncode == 0:
        raise CommandExecutionException(f"mkdir -p {err_dir}")
    if not os.path.isdir(out_dir):
      res = subprocess.run(["mkdir", "-p", out_dir])
      if not res.returncode == 0:
        L.get_logger().log(
            f"SlurmGenerator::make_dirs: Creation of directories with mkdir -p {out_dir} "
            f"failed",
            level="warn")
        raise CommandExecutionException(f"mkdir -p {out_dir}")

  def sbatch(self,
             script_path: Optional[str] = None,
             active: bool = False,
             wait: bool = False,
             load_modules: bool = False) -> Union[int, str]:
    """
    Saves the SLURM script to the file and submits the job on the system via "sbatch"-commands.
    :param script_path: Path for the slurm script. If given a slurm script will be saved and sbatched,
    if not given all options will be appended to the sbatch command directly.
    :param active: Set to False to not run the command, just return it.
    :param wait: Use the wait flag to sbatch the job.
    :param load_modules: Whether to use module system in script or not.
    :return: The job id resulted from sbatch-ing. Or if not active: The sbatch command.
    """
    self.to_slurm_options()
    if wait:
      self.config.wait = wait
      self.to_slurm_options()
    sbatch_command = ["sbatch"]
    if not script_path:
      # slurm options
      for flag, value in self.slurm_options.items():
        if value:
          sbatch_command.append(f"{flag}={value}")
        else:
          sbatch_command.append(f"{flag}")
      if load_modules:
        if self.config.uses_module_system:
          # module purge
          if self.config.purge_modules_at_start:
            sbatch_command.append("module purge;")
          # module loads
          self.__sort_module_loads()
          for module in self.modules:
            sbatch_command.append(f"module load {str(module)};")
      # commands
      sbatch_command.append(";".join(self.commands))
    else:
      self.write_slurm_script(script_path, load_modules)
      sbatch_command.append(script_path)
    if not active:
      return " ".join(sbatch_command)
    else:
      res, rt = U.shell(" ".join(sbatch_command))
      res = res.split("\n")[0]
      res = res.split("Submitted batch job ")[1]
      self.job_id = int(res)
      L.get_logger().log(f"SlurmGenerator::sbatch: Submitted batch job {self.job_id}",
                         level="debug")
      return self.job_id

  def __check_squeue(self, job_ids: List[int] = None) -> bool:
    """
    Checks the output of the "squeue" commands and returns whether all jobs in the job_ids are completed or not.
    You can give just a list of one, to check for one.
    :param job_ids: A list of job ids to find the status for.
    :return: True if the job is/jobs are completed, false otherwise. If an empty list was given, None will be returned.
    """
    sq = subprocess.run(["bash", "-c", "squeue --format=%F --noheader"], stdout=subprocess.PIPE)
    sq = sq.stdout.decode("utf-8")
    squeue_ids = sq.splitlines(keepends=False)
    map = {}
    finished = None
    if job_ids:
      finished = True
      for i, job_id in enumerate(job_ids):
        map[job_id] = True
        for squeue_job in squeue_ids:
          # need to test if id is part of squeue output to make it work with job arrays
          if str(job_id) in squeue_job:
            finished = False
            map[job_id] = False
      # print a usefull summary
      log = "State summary:\n"
      for i, (job, fin) in enumerate(map.items()):
        endwith = '' if i == len(list(map.keys())) - 1 else '\n'
        log = log + f"Job {job} is{'' if fin else ' not yet'} finished.{endwith}"
      L.get_logger().log(f"SlurmGenerator::__check_squeue: {log}", level="debug")
      del map, log
    return finished

  def wait(self, job_id: int = None, job_ids: List[int] = None) -> None:
    """
    Wait for the SLURM job given by job_id, or for the list of SLURM jobs given by job_ids to finish.
    :param job_id: Job id for waiting for a single job.
    :param job_ids: List of job ids for waiting for multiple jobs.
    :return: void.
    """
    check_for = []
    if job_id:
      self.job_id = job_id
      check_for.append(job_id)
    elif job_ids:
      check_for += job_ids
    while not self.__check_squeue(check_for):
      time.sleep(self.config.check_interval)
