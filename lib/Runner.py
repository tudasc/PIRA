"""
File: Runner.py
Author: JP Lehr
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

import typing


class Runner:
  pass


class LocalRunner(Runner):
  """  This is the new runner class. It implements the original idea of the entity being responsible for executing the target.  """

  def __init__(self, configuration: PiraConfiguration):
    """ Runner are initialized once with a PiraConfiguration """
    self._config = configuration

  def run(self, target_config: TargetConfiguration, instrument_config: InstrumentConfig, compile_time_filtering: bool):
    """ Implements the actual invocation """
    functor_manager = fm.FunctorManager()
    run_functor = functor_manager.get_or_load_functor(target_config.get_build(), target_config.get_target(),
                                                      target_config.get_flavor(), 'run')
    kwargs = {}
    runtime = .0

    if run_functor.get_method()['active']:
      kwargs['util'] = util
      run_functor.active(target_config.get_target(), **kwargs)
      log.get_logger().log('For the active functor we can barely measure runtime', level='warn')
      runtime = 1.0

    try:
      util.change_cwd(target_config.get_build())
      scorep_helper = ms.ScorepSystemHelper(self._config)
      scorep_helper.set_up(target_config, instrument_config, compile_time_filtering)
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
                     compile_time_filtering: bool = True) -> ms.RunResult:
    log.get_logger().log('LocalRunner::do_profile_run')
    log.get_logger().log(
        'LocalRunner::do_profile_run: Received instrumentation file: ' + target_config.get_instr_file(), level='debug')
    runtime = self.run(target_config, InstrumentConfig(True, instr_iteration), compile_time_filtering)

    run_result = ms.RunResult(runtime, 1)
    log.get_logger().log(
        '[Instrument][RUNTIME] $' + str(instr_iteration) + '$ ' + str(run_result.get_average()), level='perf')
    return run_result


class SlurmRunner(Runner):
  """  TODO This runner executes the measurements on a slurm allocated job. """
  pass