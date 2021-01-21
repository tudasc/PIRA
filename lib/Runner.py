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

import typing


class Runner:
  pass


class LocalBaseRunner(Runner):
  """
  The base class for execution on the same machine. It implements the basic *run* method, which invokes the target.
  """

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
    for y in range(0, self._num_repetitions):
      L.get_logger().log('LocalRunner::do_baseline_run: Running iteration ' + str(y), level='debug')
      accu_runtime += self.run(target_config, InstrumentConfig())

    run_result = M.RunResult(accu_runtime, self._num_repetitions)
    L.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(run_result.get_average()) + '\n', level='perf')

    return run_result

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

    for y in range(0, self._num_repetitions):
      L.get_logger().log('LocalRunner::do_profile_run: Running instrumentation iteration ' + str(y), level='debug')
      runtime = runtime + self.run(target_config, instrument_config)
      # Enable further processing of the resulting profile
      self._sink.process(scorep_helper.get_exp_dir(), target_config, instrument_config)

    run_result = M.RunResult(runtime, self._num_repetitions)
    L.get_logger().log(
        '[Instrument][RUNTIME] $' + str(instr_iteration) + '$ ' + str(run_result.get_average()), level='perf')
    return run_result


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
    run_result = M.RunResult()
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
    run_result = M.RunResult()
    for arg_cfg in args:
      target_config.set_args_for_invocation(arg_cfg)
      rr = super().do_baseline_run(target_config)
      run_result.add_from(rr)

    return run_result


class SlurmRunner(Runner):
  """  TODO This runner executes the measurements on a slurm allocated job. """
  pass
