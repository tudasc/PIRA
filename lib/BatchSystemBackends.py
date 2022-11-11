
import time
import json
from typing import Type, Tuple, Dict, Union, List, Any

import lib.Logging as L
import lib.Utility as U
from lib.BatchSystemGenerator import SlurmGenerator, BatchSystemGenerator
from lib.Configuration import BatchSystemHardwareConfig, SlurmConfig


class BatchSystemBackendType:
  """
  Backends to be used with batch system running.
  Currently, this supports:
  - SLURM: The SLURM workload manager (https://slurm.schedmd.com/overview.html).
  """
  SLURM = "Slurm"


class BatchSystemInterfaceType:
  """
  A base class for different workload managers interfaces.
  More or less only for type-hinting.
  """
  pass


class SlurmInterfaces(BatchSystemInterfaceType):
  """
  Interfaces for the SLURM backend_type.
  Currently, supports:
  - PYSLURM: Interface to SLURM with the pyslurm project: https://github.com/PySlurm/pyslurm.
  - SBATCH_WAIT: Use sbatch with the --wait option.
  - OS: Plain sbatch/squeue checking via the OS with pythons subprocess.
  """
  PYSLURM = "pyslurm"
  SBATCH_WAIT = "sbatch_wait"
  OS = "os"


class BatchSystemTimingType:
  """
  Which way to use to take the timings.
  """
  SUBPROCESS = "subprocess"
  OS_TIME = "os"


