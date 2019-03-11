"""
File: Runner.py
Author: JP Lehr, Sachin Manawadi 
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to run the target software.
"""

import sys
sys.path.append('..')

import lib.Utility as util
import lib.Logging as log
from lib.Configuration import PiraConfiguration, TargetConfiguration, InstrumentConfig
import lib.FunctorManagement as fm
import lib.Measurement as ms
import lib.DefaultFlags as defaults

import typing


class Runner:
  pass


class LocalRunner(Runner):
  """  This is the new runner class. It implements the original idea of the entity being responsible for executing the target.  """

  def __init__(self, configuration: PiraConfiguration, sink):
    """ Runner are initialized once with a PiraConfiguration """
    self._config = configuration
    self._sink = sink

  def run(self, target_config: TargetConfiguration, instrument_config: InstrumentConfig, compile_time_filtering: bool):
    """ Implements the actual invocation """
    functor_manager = fm.FunctorManager()
    run_functor = functor_manager.get_or_load_functor(target_config.get_build(), target_config.get_target(),
                                                      target_config.get_flavor(), 'run')
    default_provider = defaults.BackendDefaults()
    kwargs = default_provider.get_default_kwargs()
    kwargs['util'] = util
    runtime = .0

    if run_functor.get_method()['active']:
      run_functor.active(target_config.get_target(), **kwargs)
      log.get_logger().log('For the active functor we can barely measure runtime', level='warn')
      runtime = 1.0

    try:
      util.change_cwd(target_config.get_build())

      invoke_arguments = target_config.get_args_for_invocation()
      kwargs['args'] = invoke_arguments
      log.get_logger().log('LocalRunner::run: (args) ' + invoke_arguments)

      command = run_functor.passive(target_config.get_target(), **kwargs)
      _, runtime = util.shell(command, time_invoc=True)
      log.get_logger().log('LocalRunner::run::passive_invocation -> Returned runtime: ' + str(runtime), level='debug')

    except Exception as e:
      log.get_logger().log('LocalRunner::run Exception\n' + str(e), level='error')

    # TODO: Insert the data into the database
    return runtime

  def do_baseline_run(self, target_config: TargetConfiguration, iterations: int) -> ms.RunResult:
    log.get_logger().log('LocalRunner::do_baseline_run')
    accu_runtime = .0
    num_vanilla_repetitions = iterations  # XXX This should be a command line argument?
    # Baseline run. TODO Better evaluation of the obtained timings.
    for y in range(0, num_vanilla_repetitions):
      log.get_logger().log('Running iteration ' + str(y), level='debug')
      accu_runtime += self.run(target_config, InstrumentConfig(), True)

    run_result = ms.RunResult(accu_runtime, iterations)
    log.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(run_result.get_average()), level='perf')

    return run_result

  def do_profile_run(self,
                     target_config: TargetConfiguration,
                     instr_iteration: int,
                     num_repetitions: int,
                     compile_time_filtering: bool = True) -> ms.RunResult:
    log.get_logger().log('LocalRunner::do_profile_run')
    log.get_logger().log(
        'LocalRunner::do_profile_run: Received instrumentation file: ' + target_config.get_instr_file(), level='debug')
    scorep_helper = ms.ScorepSystemHelper(self._config)
    instrument_config = InstrumentConfig(True, instr_iteration)
    scorep_helper.set_up(target_config, instrument_config, compile_time_filtering)
    runtime = .0

    for y in range(0, num_repetitions):
      log.get_logger().log('Running instrumentation iteration ' + str(y), level='debug')
      runtime = runtime + self.run(target_config, instrument_config, compile_time_filtering)
      # Enable further processing of the resulting profile
      self._sink.process(scorep_helper.get_exp_dir(), target_config, instrument_config)

    run_result = ms.RunResult(runtime, num_repetitions)
    log.get_logger().log(
        '[Instrument][RUNTIME] $' + str(instr_iteration) + '$ ' + str(run_result.get_average()), level='perf')
    return run_result


class LocalScalingRunner(LocalRunner):
  """
  The LocalScalingRunner performs measurements related to Extra-P modelling. 
  The arguments given in the configuration are treated as the different input sizes, i.e.,
  the first string is the smallest input configuration, the second is the next larger configuration, etc.
  """

  def __init__(self, configuration: PiraConfiguration, sink):
    super().__init__(configuration, sink)

  def do_profile_run(self,
                     target_config: TargetConfiguration,
                     instr_iteration: int,
                     num_repetitions: int,
                     compile_time_filtering: bool = True) -> ms.RunResult:
    log.get_logger().log('LocalScalingRunner::do_profile_run')
    # We run as many experiments as we have input data configs
    # TODO: How to handle the model parameter <-> input parameter relation, do we care?
    args = self._config.get_args(target_config.get_build(), target_config.get_target())
    # TODO: How to handle multiple MeasurementResult items? We get a vector of these after this function.
    for arg_cfg in args:
      # Call the runner method with the correct arguments.
      target_config.set_args_for_invocation(arg_cfg)
      super().do_profile_run(target_config, instr_iteration, num_repetitions, compile_time_filtering)

    return ms.RunResult(3.0, 1)

  def do_baseline_run(self, target_config: TargetConfiguration, iterations: int) -> ms.RunResult:
    log.get_logger().log('LocalScalingRunner::do_baseline_run')
    args = self._config.get_args(target_config.get_build(), target_config.get_target())
    for arg_cfg in args:
      target_config.set_args_for_invocation(arg_cfg)
      super().do_baseline_run(target_config, iterations)

    return ms.RunResult(3.0, 1)


class SlurmRunner(Runner):
  """  TODO This runner executes the measurements on a slurm allocated job. """
  pass