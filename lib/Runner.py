"""
File: Runner.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to run the target software.
"""

import sys
sys.path.append('..')

import lib.Utility as U
import lib.Logging as L
import lib.FunctorManagement as F
import lib.Measurement as M
import lib.DefaultFlags as D
import lib.ProfileSink as S
from lib.Configuration import PiraConfig, TargetConfig, InstrumentConfig, InvocationConfig
from lib.BatchSystemBackends import BatchSystemInterface, SlurmBackend, SlurmInterfaces
from lib.BatchSystemGenerator import SlurmGenerator
from lib.Configuration import SlurmConfig
from lib.Measurement import RunResultSeries

import typing


class Runner:
  def __init__(self, configuration: PiraConfig, sink):
    """ Runner are initialized once with a PiraConfiguration """
    self._config = configuration
    self._sink = sink

  def has_sink(self) -> bool:
    if self._sink is None:
      return False
    if isinstance(self._sink, S.NopSink):
      return False

    return True

  def get_sink(self):
    return self._sink


class LocalBaseRunner(Runner):
  """
  The base class for execution on the same machine. It implements the basic *run* method, which invokes the target.
  """

  def __init__(self, configuration: PiraConfig, sink):
    """ Runner are initialized once with a PiraConfiguration """
    super().__init__(configuration, sink)

  def run(self, target_config: TargetConfig, instrument_config: InstrumentConfig, ) -> float:
    """ Implements the actual invocation """
    functor_manager = F.FunctorManager()
    run_functor = functor_manager.get_or_load_functor(target_config.get_build(), target_config.get_target(),
                                                      target_config.get_flavor(), 'run')
    default_provider = D.BackendDefaults()
    kwargs = default_provider.get_default_kwargs()
    kwargs['util'] = U
    kwargs['LD_PRELOAD'] = default_provider.get_MPI_wrap_LD_PRELOAD()
    runtime = .0

    if run_functor.get_method()['active']:
      run_functor.active(target_config.get_target(), **kwargs)
      L.get_logger().log('For the active functor we can barely measure runtime', level='warn')
      runtime = 1.0

    try:
      U.change_cwd(target_config.get_place())

      invoke_arguments = target_config.get_args_for_invocation()
      kwargs['args'] = invoke_arguments
      if invoke_arguments is not None:
        L.get_logger().log('LocalBaseRunner::run: (args) ' + str(invoke_arguments))

      command = run_functor.passive(target_config.get_target(), **kwargs)
      _, runtime = U.shell(command, time_invoc=True)
      L.get_logger().log(
          'LocalBaseRunner::run::passive_invocation -> Returned runtime: ' + str(runtime), level='debug')

    except Exception as e:
      L.get_logger().log('LocalBaseRunner::run Exception\n' + str(e), level='error')
      raise RuntimeError('LocalBaseRunner::run caught exception. ' + str(e))

    # TODO: Insert the data into the database
    return runtime


