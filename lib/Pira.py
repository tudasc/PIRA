"""
File: Pira.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module implementing the main workflow of PIRA.
"""

import os
from lib.ConfigLoaderNew import ConfigurationLoader as CLoader
from lib.Configuration import TargetConfiguration, PiraConfiguration
from lib.Runner import Runner, LocalRunner
from lib.Builder import Builder as B
from lib.Analyzer import Analyzer as A
from lib.db import database as db
import lib.Logging as log
import lib.Utility as util
import lib.tables as tables
import lib.BatchSystemHelper as bat_sys
import lib.FunctorManagement as fm 
import lib.Measurement as ms
import lib.TimeTracking as tt
import lib.Database as d
import lib.ConfigLoaderNew as cln

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
   

def runner(flavor: str, build: str, benchmark: str, kwargs, config: CLoader, is_no_instrumentation_run: bool,
           iteration_number: int, itemID: str, database, cur) -> float:
  benchmark_name = config.get_benchmark_name(benchmark)
  is_for_db = False
  f_man = fm.FunctorManager(config)
  run_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'run')

  if run_functor.get_method()['active']:
    kwargs['util'] = util
    run_functor.active(benchmark, **kwargs)
    log.get_logger().log('For the active functor we cannot measure runtime', level='warn')
    return .0

  else:
    try:
      util.change_cwd(build)
      scorep_helper = ms.ScorepSystemHelper(config)
      scorep_helper._set_up(build, benchmark, flavor, iteration_number, not is_no_instrumentation_run)
      DBCubeFilePath = scorep_helper.get_data_elem('cube_dir')

      # The integer is only a bool for the database to show if no_instrumentation is set.
      if is_no_instrumentation_run:
        DBIntVal = 0
      else:
        DBIntVal = 1

      # Run the actual command
      command = run_functor.passive(benchmark, **kwargs)
      out, runtime = util.shell(command, time_invoc=True)
      # Insert into DB
      experiment_data = (util.generate_random_string(), benchmark_name, iteration_number, DBIntVal,
                           DBCubeFilePath, str(runtime), itemID)
      database.insert_data_experiment(cur, experiment_data)

      return runtime

    except Exception as e:
      log.get_logger().log(str(e), level='warn')

      raise Exception('Runner encountered problem.')


def submitter(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
              database, cur) -> None:
  benchmark_name = config.get_benchmark_name(benchmark)
  submitter_functor = util.load_functor(
      config.get_runner_func(build, benchmark), 'slurm_submitter_' + benchmark_name + '_' + flavor)
  exp_dir = config.get_analyser_exp_dir(build, benchmark)
  # TODO These functions are now part of the ScorepHelper
  DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir, flavor, iteration_number)
  util.set_scorep_exp_dir(exp_dir, flavor, iteration_number)
  util.set_overwrite_scorep_exp_dir()

  if is_no_instrumentation_run:
    DBIntVal = 0

  else:
    DBIntVal = 1
    util.set_scorep_profiling_basename(flavor, benchmark_name)

  tup = [(flavor, config.get_batch_script_func(build, benchmark))]
  kwargs = {"util": util, "runs_per_job": 1, "dependent": 0}
  job_id = submitter_functor.dispatch(tup, **kwargs)
  # TODO: Create new BatchSystemJob instance instead
  bat_sys.create_batch_queued_temp_file(job_id, benchmark_name, iteration_number, DBIntVal, DBCubeFilePath,
                                     itemID, build, benchmark, flavor)
  log.get_logger().log('Submitted job. Exiting. Re-invoke when job is finished.')
  exit(0)

def execute_with_config(runner: Runner, analyzer: A, target_config: TargetConfiguration) -> None:
  try:
    log.get_logger().log('run_setup phase.', level='debug')
    no_instrumentation = True

    # Build without any instrumentation
    vanilla_builder = B(target_config, no_instrumentation)
    tracker = tt.TimeTracker()
    tracker.m_track('Vanilla Build', vanilla_builder, 'build')

    # Run without instrumentation for baseline
    iterations = 1 # XXX Should be cmdline arg?
    vanilla_rr = runner.do_baseline_run(target_config, iterations)
    log.get_logger().log('RunResult: ' + str(vanilla_rr) + ' | avg: ' + str(vanilla_rr.get_average()), level='debug')
    instr_file = ''

    for x in range(0, 15):
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
      no_instrumentation = False
      instr_builder = B(target_config, no_instrumentation)
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
      log.get_logger().dump_tape(cli=True)

  except Exception as e:
    log.get_logger().log('Problem during preparation of run.\nMessage:\n' + str(e), level='debug')
    raise RuntimeError(str(e))


