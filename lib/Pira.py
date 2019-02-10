"""
File: Pira.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module implementing the main workflow of PIRA.
"""

from lib.ConfigLoaderNew import ConfigurationLoader as CLoader
from lib.Configuration import TargetConfiguration, PiraConfiguration
from lib.Runner import Runner, LocalRunner
from lib.Builder import Builder as B
from lib.Analyzer import Analyzer as A
import lib.Logging as log
import lib.Utility as util
import lib.BatchSystemHelper as bat_sys
import lib.FunctorManagement as fm 
import lib.Measurement as ms
import lib.TimeTracking as tt
import lib.Database as d

import typing

# Contants to manage slurm submitter tmp file read
JOBID = 0
BENCHMARKNAME = 1
ITERATIONNUMBER = 2
ISWITHINSTR = 3
CUBEFILEPATH = 4
ITEMID = 5
BUILDNAME = 6
ITEM = 7
FLAVOR = 8


def execute_with_config(runner: Runner, analyzer: A, target_config: TargetConfiguration) -> None:
  try:
    log.get_logger().log('run_setup phase.', level='debug')
    no_instrumentation = False

    # Build without any instrumentation
    vanilla_builder = B(target_config, no_instrumentation)
    tracker = tt.TimeTracker()
    tracker.m_track('Vanilla Build', vanilla_builder, 'build')

    # Run without instrumentation for baseline
    iterations = 1 # XXX Should be cmdline arg?
    vanilla_rr = runner.do_baseline_run(target_config, iterations)
    log.get_logger().log('RunResult: ' + str(vanilla_rr) + ' | avg: ' + str(vanilla_rr.get_average()), level='debug')
    instr_file = ''

    for x in range(0, 2):
      log.get_logger().toggle_state('info')
      log.get_logger().log('Running instrumentation iteration ' + str(x), level='info')
      log.get_logger().toggle_state('info')

      # Only run the pgoe to get the functions name
      log.get_logger().log('Starting with the profiler run', level='debug')
      iteration_tracker = tt.TimeTracker()

      #Analysis Phase
      instr_file = analyzer.analyze(target_config, x)
      log.get_logger().log('[WHITELIST] $' + str(x) + '$ ' + str(util.lines_in_file(instr_file)), level='perf')
      util.shell('stat ' + instr_file)

      # After baseline measurement is complete, do the instrumented build/run
      no_instrumentation = True
      instr_builder = B(target_config, no_instrumentation, instr_file)
      tracker.m_track('Instrument Build', instr_builder, 'build')

      #Run Phase
      instr_rr = runner.do_profile_run(target_config, x)

      # Compute overhead of instrumentation
      ovh_percentage = instr_rr.compute_overhead(vanilla_rr)
      log.get_logger().log('[RUNTIME] $' + str(x) + '$ ' + str(instr_rr.get_average()), level='perf')
      log.get_logger().log('[OVERHEAD] $' + str(x) + '$ ' + str(ovh_percentage), level='perf')

      iteration_tracker.stop()
      user_time, system_time = iteration_tracker.get_time()
      log.get_logger().log('[ITERTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

  except Exception as e:
    log.get_logger().log('Problem during preparation of run.\nMessage:\n' + str(e), level='debug')
    raise RuntimeError(str(e))


def main(path_to_config: str) -> None:
  """ Main function for pira framework. Used to invoke the various components. """

  log.get_logger().log('Pira::main: Running PIRA with configuration\n ' + str(path_to_config), level='info')
  home_dir = util.get_cwd()

  try:
    config_loader = CLoader()
    configuration = config_loader.load_conf(path_to_config)
    
    if bat_sys.check_queued_job():
      # TODO: Implement
      assert(False)

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
      runner = LocalRunner(configuration)

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
              t_config = TargetConfiguration(build, item, flavor, db_item_id)

              # Execute using a local runner, given the generated target description
              execute_with_config(runner, analyzer, t_config)

          # If global flavor
          else:
            # TODO: Implement
            assert(False)

    util.change_cwd(home_dir)

  except RuntimeError as rt_err:
    util.change_cwd(home_dir)
    log.get_logger().log(
        'Runner.run caught exception. Message: ' + str(rt_err), level='warn')
    log.get_logger().dump_tape()