class LocalRunner(LocalBaseRunner):
  """
  The LocalRunner invokes the target application with the first argument string given in the config.
  For scalability studies, i.e., iterate over all given input sizes, use the LocalScalingRunner.
  """

  def __init__(self, configuration: PiraConfig, sink):
    """ Runner are initialized once with a PiraConfiguration """
    super().__init__(configuration, sink)
    self._num_repetitions = InvocationConfig.get_instance().get_num_repetitions()

  def get_num_repetitions(self) -> int:
    return self._num_repetitions

  def do_baseline_run(self, target_config: TargetConfig) -> M.RunResult:
    L.get_logger().log('LocalRunner::do_baseline_run')
    accu_runtime = .0

    if not target_config.has_args_for_invocation():
      L.get_logger().log('LocalRunner::do_baseline_run: BEGIN not target_config.has_args_for_invocation()')
      # This runner only takes into account the first argument string (if not already set)
      args = self._config.get_args(target_config.get_build(), target_config.get_target())
      L.get_logger().log('LocalRunner::do_baseline_run: args: ' + str(args))
      target_config.set_args_for_invocation(args[0])
      L.get_logger().log('LocalRunner::do_baseline_run: END not target_config.has_args_for_invocation()')

    # TODO Better evaluation of the obtained timings.
    time_series = M.RunResultSeries(reps=self.get_num_repetitions())
    for y in range(0, self.get_num_repetitions()):
      L.get_logger().log('LocalRunner::do_baseline_run: Running iteration ' + str(y), level='debug')
      l_runtime = self.run(target_config, InstrumentConfig())
      accu_runtime += l_runtime
      time_series.add_values(l_runtime, self.get_num_repetitions())

    run_result = M.RunResult(accu_runtime, self.get_num_repetitions())
    L.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(run_result.get_average()) + '\n', level='perf')
    L.get_logger().log('[Vanilla][RTSeries] Average: ' + str(time_series.get_average()), level='perf')
    L.get_logger().log('[Vanilla][RTSeries] Median: ' + str(time_series.get_median()), level='perf')
    L.get_logger().log('[Vanilla][RTSeries] Stdev: ' + str(time_series.get_stdev()), level='perf')
    L.get_logger().log('[Vanilla][REPETITION SUM] Vanilla sum: ' + str(time_series.get_accumulated_runtime()), level='perf')

    return time_series

  def do_profile_run(self,
                     target_config: TargetConfig,
                     instr_iteration: int) -> M.RunResult:
    L.get_logger().log(
        'LocalRunner::do_profile_run: Received instrumentation file: ' + target_config.get_instr_file(), level='debug')
    scorep_helper = M.ScorepSystemHelper(self._config)
    instrument_config = InstrumentConfig(True, instr_iteration)
    scorep_helper.set_up(target_config, instrument_config)
    runtime = .0

    if not target_config.has_args_for_invocation():
      # This runner only takes into account the first argument string (if not already set)
      args = self._config.get_args(target_config.get_build(), target_config.get_target())
      target_config.set_args_for_invocation(args[0])

    time_series = M.RunResultSeries(reps=self.get_num_repetitions())
    for y in range(0, self._num_repetitions):
      L.get_logger().log('LocalRunner::do_profile_run: Running instrumentation iteration ' + str(y), level='debug')
      l_runtime = self.run(target_config, instrument_config)
      runtime += l_runtime
      time_series.add_values(l_runtime, self.get_num_repetitions())
      # Enable further processing of the resulting profile
      self._sink.process(scorep_helper.get_exp_dir(), target_config, instrument_config)

    run_result = M.RunResult(runtime, self.get_num_repetitions())
    L.get_logger().log(
        '[Instrument][RUNTIME] $' + str(instr_iteration) + '$ ' + str(run_result.get_average()), level='perf')
    L.get_logger().log('[Instrument][RTSeries] Average: ' + str(time_series.get_average()), level='perf')
    L.get_logger().log('[Instrument][RTSeries] Median: ' + str(time_series.get_median()), level='perf')
    L.get_logger().log('[Instrument][RTSeries] Stdev: ' + str(time_series.get_stdev()), level='perf')

    return time_series


class LocalScalingRunner(LocalRunner):
  """
  The LocalScalingRunner performs measurements related to Extra-P modelling. 
  The arguments given in the configuration are treated as the different input sizes, i.e.,
  the first string is the smallest input configuration, the second is the next larger configuration, etc.
  """

  def __init__(self, configuration: PiraConfig, sink):
    super().__init__(configuration, sink)

  def do_profile_run(self,
                     target_config: TargetConfig,
                     instr_iteration: int) -> M.RunResult:
    L.get_logger().log('LocalScalingRunner::do_profile_run')
    # We run as many experiments as we have input data configs
    # TODO: How to handle the model parameter <-> input parameter relation, do we care?
    args = self._config.get_args(target_config.get_build(), target_config.get_target())
    # TODO: How to handle multiple MeasurementResult items? We get a vector of these after this function.
    #run_result = M.RunResult()
    run_result = M.RunResultSeries(reps=self.get_num_repetitions(), num_data_sets=5)
    for arg_cfg in args:
      # Call the runner method with the correct arguments.
      target_config.set_args_for_invocation(arg_cfg)
      rr = super().do_profile_run(target_config, instr_iteration)
      run_result.add_from(rr)

    # At this point we have all the data we need to construct an Extra-P model

    return run_result

  def do_baseline_run(self, target_config: TargetConfig) -> M.RunResult:
    L.get_logger().log('LocalScalingRunner::do_baseline_run')
    args = self._config.get_args(target_config.get_build(), target_config.get_target())
    #run_result = M.RunResult()
    run_result = M.RunResultSeries(reps=self.get_num_repetitions(), num_data_sets=5)
    for arg_cfg in args:
      target_config.set_args_for_invocation(arg_cfg)
      rr = super().do_baseline_run(target_config)
      run_result.add_from(rr)

    return run_result