def run_detail(target_config, is_no_instrumentation_run, iteration_number) -> float:
  kwargs = {'compiler': ''}
  try:
    if config.is_submitter(build, benchmark):
      submitter(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
              database, cur)
    else:
      return runner(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
           database, cur)

  except Exception as e:
    log.get_logger().log('Unwinding')
    raise Exception('run_detail(' + str(build) + ', ' + str(benchmark) + ', ' + str(flavor) + ', ' +
                    str(is_no_instrumentation_run) + ', ' + str(iteration_number) + ', ' + str(itemID) +
                    ',...')


def main(path_to_config) -> None:
  """ Main function for pira framework. Used to invoke the various components. """

  #log.get_logger().set_state('info')
  log.get_logger().log('Running with configuration: ' + str(path_to_config))
  home_dir = util.get_cwd()

  try:
    config_loader = CLoader()
    configuration = config_loader.load_conf(path_to_config)
    configuration.initialize_stopping_iterator()
    configuration.initialize_first_iteration()
    log.get_logger().log('Loaded configuration')

    # Flow for submitter
    # FIXME: Refactor this code!
    if bat_sys.check_queued_job():
      log.get_logger().log('Running the submitter case.')
      # read file to get build, item, flavor, iteration, itemID, and runtime
      job_details = bat_sys.read_batch_queued_job()

      # get run-time of the submitted job
      runtime = bat_sys.get_runtime_of_submitted_job(job_details[JOBID])
      bat_sys.read_batch_queued_job()

      # Insert into DB
      experiment_data = (util.generate_random_string(), job_details[BENCHMARKNAME],
                         job_details[ITERATIONNUMBER], job_details[ISWITHINSTR], job_details[CUBEFILEPATH],
                         runtime, job_details[ITEMID])
      database.insert_data_experiment(db_cur, experiment_data)

      if (int(job_details[ISWITHINSTR]) == 0 and int(job_details[ITERATIONNUMBER]) < 4):

        # Build and run without any instrumentation
        vanilla_build = B(job_details[BUILDNAME], configuration)
        vanilla_build.build_no_instr = True
        vanilla_build.build(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR])

        # Run - this binary does not contain any instrumentation.
        run_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR], True,
                   int(job_details[ITERATIONNUMBER]) + 1, job_details[ITEMID], database, db_cur)

      if (int(job_details[ISWITHINSTR]) == 0 and int(job_details[ITERATIONNUMBER]) == 4):
        analyser_dir = configuration.get_analyser_dir(job_details[BUILDNAME], job_details[ITEM])
        # Remove anything in the output dir of the analysis tool
        util.remove_from_pgoe_out_dir(analyser_dir)

        # Generate white-list functions
        analyser = A(configuration, job_details[BUILDNAME], job_details[ITEM])
        analyser.analyse_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR],
                                0)

        builder = B(job_details[BUILDNAME], configuration)
        builder.build(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR])
        run_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR], False, 0,
                   job_details[ITEMID], database, db_cur)

      if (int(job_details[ISWITHINSTR]) == 1):
        analyser = A(configuration, job_details[BUILDNAME], job_details[ITEM])
        analyser.analyse_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR],
                                int(job_details[ITERATIONNUMBER]))

        builder = B(job_details[BUILDNAME], configuration)
        builder.build(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR])

        # Run Phase
        run_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR], False,
                   int(job_details[ITERATIONNUMBER]) + 1, job_details[ITEMID], database, db_cur)
    else:
      '''
      This is running PIRA actively on the local machine.
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
            '''
            FIXME So far no db_item_id generated for global flavor items
            '''
            for flavor in configuration.global_flavors:
              run_setup(configuration, build, item, flavor, db_item_id, database, db_cur)
    util.change_cwd(home_dir)

  except RuntimeError as rt_err:
    util.change_cwd(home_dir)
    log.get_logger().log(
        'Runner.run caught exception. Message: ' + str(rt_err), level='warn')
    log.get_logger().dump_tape()