class BatchSystemInterface:
  """
  Interface for batch system runs. Derive this, if you are going to write another
  Backend for a workload manager other than SLURM.
  Reference implementation: These functions should be implemented by the concrete
  Backends. Or: The basic implementations of this abstract class can be used for basic
  functionality.

  Along with every of these abstract methods the interface is documented. Each method has either a
  implementation (to also maybe be used by derived classes), or not (e.g. body "pass", or "return None")
  to be implemented by the derived classes. In this case there is documentation in its docstring, which
  will describe how to use these methods, and what is expected to happen when the method is executed.

  The concept of keys:
  For many of the interfaces functions, a key is needed. You may use U.generate_random_string() to generate one.
  A key is used to reference a batch system job. This means, since these keys are used to obtain the results
  for timed commands, only one timed command per job can be added. But this should be enough for PIRA.
  See individual *Backend classes for more detail.
  """
  def __init__(self, backend_type: BatchSystemBackendType = BatchSystemBackendType.SLURM,
               interface_type: BatchSystemInterfaceType = None,
               timings_type: BatchSystemTimingType = None,
               check_interval_in_seconds: int = 30) -> None:
    """
    Constructor.
    """
    self.check_interval = check_interval_in_seconds
    self.backend = backend_type
    self.interface = interface_type
    self.timing_type = timings_type
    self.config = None
    self.generator = None
    self.preparation_commands = {}
    self.timed_commands = {}
    self.teardown_commands = {}
    self.job_id_map = {}
    self.results = {}

  def get_interfaces(self) -> Union[None, Type[BatchSystemInterfaceType]]:
    """
    Returns the interfaces for a specific backend_type. The interfaces are represented as enum classes.
    """
    return None

  def set_interface(self, interface: BatchSystemInterfaceType) -> None:
    """
    Set the interface_type you want to use.
    :param interface: The interface.
    :return: None.
    """
    self.interface = interface

  def configure(self, batch_config: BatchSystemHardwareConfig, batch_generator: BatchSystemGenerator) -> None:
    """
    Set up the configuration for the batch system. This is used to add a batch system configuration
    and a batch system generator to be used, form the outside.
    :param batch_config: The configuration for the batch system.
    :param batch_generator: The generator for the batch system.
    :return: None.
    """
    self.config = batch_config
    self.generator = batch_generator

  def add_preparation_command(self, key: str, cmd: str) -> None:
    """
    Add a command that needs to be executed bevor the timed command,
    but should not be timed itself. E.g. do a cd before executing the actual target.
    :param key: A key (see class docstring).
    :param cmd: The command.
    :return: None.
    """
    # TODO: Add pre- post- hook/functor to use this.
    self.preparation_commands[key] = cmd

  def add_teardown_command(self, key: str, cmd: str) -> None:
    """
    Add a command that needs to be executed bevor the timed command,
    but should not be timed itself. E.g. a cd back after executing the actual target.
    :param key: A key (see class docstring).
    :param cmd: The command.
    :return: None.
    """
    # TODO: Add pre- post- hook/functor to use this.
    self.teardown_commands[key] = cmd

  def add_timed_command(self, key: str, cmd: str):
    """
    Add a command, that needs to be timed. Only one command per key is allowed,
    which means this will overwrite the command, if the key exists in the maps.

    Any implementation is expected to put a key-value pair of the key
    and the command in the self.timed_commands map. It is further expected to
    add a key-value pair of the key and None to self.job_id map (placeholder to
    be filled by the dispatching process). Also, it is expected
    to add key-value pairs of tuple(key, repetition) and None to the self.results map
    (effectively adding placeholders for the results to be filled later).

    :param key: A key (see class docstring).
    :param cmd: The command.
    """
    self.timed_commands[key] = cmd
    self.job_id_map[key] = None
    self.results[(key, None)] = None

  def dispatch(self, key: str) -> Any:
    """
    Start execution(s) by dispatching the job details referenced by the key
    to the batch system. To dispatch a group of jobs, use this method on any key you got.

    Any implementation of this method is expected to dispatch the job details referenced
    by the key to the batch system. This means setting up the needed scripts/commands for
    this batch system (preferably be using the generator class meant for this batch system),
    dispatch it, and keeping the output form the dispatch process. It is further expected to
    set the value (overwrite the None-placeholder) for the key in self.job_id_map to a
    job identifier (e.g. job id), retrieved from the dispatch output.

    :param key: The key to reference the job to be dispatched (see class docstring).
    :return: An identifier for the dispatched job, e.g. a job id.
    """
    pass

  def get_job_id_by_key(self, key: str) -> Any:
    """
    Getter for retrieving a job identifier by a known key.
    :param key: A key (see class docstring).
    :return: None if job referenced by key was not yet dispatched (job
    identifier unknown / the placeholder added by add_timed_command), or
    the job identifier otherwise.
    """

  def wait(self) -> None:
    """
    Wait until the results are ready. Blocks until this is the case.

    Any implementation of this is expected to block until the job(s) are finished.
    This means all jobs that can be identified by key-value entries in the self.job_id_map
    (So only jobs that where dispatched before). This way, you can wait for either single jobs,
    or groups of jobs. Further, it is expected to gather the results and put them into
    the self.results map. The keys are tuples of (key, repetition) each, which means this should
    overwrite the None-placeholders set by the add_timed_command methods.
    This way it can be checked later, if errors occurred somehow, by checking for None in the results.
    Results (the map values) are expected to be added as tuples of (runtime, output).

    :return: None.
    """
    pass

  def get_results(self, key: str, repetition: int) -> Tuple[float, str]:
    """
    Get the results (runtime, output), for a job/key.

    :param key: A key (see class docstring).
    :param repetition: A repetition number to obtain results for.
    :return: Tuple of (runtime[float], output[str]) for this jobs repetition of its command.
    """
    return self.results[(key, repetition)]

  def cleanup(self) -> None:
    """
    Cleanup variables for the next run.
    :return: None.
    """
    self.results = {}
    self.job_id_map = {}
    self.preparation_commands = {}
    self.timed_commands = {}
    self.teardown_commands = {}
    # clean up the runtime files
    U.remove_file_with_pattern(U.get_default_pira_dir(), "pira-slurm-.*")