class SlurmBaseRunner(Runner):
  """
  Base for all slurm runners.
  """
  def __init__(self, configuration: PiraConfig, slurm_configuration: SlurmConfig,
               batch_interface: BatchSystemInterface, sink):
    super().__init__(configuration, sink)
    self._slurm_config = slurm_configuration
    self.batch_interface = batch_interface

  def add_run_command(self, target_config: TargetConfig, instrument_config: InstrumentConfig) -> str:
    """
    Prepares the command and adds it via the batch interface.
    Returns a key to identify the results after batch system jobs ran.
    """
    functor_manager = F.FunctorManager()
    run_functor = functor_manager.get_or_load_functor(target_config.get_build(), target_config.get_target(),
                                                      target_config.get_flavor(), 'run')
    default_provider = D.BackendDefaults()
    kwargs = default_provider.get_default_kwargs()
    kwargs['util'] = U
    kwargs['LD_PRELOAD'] = default_provider.get_MPI_wrap_LD_PRELOAD()
    runtime = .0

    if run_functor.get_method()['active']:
      L.get_logger().log('SlurmBaseRunner::add_run_command: Active running is not possible while '
                         'dispatching to a cluster. Exiting.', level='error')
      raise RuntimeError('Active running is not possible while dispatching to a cluster.')

    try:
      U.change_cwd(target_config.get_place())

      invoke_arguments = target_config.get_args_for_invocation()

      kwargs['args'] = invoke_arguments
      if invoke_arguments is not None:
        L.get_logger().log('SlurmBaseRunner::add_run_command: (args) ' + str(invoke_arguments), level="debug")

      command = run_functor.passive(target_config.get_target(), **kwargs)

      # We add the command to the batch config via the interface here. We have to care
      # about telling the interface to run everything later, and care about retrieving
      # to results by "key" later to return them.
      key = U.generate_random_string()
      L.get_logger().log("SlurmBaseRunner::add_run_command: Using key to reference results: " + key, level="debug")

      # Repetition not used, determined by the slurm config
      self.batch_interface.add_timed_command(key=key, cmd=command)
      L.get_logger().log(f"SlurmBaseRunner::add_run_command: Added command via batch interface: {command}",
                         level="debug")

    except Exception as e:
      L.get_logger().log('SlurmBaseRunner::add_run_command: Exception\n' + str(e), level='error')
      raise RuntimeError('SlurmBaseRunner::add_run_command: Caught exception. ' + str(e))

    # TODO: Insert the data into the database
    return key

  def dispatch(self, key: str) -> int:
    """
    Start the execution of the added command(s) by dispatching to the cluster.
    :return: The job_id of the dispatched job.
    """
    L.get_logger().log(f"SlurmBaseRunner::run: Dispatch added commands.",
                       level="debug")
    job_id = self.batch_interface.dispatch(key)
    return job_id

  def wait(self) -> None:
    """
    Wait for the execution of commands to finish.
    """
    L.get_logger().log(f"SlurmBaseRunner::run: Waiting for added commands to finish.",
                       level="debug")
    self.batch_interface.wait()

  def get_runtime(self, key: str, repetition: int) -> float:
    """
    Return the results from a run, by requesting the batch system interface.
    """
    L.get_logger().log(f"SlurmBaseRunner::get_runtime: Reading runtime for key {key}, repetition"
                       f" {repetition}", level="debug")
    return self.batch_interface.get_results(key, repetition)[0]


