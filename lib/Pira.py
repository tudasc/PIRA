"""
File: Pira.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module implementing the main workflow of PIRA.
"""

import lib.Logging as L
import lib.Utility as U
import lib.BatchSystemHelper as B
import lib.FunctorManagement as F
import lib.TimeTracking as T
import lib.Database as D
import lib.Exporter as E
import lib.Checker as C
from lib.DefaultFlags import BackendDefaults
from lib.RunnerFactory import PiraRunnerFactory
from lib.ConfigurationLoader import SimplifiedConfigurationLoader as SCLoader
from lib.ConfigurationLoader import ConfigurationLoader as CLoader
from lib.Configuration import TargetConfig, PiraConfig, ExtrapConfig, InvocationConfig, \
  PiraConfigErrorException, CSVConfig

from lib.Runner import Runner, LocalRunner, LocalScalingRunner
from lib.Builder import Builder as BU
from lib.Analyzer import Analyzer as A


import typing
import sys
import os

def execute_with_config(runner: Runner, analyzer: A, target_config: TargetConfig, csv_config: CSVConfig) -> None:
  try:
    instrument = False
    was_rebuilt = True

    #rr_exporter = E.RunResultExporter()
    rr_exporter = E.PiraRuntimeExporter()

    # Build without any instrumentation
    L.get_logger().log('Building vanilla version for baseline measurements', level='info')
    vanilla_builder = BU(target_config, instrument)
    tracker = T.TimeTracker()
    tracker.m_track('Vanilla Build', vanilla_builder, 'build')

    # Run without instrumentation for baseline
    L.get_logger().log('Running baseline measurements', level='info')
    vanilla_rr = runner.do_baseline_run(target_config)
    L.get_logger().log(
        'Pira::execute_with_config: RunResult: ' + str(vanilla_rr) + ' | avg: ' + str(vanilla_rr.get_average()),
        level='debug')
    instr_file = ''

    if (csv_config.should_export()):
      rr_exporter.add_iteration_data('Vanilla', vanilla_rr)

    for iteration in range(0,InvocationConfig.get_instance().get_pira_iters()):
      L.get_logger().log('Running instrumentation iteration ' + str(iteration), level='info')

      # Only run the pgoe to get the functions name
      iteration_tracker = T.TimeTracker()

      # Analysis Phase
      instr_file = analyzer.analyze(target_config, iteration, was_rebuilt)
      was_rebuilt = False
      L.get_logger().log('[WHITELIST] $' + str(iteration) + '$ ' + str(U.lines_in_file(instr_file)), level='perf')
      U.shell('stat ' + instr_file)

      # After baseline measurement is complete, do the instrumented build/run
      # This is only necessary in every iteration when run in compile-time mode.
      # For hybrid-filtering this is done after the specified amount of iterations
      if needs_rebuild(iteration):
          was_rebuilt = True
          instrument = True
          instr_builder = BU(target_config, instrument, instr_file)
          tracker.m_track('Instrument Build', instr_builder, 'build')

      # Run Phase
      L.get_logger().log('Running profiling measurements', level='info')
      instr_rr = runner.do_profile_run(target_config, iteration)
      if(csv_config.should_export()):
        rr_exporter.add_iteration_data('Instrumented ' + str(iteration), instr_rr)

      # Compute overhead of instrumentation
      ovh_percentage = instr_rr.compute_overhead(vanilla_rr)
      L.get_logger().log('[RUNTIME] $' + str(iteration) + '$ ' + str(instr_rr.get_average()), level='perf')
      L.get_logger().log('[OVERHEAD] $' + str(iteration) + '$ ' + str(ovh_percentage), level='perf')
      L.get_logger().log('[REPETITION SUM] $' + str(iteration) + '$ ' + str(instr_rr.get_accumulated_runtime()), level='perf')

      iteration_tracker.stop()
      user_time, system_time = iteration_tracker.get_time()
      L.get_logger().log('[ITERTIME] $' + str(iteration) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

    if(csv_config.should_export()):
      file_name = target_config.get_target() + '-' +  target_config.get_flavor() + '.csv'
      csv_file = os.path.join(csv_config.get_csv_dir(), file_name)
      try:
        U.make_dir(csv_config.get_csv_dir())
        rr_exporter.export(csv_file, csv_config.get_csv_dialect())
      except Exception as e:
        L.get_logger().log(
          'Pira::execute_with_config: Problem writing CSV file\nMessage:\n' + str(e), level='error')

  except Exception as e:
    L.get_logger().log(
        'Pira::execute_with_config: Problem during preparation of run.\nMessage:\n' + str(e), level='error')
    raise RuntimeError(str(e))

def do_rebuild(build_name: str, target_config: TargetConfig, instrument: bool, instr_file: str=None) -> None:
  if instrument and instr_file == None:
    L.get_logger().log('Should instrument but no instrumentation file.', level='error')
    raise Exception('instrument and no instrumentation file')

  builder = BU(target_config, instrument, instr_file)
  tracker = T.TimeTracker()
  tracker.m_track(build_name, builder, 'build')


def needs_rebuild(iteration: int) -> bool:
  hybrid_filtering = InvocationConfig.get_instance().is_hybrid_filtering()
  hybrid_filter_iters = InvocationConfig.get_instance().get_hybrid_filter_iters()
  compile_time_filtering = InvocationConfig.get_instance().is_compile_time_filtering()
  return compile_time_filtering or (iteration == 0) or (hybrid_filtering and (iteration % hybrid_filter_iters == 0))



def process_args_for_extrap(cmdline_args) -> typing.Tuple[bool, ExtrapConfig]:
  use_extra_p = False
  extrap_config = ExtrapConfig('', '', '')
  if cmdline_args.extrap_dir != '':
    use_extra_p = True
    extrap_config = ExtrapConfig(cmdline_args.extrap_dir, cmdline_args.extrap_prefix, '')

    num_reps = cmdline_args.repetitions
    if num_reps < 5:
      L.get_logger().log('At least 5 repetitions are recommended for Extra-P modelling.', level='warn')
      if num_reps < 0:
        L.get_logger().log('REMEMBER TO REMOVE IN PIRA::process_args_for_extrap', level='warn')
        L.get_logger().log('At least 3 repetitions are required for Extra-P modelling.', level='error')
        raise RuntimeError('At least 5 repetitions are needed for Extra-P modelling.')

  return use_extra_p, extrap_config


def process_args_for_csv(cmdline_args):
  csv_dir = cmdline_args.csv_dir
  csv_dialect = cmdline_args.csv_dialect
  csv_cfg = CSVConfig(csv_dir, csv_dialect)
  return csv_cfg


def main(cmdline_args) -> None:
  """ Main function for pira framework. Used to invoke the various components. """
  invoc_cfg = InvocationConfig(cmdline_args)
  L.get_logger().log(str(invoc_cfg),level='info')
  use_extra_p, extrap_config = process_args_for_extrap(cmdline_args)
  home_dir = U.get_cwd()
  U.set_home_dir(home_dir)
  U.make_dir(invoc_cfg.get_pira_dir())

  csv_config = process_args_for_csv(cmdline_args)

  try:
    if invoc_cfg.get_config_version() == 1:
      config_loader = CLoader()
    else:
      config_loader = SCLoader()

    configuration = config_loader.load_conf()
    C.Checker.check_configfile(configuration)

    if B.check_queued_job():
      # FIXME: Implement
      L.get_logger().log('In this version of PIRA it is not yet implemented', level='error')
      assert (False)

    else:
      '''
      This branch is running PIRA actively on the local machine.
      It is blocking, and the user can track the progress in the terminal.
      '''
      L.get_logger().log('Running the local case')

      # The FunctorManager manages loaded functors and generates the respective names
      F.FunctorManager(configuration)
      dbm = D.DBManager(D.DBManager.db_name + '.' + D.DBManager.db_ext)
      dbm.create_cursor()
      analyzer = A(configuration)

      runner_factory = PiraRunnerFactory(configuration)
      runner = runner_factory.get_simple_local_runner()
      if use_extra_p:
        L.get_logger().log('Running with Extra-P runner')
        runner = runner_factory.get_scalability_runner(extrap_config)

      if runner.has_sink():
        analyzer.set_profile_sink(runner.get_sink())

      # A build/place is a top-level directory
      for build in configuration.get_builds():
        L.get_logger().log('Build: ' + str(build))
        total_time = T.TimeTracker()
        app_tuple = (U.generate_random_string(), build, '', '')
        dbm.insert_data_application(app_tuple)

        # An item is a target/software in that directory
        for item in configuration.get_items(build):
          L.get_logger().log('Running for item ' + str(item))

          # A flavor is a specific version to build
          if configuration.has_local_flavors(build, item):
            for flavor in configuration.get_flavors(build, item):
              L.get_logger().log('Running for local flavor ' + flavor, level='debug')

              # prepare database, and get a unique handle for current item.
              db_item_id = dbm.prep_db_for_build_item_in_flavor(configuration, build, item, flavor)
              # Create configuration object for the item currently processed.
              place = configuration.get_place(build)
              t_config = TargetConfig(place, build, item, flavor, db_item_id)
              # Execute using a local runner, given the generated target description
              execute_with_config(runner, analyzer, t_config, csv_config)

          # If global flavor
          else:
            # TODO: Implement
            L.get_logger().log('In this version of PIRA it is not yet implemented', level='error')
            assert (False)

        total_time.stop()
        L.get_logger().log('PIRA total runtime: {}'.format(total_time.get_time()), level='perf')


    U.change_cwd(home_dir)

  except RuntimeError as rt_err:
    U.change_cwd(home_dir)
    L.get_logger().log('Runner.run caught exception. Message: ' + str(rt_err), level='error')
    L.get_logger().dump_tape()
    sys.exit(-1)
