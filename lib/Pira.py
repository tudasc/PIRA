"""
File: Pira.py
Author: JP Lehr, Sachin Manawadi
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module implementing the main workflow of PIRA.
"""

from lib.ConfigurationLoader import ConfigurationLoader as CLoader
from lib.Configuration import TargetConfiguration, PiraConfiguration
from lib.Runner import Runner, LocalRunner, LocalScalingRunner
from lib.Builder import Builder as B
from lib.Analyzer import Analyzer as A
import lib.Logging as log
import lib.Utility as util
import lib.BatchSystemHelper as bat_sys
import lib.FunctorManagement as fm
import lib.Measurement as ms
import lib.TimeTracking as tt
import lib.Database as d
import lib.ProfileSink as sinks

import typing


def execute_with_config(runner: Runner, analyzer: A, target_config: TargetConfiguration) -> None:
  try:
    log.get_logger().log('run_setup phase.', level='debug')
    instrument = False

    # Build without any instrumentation
    vanilla_builder = B(target_config, instrument)
    tracker = tt.TimeTracker()
    tracker.m_track('Vanilla Build', vanilla_builder, 'build')

    # Run without instrumentation for baseline
    log.get_logger().log('Running baseline measurements', level='info')
    iterations = 1  # XXX Should be cmdline arg?
    vanilla_rr = runner.do_baseline_run(target_config, iterations)
    log.get_logger().log('RunResult: ' + str(vanilla_rr) + ' | avg: ' + str(vanilla_rr.get_average()), level='debug')
    instr_file = ''

    for x in range(0, 2):
      log.get_logger().log('Running instrumentation iteration ' + str(x), level='info')

      # Only run the pgoe to get the functions name
      iteration_tracker = tt.TimeTracker()

      #Analysis Phase
      instr_file = analyzer.analyze(target_config, x)
      log.get_logger().log('[WHITELIST] $' + str(x) + '$ ' + str(util.lines_in_file(instr_file)), level='perf')
      util.shell('stat ' + instr_file)

      # After baseline measurement is complete, do the instrumented build/run
      # This is only necessary in every iteration when run in compile-time mode.
      if x is 0 or target_config.is_compile_time_filtering():
        instrument = True
        instr_builder = B(target_config, instrument, instr_file)
        tracker.m_track('Instrument Build', instr_builder, 'build')

      #Run Phase
      num_repetitions = 2
      log.get_logger().log('Running profiling measurements', level='info')
      instr_rr = runner.do_profile_run(target_config, x, num_repetitions)

      # Compute overhead of instrumentation
      ovh_percentage = instr_rr.compute_overhead(vanilla_rr)
      log.get_logger().log('[RUNTIME] $' + str(x) + '$ ' + str(instr_rr.get_average()), level='perf')
      log.get_logger().log('[OVERHEAD] $' + str(x) + '$ ' + str(ovh_percentage), level='perf')

      iteration_tracker.stop()
      user_time, system_time = iteration_tracker.get_time()
      log.get_logger().log('[ITERTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

  except Exception as e:
    log.get_logger().log('Problem during preparation of run.\nMessage:\n' + str(e), level='error')
    raise RuntimeError(str(e))


def main(arguments) -> None:
  """ Main function for pira framework. Used to invoke the various components. """
  path_to_config = arguments.config
  compile_time_filter = not arguments.runtime_filter

  cf_str = 'compile-time filtering'
  if not compile_time_filter:
    cf_str = 'runtime filtering'
  log.get_logger().log(
      'Pira::main: Running PIRA in ' + cf_str + ' with configuration\n ' + str(path_to_config), level='info')

  use_extra_p = False
  if arguments.extrap_dir is not '':
    use_extra_p = True

  home_dir = util.get_cwd()
  util.set_home_dir(home_dir)

  try:
    config_loader = CLoader()
    configuration = config_loader.load_conf(path_to_config)

    if bat_sys.check_queued_job():
      # TODO: Implement
      log.get_logger().log('In this version of PIRA it is not yet implemented', level='error')
      assert (False)

    else:
      '''
      This branch is running PIRA actively on the local machine.
      It is blocking, and the user can track the progress in the terminal.
      '''
      log.get_logger().log('Running the local case')

      # The FunctorManager manages loaded functors and generates the respective names
      fm.FunctorManager(configuration)
      dbm = d.DBManager(d.DBManager.db_name + '.' + d.DBManager.db_ext)
      dbm.create_cursor()
      analyzer = A(configuration)

      # TODO: We probably want to factor out this preparation code into a factory
      attached_sink = sinks.NopSink()
      prepare_runner = LocalRunner(configuration, attached_sink)
      if use_extra_p:
        attached_sink = sinks.ExtrapProfileSink(arguments.extrap_dir, 'param', arguments.extrap_prefix, '',
                                                'profile.cubex')
        prepare_runner = LocalScalingRunner(configuration, attached_sink)

      final_runner = prepare_runner

      # A build/place is a top-level directory
      for build in configuration.get_builds():
        log.get_logger().log('Build: ' + str(build))
        app_tuple = (util.generate_random_string(), build, '', '')
        dbm.insert_data_application(app_tuple)

        # An item is a target/software in that directory
        for item in configuration.get_items(build):
          log.get_logger().log('Running for item ' + str(item))

          # A flavor is a specific version to build
          if configuration.has_local_flavors(build, item):
            for flavor in configuration.get_flavors(build, item):
              log.get_logger().log('Running for local flavor ' + flavor, level='debug')

              # prepare database, and get a unique handle for current item.
              db_item_id = dbm.prep_db_for_build_item_in_flavor(configuration, build, item, flavor)
              # Create configuration object for the item currently processed.
              t_config = TargetConfiguration(build, item, flavor, db_item_id, compile_time_filter)

              # Execute using a local runner, given the generated target description
              execute_with_config(final_runner, analyzer, t_config)

          # If global flavor
          else:
            # TODO: Implement
            log.get_logger().log('In this version of PIRA it is not yet implemented', level='error')
            assert (False)

    util.change_cwd(home_dir)

  except RuntimeError as rt_err:
    util.change_cwd(home_dir)
    log.get_logger().log('Runner.run caught exception. Message: ' + str(rt_err), level='error')
    log.get_logger().dump_tape()