class SlurmRunner(SlurmBaseRunner):
  """
  The SlurmRunner invokes the target application with the first argument string given in the config.
  For scalability studies, i.e., iterate over all given input sizes, use the SlurmScalingRunner.
  """

  def __init__(self, configuration: PiraConfig, slurm_configuration: SlurmConfig,
               batch_interface: BatchSystemInterface, sink):
    super().__init__(configuration, slurm_configuration, batch_interface, sink)
    generator = SlurmGenerator(slurm_configuration)
    generator.add_modules()
    self.batch_interface.configure(slurm_configuration, generator)
    self._num_repetitions = InvocationConfig.get_instance().get_num_repetitions()

  def get_num_repetitions(self) -> int:
      return self._num_repetitions

  def do_profile_run(self,
                     target_config: TargetConfig,
                     instr_iteration: int) -> M.RunResultSeries:
    L.get_logger().log(
      'SlurmRunner::do_profile_run: Received instrumentation file: ' + target_config.get_instr_file(), level='debug')
    scorep_helper = M.ScorepSystemHelper(self._config)
    instrument_config = InstrumentConfig(True, instr_iteration)
    scorep_helper.set_up(target_config, instrument_config)

    # List of tupels (iteration number, key)
    command_result_map: typing.List[typing.Tuple[int, str]] = []

    if not target_config.has_args_for_invocation():
      # This runner only takes into account the first argument string (if not already set)
      args = self._config.get_args(target_config.get_build(), target_config.get_target())
      target_config.set_args_for_invocation(args[0])

    self.dispatch_run(target_config, instrument_config, command_result_map, scorep_var_export=True)

    self.wait_run()

    time_series = M.RunResultSeries(reps=self.get_num_repetitions())

    # instead of setting append_iteration, we need to copy back one of the cubes to the original
    # cube dir here, this is where the analyzer expects to find it
    # this ensures, that we know which cube will be used in the analyzer, instead of just using one of them.
    # one of them would work, but it can be good to know which one it is for error tracing.
    last_rep = str(self.get_num_repetitions()-1)
    last_rep_dir = f"{scorep_helper.get_exp_dir()}-{last_rep}"
    cube_src = f"{U.get_cubex_file(last_rep_dir, target_config.get_target(), target_config.get_flavor())}"
    cube_to = f"{U.get_cubex_file(scorep_helper.get_exp_dir(), target_config.get_target(), target_config.get_flavor())}"
    U.copy_file(f"{cube_src}", f"{cube_to}")
    L.get_logger().log(f"SlurmRunner::do_profile_run: Copied cube form last repetition {cube_src} to {cube_to} for "
                       f"examination by the analyzer.", level="debug")
    del last_rep, last_rep_dir, cube_src, cube_to

    self.collect_run(command_result_map, time_series, scorep_helper, target_config,
                     instrument_config, instr_iteration)

    # cleanup for the next iteration
    self.batch_interface.cleanup()

    return time_series

  def do_baseline_run(self, target_config: TargetConfig) -> RunResultSeries:
    """
    Do the baseline run.
    """
    L.get_logger().log('SlurmRunner::do_baseline_run', level="debug")

    # List of tupels (iteration number, key)
    command_result_map: typing.List[typing.Tuple[int, str]] = []

    if not target_config.has_args_for_invocation():
      L.get_logger().log('SlurmRunner::do_baseline_run: BEGIN not target_config.has_args_for_invocation()',
                         level="debug")
      # This runner only takes into account the first argument string (if not already set)
      args = self._config.get_args(target_config.get_build(), target_config.get_target())
      L.get_logger().log('SlurmRunner::do_baseline_run: args: ' + str(args), level="debug")
      target_config.set_args_for_invocation(args[0])
      L.get_logger().log('SlurmRunner::do_baseline_run: END not target_config.has_args_for_invocation()',
                         level="debug")

    self.dispatch_run(target_config, InstrumentConfig(), command_result_map)

    self.wait_run()

    # TODO Better evaluation of the obtained timings.
    time_series = M.RunResultSeries(reps=self.get_num_repetitions())
    self.collect_run(command_result_map, time_series)

    # cleanup for the next iteration
    self.batch_interface.cleanup()

    return time_series

  # Methods for each part of the pipeline. They are puzzled togehter in different orders
  # by the do_baseline_run and do_profile_run methods of each this and the derived Scalability runner
  # in order in which they might be used

  def dispatch_run(self, target_config: TargetConfig, instrumentation_config: InstrumentConfig,
                   command_result_map: typing.List[typing.Tuple[int, str]],
                   scorep_var_export: bool = False) -> int:
    """
    Set up and dispatch a run to SLURM.
    :param target_config: the target config that should be used.
    :param instrumentation_config: the instrumentation configuration to be used by the run.
    :param command_result_map: A out parameter. Will be used to add the key and repetitions
    to the upper methods command_result_map for the run to know about.
    :param scorep_var_export: For the Score-P setup to work with parallel repetitions, it is needed
    that the SCOREP_EXPERIMENT_DIR env var is modified before and together with the actual execution of the
    target, to ensure all repetitions can be resolved later. Set this to true, if you want SLURM to care about this.
    :return: Additionally returns the job_id of the dispatched job. Might be used for
    dependency modelling in scalability experiments (derived runner).
    """
    L.get_logger().log('SlurmRunner::set_up_run: Adding command for repetitions', level='debug')
    key = self.add_run_command(target_config, instrumentation_config)
    if scorep_var_export:
      # add export command for SCOREP_EXPERIMENT_DIRECTORY
      self.batch_interface.add_preparation_command(key,
                                                   "export SCOREP_EXPERIMENT_DIRECTORY="
                                                   "$SCOREP_EXPERIMENT_DIRECTORY-$SLURM_ARRAY_TASK_ID")
    for y in range(0, self.get_num_repetitions()):
      # Add key for all repetitions
      # We can use this key, and the iteration number to retreive the result
      command_result_map.append((y, key))
    L.get_logger().log('SlurmRunner::dispatch_run: Running all iterations on batch system', level='debug')
    job_id = self.dispatch(key)
    return job_id

  def wait_run(self):
    """
    Wait for the runs job to finish.
    """
    self.wait()

  def collect_run(self, command_result_map, time_series, scorep_helper=None, target_config=None, instrument_config=None,
                  instr_iteration: int = None, append_repetition: bool = False) -> float:
    """
    Collect the results for all dispatched runs.
    :param command_result_map: The list of entries to collect results for.
    :param time_series: Out parameter. The RunResultSeries to which the runtimes should be
    added, to later evaluation form the above methods.
    All following parameters: Only needed if called form a do_profile_run method:
    :param scorep_helper: The scorep helper object.
    :param target_config: The target config.
    :param instrument_config: The instrumentation config.
    :param instr_iteration: The current instrumentation iteration (for printing).
    :param append_repetition: If the repetition should be appended to the experiment-dir of score-p.
    :return: The runtime of the job.
    """
    accu_runtime = 0
    for i, (repetition, key) in enumerate(command_result_map):
      l_runtime = self.get_runtime(key, repetition)
      accu_runtime += l_runtime
      time_series.add_values(l_runtime, self.get_num_repetitions())
      if scorep_helper is not None:
        # Enable further processing of the resulting profile
        self._sink.process(f"{scorep_helper.get_exp_dir()}{'-'+str(repetition) if append_repetition else ''}",
                           target_config, instrument_config)
    run_result = M.RunResult(accu_runtime, self.get_num_repetitions())
    if scorep_helper is not None:
      # instrumentation prints
      L.get_logger().log(
        '[Instrument][RUNTIME] $' + str(instr_iteration) + '$ ' + str(run_result.get_average()), level='perf')
      L.get_logger().log('[Instrument][RTSeries] Average: ' + str(time_series.get_average()), level='perf')
      L.get_logger().log('[Instrument][RTSeries] Median: ' + str(time_series.get_median()), level='perf')
      L.get_logger().log('[Instrument][RTSeries] Stdev: ' + str(time_series.get_stdev()), level='perf')
    else:
      # vanilla perf prints
      L.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(run_result.get_average()) + '\n', level='perf')
      L.get_logger().log('[Vanilla][RTSeries] Average: ' + str(time_series.get_average()), level='perf')
      L.get_logger().log('[Vanilla][RTSeries] Median: ' + str(time_series.get_median()), level='perf')
      L.get_logger().log('[Vanilla][RTSeries] Stdev: ' + str(time_series.get_stdev()), level='perf')
      L.get_logger().log('[Vanilla][REPETITION SUM] Vanilla sum: ' + str(time_series.get_accumulated_runtime()),
                         level='perf')
    return accu_runtime