class SlurmBackend(BatchSystemInterface):
  """
  Backend for the SLURM batch system runner.
  """
  def __init__(self, backend_type: BatchSystemBackendType = BatchSystemBackendType.SLURM,
               interface_type: BatchSystemInterfaceType = SlurmInterfaces.PYSLURM,
               timing_type: BatchSystemTimingType = BatchSystemTimingType.SUBPROCESS) -> None:
    """
    Constructor
    """
    super(SlurmBackend, self).__init__(backend_type, interface_type, timing_type)

  def get_interfaces(self) -> Type[SlurmInterfaces]:
    """
    Getter for the Slurm Backend interfaces
    """
    return SlurmInterfaces

  def set_interface(self, interface: Type[SlurmInterfaces]) -> None:
    """
    Setter for the interface_type
    """
    self.interface = interface

  def configure(self, slurm_config: SlurmConfig, slurm_generator: SlurmGenerator):
    """
    Configures the batch system to use the SLURM options wanted by the user.
    """
    self.config = slurm_config
    self.generator = slurm_generator

  def add_timed_command(self, key: str, cmd: str):
    """
    Add a command, that needs to be timed.
    :param key: A key to reference the command.
    :param cmd: The command.
    """
    for array_id in range(
          self.config.job_array_start,
          self.config.job_array_end+1,
          self.config.job_array_step,
    ):
      # add a placeholder for the results
      self.results[(key, array_id)] = None
    # add a placeholder for the job_id
    self.job_id_map[key] = None
    # add command once
    self.timed_commands[key] = cmd

  def dispatch(self, key: str) -> int:
    """
    Submits the job referenced by key to the cluster via SLURM.
    How this is actually done depends on the interface in use.
    :return: The job_id obtained while dispatching as int.
    """
    self.generator.clear_commands()
    self.generator.clear_modules()
    L.get_logger().log(f"SlurmBackend::dispatch: Dispatching for key {key}", level="debug")
    L.get_logger().log(f"SlurmBackend::dispatch: Interface is: {self.interface}", level="debug")
    # pass commands to the config
    if key in self.preparation_commands:
      self.generator.add_command(self.preparation_commands[key])
    if key not in self.timed_commands:
      L.get_logger().log(f"SlurmBackend::dispatch: There is no command to be added for key {key}.", level="error")
    # add the timing with the command
    if self.timing_type == BatchSystemTimingType.SUBPROCESS:
      cmd = f"python3 {U.get_pira_code_dir()}/lib/BatchSystemTimer.py {key} $SLURM_ARRAY_JOB_ID " \
            f"$SLURM_ARRAY_TASK_ID {U.get_default_pira_dir()} '{self.timed_commands[key]}'"
      self.generator.add_command(cmd)
      L.get_logger().log(f"SlurmBackend::dispatch: Added command '{cmd}'", level="debug")
    elif self.timing_type == BatchSystemTimingType.OS_TIME:
      if self.timed_commands[key].startswith("mpirun"):
        # /usr/bin/time crashed on mpi targets when command is not in quotes
        self.generator.add_command(f"/usr/bin/time --format=%e '{self.timed_commands[key]}'")
      else:
        # but local commands seem to crash with it when in quotes
        self.generator.add_command(f"/usr/bin/time --format=%e {self.timed_commands[key]}")
      L.get_logger().log(f"SlurmBackend::dispatch: Added command '/usr/bin/time --format="
                         f"%e {self.timed_commands[key]}'", level="debug")
    else:
      L.get_logger().log("SlurmBackend::dispatch: Invalid timing_type. Exiting.", level="error")
      U.exit(1)
    if key in self.teardown_commands:
      self.generator.add_command(self.teardown_commands[key])
    # dispatch for different methods
    if self.interface == SlurmInterfaces.PYSLURM:
      try:
        pyslurm = __import__("pyslurm")
      except ModuleNotFoundError:
        L.get_logger().log("PySlurm Module not found. Exiting.", level="error")
        raise RuntimeError("PySlurm Module not found. Exiting.")
      job_controller = pyslurm.job()
      job_opts = self.generator.get_pyslurm_args()
      job_id = job_controller.submit_batch_job(job_opts)
      job_id = int(job_id)
      L.get_logger().log(f"SlurmBackend::dispatch: Dispatched job {job_id} to slurm via PySlurm.", level="debug")
      del job_controller
    elif self.interface == SlurmInterfaces.SBATCH_WAIT:
      L.get_logger().log(f"SlurmBackend::dispatch: Starting execution of repetitions via sbatch --wait...", level="debug")
      job_id = self.generator.sbatch(script_path=self.config.slurm_script_file, active=True, wait=True)
    elif self.interface == SlurmInterfaces.OS:
      # sbatch it
      job_id = self.generator.sbatch(script_path=self.config.slurm_script_file, active=True)
      L.get_logger().log(
        f"SlurmBackend::dispatch: Sbatch'ed jobscript {self.config.slurm_script_file} via systems sbatch.",
        level="debug")
    else:
      L.get_logger().log(f"SlurmBackend::dispatch: Interface is None. Exiting.", level="error")
      raise RuntimeError("SlurmBackend::dispatch: Interface is None. Exiting.")
    # add job id to map for further processing
    self.job_id_map[key] = job_id
    L.get_logger().log(f"SlurmBackend::dispatch: Dispatched batch job {job_id}.", level="info")
    return job_id

  def wait(self) -> None:
    """
    Waits for all dispatched jobs to finish (single job or group). Saves the results.
    """
    # check which jobs we need to wait for
    jobs = []
    for key, job_id in self.job_id_map.items():
      if job_id is not None:
        jobs.append(job_id)
    # waiting for a single job. All methods allowed
    if len(jobs) == 1:
      if self.interface == SlurmInterfaces.PYSLURM:
        try:
          pyslurm = __import__("pyslurm")
        except ModuleNotFoundError:
          L.get_logger().log("PySlurm Module not found. Exiting.", level="error")
          raise RuntimeError("PySlurm Module not found. Exiting.")
        exit_code = pyslurm.job().wait_finished(jobs[0])
      elif self.interface == SlurmInterfaces.SBATCH_WAIT:
        # waiting is done by SLURM, just pass on
        pass
      elif self.interface == SlurmInterfaces.OS:
        # use the generators wait functions
        # give single job along
        self.generator.wait(job_id=jobs[0])
      else:
        L.get_logger().log(f"SlurmBackend::wait: Interface is None. Exiting.", level="error")
        raise RuntimeError("SlurmBackend::wait: Interface is None. Exiting.")
    # waiting for a group of jobs: only "os" method allowed
    else:
      if self.interface == SlurmInterfaces.OS:
        # use the generators wait functions
        # give all jobs along
        self.generator.wait(job_ids=jobs)
      else:
        L.get_logger().log("SlurmBackend::wait: Trying to wait for a group of jobs with method other then 'os'."
                           "Only non-blocking wait methods are allowed for waiting on groups: 'os'.", level="error")
    # After waiting: Read/obtain the results, and populate the result dict with it
    self.populate_result_dict()

  def populate_result_dict(self) -> None:
    """
    Read the output and runtime from the run methods' results.
    :return: None.
    """
    # filter for dispatched (and finished) jobs
    key_job_map = {key: value for key, value in self.job_id_map.items() if value is not None}
    for job_key, job_id in key_job_map.items():
      L.get_logger().log(f"SlurmBackend::populate_result_dict: Obtaining results for job {str(job_id)}, "
                         f"key {job_key}", level="debug")
      L.get_logger().log("SlurmBackend::populate_result_dict: Timing method is: " + str(self.timing_type),
                         level="debug")
      if self.timing_type == BatchSystemTimingType.SUBPROCESS:
        # for all repetitions of the job_key
        for key, repetition in [(k, r) for (k, r) in self.results.keys() if k == job_key]:
          try:
            with open(f"{U.get_default_pira_dir()}/pira-slurm-{job_id}-{key}-{repetition}.json", "r") as f:
              try:
                result_dict = json.load(f)
                self.results[(key, repetition)] = float(result_dict["elapsed"]), result_dict["output"]
              except KeyError:
                L.get_logger().log(f"SlurmBackend::populate_result_dict: Failed to read results for "
                                   f"key {key}, repetition {repetition} from json result file.", level="error")
          except FileNotFoundError:
            L.get_logger().log(f"SlurmBackend::populate_result_dict: Opening runtime json "
                               f"file failed: {U.get_default_pira_dir()}/pira-"
                               f"slurm-{job_id}-{key}-{repetition}.json. Exiting.", level="error")
            raise RuntimeError(f"SlurmBackend::populate_result_dict: Reading runtime from runtime json "
                               f"file failed: {U.get_default_pira_dir()}/pira-"
                               f"slurm-{job_id}-{key}-{repetition}.json. Exiting.")
      elif self.timing_type == BatchSystemTimingType.OS_TIME:
        # for all repetitions of the job_key
        for key, repetition in [(k, r) for (k, r) in self.results.keys() if k == job_key]:
          try:
            with open(f"{self.config.std_err_path}.{job_id}_{repetition}", "r") as f:
              lines = f.readlines()
              try:
                runtime = float(lines[-1].strip())
              except (ValueError, IndexError):
                L.get_logger().log(f"SlurmBackend::populate_result_dict: Reading runtime from out-file "
                                   f"failed: {self.config.std_out_path}.{job_id}_{repetition}. Exiting.", level="error")
                raise RuntimeError(f"SlurmBackend::populate_result_dict: Reading runtime from out-file "
                                   f"failed: {self.config.std_out_path}.{job_id}_{repetition}. Exiting.")
              self.results[(key, repetition)] = runtime, "\n".join(lines[:-1])
          except FileNotFoundError:
            L.get_logger().log(f"SlurmBackend::populate_result_dict: Opening out-file "
                               f"failed: {self.config.std_err_path}.{job_id}_{repetition}. Exiting.", level="error")
            raise RuntimeError(f"SlurmBackend::populate_result_dict: Opening "
                               f"out-file failed: {self.config.std_err_path}.{job_id}_{repetition}. Exiting.")
      else:
        L.get_logger().log(f"SlurmBackend::populate_result_dict: Timing type is None. Exiting.", level="error")
        raise RuntimeError("SlurmBackend::populate_result_dict: Timing type is None. Exiting.")
