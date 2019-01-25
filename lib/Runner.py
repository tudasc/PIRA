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
from lib.Configuration import PiraConfiguration, TargetConfiguration
import lib.FunctorManagement as fm
import lib.Measurement as ms

import typing

class Runner:
  pass

class LocalRunner(Runner):

  """This is the new runner class. It implements the original idea of the entity being responsible for executing the target.
  TODO: Move this class to its own file, once it is working.
  """
  class InstrumentConfig:
    """  Holds information how instrumentation is handled in the different run phases.  """
    def __init__(self, is_instrumentation_run=False, instrumentation_iteration=None):
      self._is_instrumentation_run = is_instrumentation_run
      self._instrumentation_iteration = instrumentation_iteration
    
    def get_instrumentation_iteration(self):
      return self._instrumentation_iteration
    
    def is_instrumentation_run(self):
      return self._is_instrumentation_run
    
  def __init__(self, configuration: PiraConfiguration):
    """ Runner are initialized once with a PiraConfiguration """
    self._config = configuration
  
  def run(self, target_config: TargetConfiguration, instrument_config: InstrumentConfig):
    """ Implements the actual invocation """
    functor_manager = fm.FunctorManager()
    run_functor = functor_manager.get_or_load_functor(target_config.get_build(), target_config.get_target(), target_config.get_flavor(), 'run')
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
      scorep_helper.set_up(target_config, instrument_config)
      command = run_functor.passive(target_config.get_target(), **kwargs)
      _, runtime = util.shell(command, time_invoc=True)
      log.get_logger().log('LocalRunner::run::passive_invocation -> Returned runtime: ' + str(runtime), level='debug')
    
    except Exception as e:
      log.get_logger().log('Problem in LocalRunner::run\n' + str(e))
    
    # TODO: Insert the data into the database
    return runtime


  def do_baseline_run(self, target_config: TargetConfiguration, iterations: int) -> ms.RunResult:
    log.get_logger().log('LocalRunner::do_baseline_run')
    accu_runtime = .0
    num_vanilla_repetitions = iterations # XXX This should be a command line argument?
    # Baseline run. TODO Better evaluation of the obtained timings.
    for y in range(0, num_vanilla_repetitions):
      log.get_logger().log('Running iteration ' + str(y), level='debug')
      accu_runtime += self.run(target_config, LocalRunner.InstrumentConfig())

    run_result = ms.RunResult(accu_runtime, iterations)
    log.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(run_result.get_average()), level='perf')

    return run_result
  
  def do_profile_run(self, target_config: TargetConfiguration, instr_iteration: int) -> ms.RunResult:
    log.get_logger().log('LocalRunner::do_profile_run')
    runtime = self.run(target_config, LocalRunner.InstrumentConfig(True, instr_iteration))

    run_result = ms.RunResult(runtime, 1)
    log.get_logger().log('[Instrument][RUNTIME] $' + str(instr_iteration) + '$ ' + str(run_result.get_average()), level='perf')
    return run_result
 