class SlurmScalingRunner(SlurmRunner):
  """
  The SlurmScalingRunner performs measurements related to Extra-P modelling.
  The arguments given in the configuration are treated as the different input sizes, i.e.,
  the first string is the smallest input configuration, the second is the next larger configuration, etc.

  About the "interface" option in scalability experiments:
  Dispatching a scalability experiment, means dispatching
  multiple jobs to the same time. This way the may run in parallel. If self.force_sequential is set
  dependencies between the jobs will be added, SLURM will take care that they actually run sequential.
  So in summary: First dispatch each job, wait for them all to finish, and gather all their results.
  But this brings some problems with the "interface" option along:
  1) We need to make sure that we do use a non-blocking dispatch method - otherwise it will block until
     finished in the dispatch loop, which means it will be sequential again. So, valid is "pyslurm", and "os",
     but not "sbatch-wait".
  2) We need to make sure that we do use a non-blocking wait function for each job, since we now need to
     wait for a set of multiple jobs. Sadly, "pyslurm" as well as "sbatch-wait" (see bevor), are blocking.
     The only method which can handle waiting for a group of jobs at the moment is to use "os" (Since it
     is pulling and not handling the blocking of to sbatch or pyslurm).
  That's because we're manipulating the batch interfaces "interface" option before these steps here, to adhere
  to these rules.
  """

  def __init__(self, configuration: PiraConfig, slurm_configuration: SlurmConfig,
               batch_interface: BatchSystemInterface, sink):
    """
    Constructor.
    """
    super().__init__(configuration, slurm_configuration, batch_interface, sink)
    # force scalability if set in config
    self.force_sequential = slurm_configuration.force_sequential

  def do_profile_run(self,
                     target_config: TargetConfig,
                     instr_iteration: int) -> RunResultSeries:
    """
    Slurm profile scaling run.
    """
    L.get_logger().log('SlurmScalingRunner::do_baseline_run', level="debug")

    # saving the batch interface from the config, to restore it later
    config_batch_interface = self.batch_interface.interface

    args = self._config.get_args(target_config.get_build(), target_config.get_target())

    # List of command_result_maps for all args
    cmd_maps = []
    # list to save the job_ids
    jobs = []

    # check if interface for dispatching adheres to rule 1), see class docstring
    if self.batch_interface.interface == SlurmInterfaces.SBATCH_WAIT:
      L.get_logger().log("SlurmScalingRunner::do_profile_run: Interface 'sbatch-wait' is a blocking "
                         "dispatch interface, which cannot be used with scaling experiments."
                         " Downgrading to 'os'.", level="warn")
      self.batch_interface.interface = SlurmInterfaces.OS

    # map to save setup for the score-p related stuff
    tool_map = {}

    # dispatch job for each arg
    for i, arg in enumerate(args):
      # setup args for invocation
      target_config.set_args_for_invocation(arg)
      # set up score-p related stuff upfront (needs to be initialized bevor the target runs)
      L.get_logger().log(
        'SlurmScalingRunner::do_profile_run: Received instrumentation file: ' + target_config.get_instr_file(),
        level='debug')
      scorep_helper = M.ScorepSystemHelper(self._config)
      instrument_config = InstrumentConfig(True, instr_iteration)
      # give the arg along, to set up the experiment dir of score-p:
      # this way we can run multiple args in parallel, and still retrieving
      # the results individually later in this iteration
      scorep_helper.set_up(target_config, instrument_config, arg)
      tool_map[i] = (scorep_helper, instrument_config)
      # List of tupels (iteration number, key)
      command_result_map: typing.List[typing.Tuple[int, str]] = []
      # if force sequential: add dependency to job_id before
      if self.force_sequential and i > 0:
        self.batch_interface.generator.config.dependencies = f"afterok:{jobs[i - 1]}"
      else:
        self.batch_interface.generator.config.dependencies = ""
      # set scorep_var_export to split repetitions
      job_id = self.dispatch_run(target_config, InstrumentConfig(), command_result_map, scorep_var_export=True)
      jobs.append(job_id)
      cmd_maps.append(command_result_map)

    # waiting needs to be done with non-blocking wait 'os' - rule 2), see class docstring
    if self.batch_interface.interface != SlurmInterfaces.OS:
      L.get_logger().log(f"SlurmScalingRunner::do_profile_run: {str(self.batch_interface.interface)} is a blocking "
                         "wait interface, which cannot be used with scaling experiments."
                         " Downgrading to 'os'.", level="warn")
      self.batch_interface.interface = SlurmInterfaces.OS
    # wait for the group of all jobs to finish
    self.wait_run()

    run_result = M.RunResultSeries(reps=self.get_num_repetitions(), num_data_sets=5)
    for i, (cmd_map, arg) in enumerate(zip(cmd_maps, args)):
      # args overwrite each other, so we have to do this also before evaluating, to process for the correct args
      target_config.set_args_for_invocation(arg)
      # get score-p related helpers again, were set up in dispatch loop
      scorep_helper = tool_map[i][0]
      instrument_config = tool_map[i][1]
      # init timing saving container and read results
      time_series = M.RunResultSeries(reps=self.get_num_repetitions())
      # set append_repetition to read from repetition cube-dirs - opponent to scorep_var_export from above
      self.collect_run(cmd_map, time_series, scorep_helper, target_config, instrument_config, instr_iteration,
                       append_repetition=True)
      run_result.add_from(time_series)

    self.batch_interface.cleanup()
    # restore the batch interface
    self.batch_interface.interface = config_batch_interface

    return run_result

  def do_baseline_run(self, target_config: TargetConfig) -> RunResultSeries:
    """
    Slurm baseline scaling run.
    """
    L.get_logger().log('SlurmScalingRunner::do_baseline_run', level="debug")

    # saving the batch interface from the config, to restore it later
    config_batch_interface = self.batch_interface.interface

    args = self._config.get_args(target_config.get_build(), target_config.get_target())

    # List of command_result_maps for all args
    cmd_maps = []
    jobs = []

    # check if interface for dispatching adheres to rule 1), see class docstring
    if self.batch_interface.interface == SlurmInterfaces.SBATCH_WAIT:
      L.get_logger().log("SlurmScalingRunner::do_baseline_run: Interface 'sbatch-wait' is a blocking "
                         "dispatch interface, which cannot be used with scaling experiments. "
                         "Downgrading to 'os'.", level="warn")
      self.batch_interface.interface = SlurmInterfaces.OS
    # dispatch job for each arg
    for i, arg in enumerate(args):
      # setup args for invocation
      target_config.set_args_for_invocation(arg)
      # List of tupels (iteration number, key)
      command_result_map: typing.List[typing.Tuple[int, str]] = []
      # if force sequential: add dependency to job_id before
      if self.force_sequential and i > 0:
        self.batch_interface.generator.config.dependencies = f"afterok:{jobs[i-1]}"
      else:
        self.batch_interface.generator.config.dependencies = ""
      job_id = self.dispatch_run(target_config, InstrumentConfig(), command_result_map)
      jobs.append(job_id)
      cmd_maps.append(command_result_map)

    # waiting needs to be done with non-blocking wait 'os' - rule 2)s
    if self.batch_interface.interface != SlurmInterfaces.OS:
      L.get_logger().log(f"SlurmScalingRunner::do_baseline_run: {str(self.batch_interface.interface)} is a blocking "
                         "wait interface, which cannot be used with scaling experiments."
                         " Downgrading to 'os'.", level="warn")
      self.batch_interface.interface = SlurmInterfaces.OS
    # wait for the group of all jobs to finish
    self.wait_run()

    run_result = M.RunResultSeries(reps=self.get_num_repetitions(), num_data_sets=5)
    for map in cmd_maps:
      time_series = M.RunResultSeries(reps=self.get_num_repetitions())
      self.collect_run(map, time_series)
      run_result.add_from(time_series)

    self.batch_interface.cleanup()
    # restore the batch interface
    self.batch_interface.interface = config_batch_interface

    return run_result

