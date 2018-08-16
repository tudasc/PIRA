import os
from lib.ConfigLoaderNew import ConfigurationLoader as CLoader
from lib.Builder import Builder as B
from lib.Analyzer import Analyzer as A
from lib.db import database as db
import lib.Logging as log
import lib.Utility as util
import lib.tables as tables
import lib.BatchSystemHelper as bat_sys
import lib.FunctorManagement as fm
import lib.MeasurementSystem as ms

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
      scorep_helper.set_up(build, benchmark, flavor, iteration_number, not is_no_instrumentation_run)
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

def run_streamline(configuration, build, item, flavor, itemID, database, cur) -> None:
  try:
    log.get_logger().log('run_setup phase.', level='debug')
    log.get_logger().dump_tape(cli=True)
    no_instrumentation = True
    configuration.is_first_iteration[build + item + flavor] = True
    # Build and run without any instrumentation
    vanilla_build = B(build, configuration, no_instrumentation)
    vanilla_build.build(configuration, build, item, flavor)

    log.get_logger().log('Running the baseline binary.')
    accu_runtime = .0
    num_vanilla_repetitions = 1
    # Baseline run. TODO Better evaluation of the obtained timings.
    for y in range(0, num_vanilla_repetitions):
      accu_runtime += run_detail(configuration, build, item, flavor, no_instrumentation, y, itemID, database, cur)

    vanilla_avg_rt = accu_runtime / num_vanilla_repetitions
    log.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(vanilla_avg_rt), level='perf')

    analyser_dir = configuration.get_analyser_dir(build, item)
    util.remove_from_pgoe_out_dir(analyser_dir)

#    analyser = A(configuration, build, item)
#    instr_file = analyser.analyse_detail(configuration, build, item, flavor, y)
#    log.get_logger().log('[WHITELIST] $0$ ' + str(util.lines_in_file(instr_file)), level='perf')
    
    #configuration.is_first_iteration[build + item + flavor] = True
    for x in range(0, 5):
      log.get_logger().toggle_state('info')
      log.get_logger().log('Running iteration ' + str(x), level='info')
      log.get_logger().toggle_state('info')
      instr_file = ''
      # Only run the pgoe to get the functions name
      log.get_logger().log('Starting with the profiler run', level='debug')
      iteration_timer_start = os.times()
      
      #Analysis Phase
      analyser = A(configuration, build, item)
      instr_file = analyser.analyse_detail(configuration, build, item, flavor, x)
      log.get_logger().log('[WHITELIST] $' + str(x) + '$ ' + str(util.lines_in_file(instr_file)), level='perf')
      
      # After baseline measurement is complete, do the instrumented build/run
      no_instrumentation = False
      builder = B(build, configuration, no_instrumentation)
      builder_timer_start = os.times()
      builder.build(configuration, build, item, flavor)
      builder_timer_stop = os.times()
      user_time = builder_timer_stop[2] - builder_timer_start[2]
      system_time = builder_timer_stop[3] - builder_timer_start[3]
      log.get_logger().log('[BUILDTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

      #Run Phase
      instr_rt = run_detail(configuration, build, item, flavor, no_instrumentation, x, itemID, database, cur)

      # Compute overhead of instrumentation
      ovh_percentage = instr_rt / vanilla_avg_rt
      log.get_logger().log('[RUNTIME] $' + str(x) + '$ ' + str(instr_rt), level='perf')
      log.get_logger().log('[OVERHEAD] $' + str(x) + '$ ' + str(ovh_percentage), level='perf')

      iteration_timer_stop = os.times()
      user_time = iteration_timer_stop[2] - iteration_timer_start[2]
      system_time = iteration_timer_stop[3] - iteration_timer_start[3]
      log.get_logger().log('[ITERTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')
      log.get_logger().dump_tape(cli=True)

  except Exception as e:
    log.get_logger().log('run_setup problem', level='debug')
    raise RuntimeError(str(e))


def run_detail(config, build, benchmark, flavor, is_no_instrumentation_run, iteration_number, itemID, database,
    cur) -> float:
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


def run_setup(configuration, build, item, flavor, itemID, database, cur) -> None:
  try:
    log.get_logger().log('run_setup phase.', level='debug')
    for x in range(0, 5):
      log.get_logger().toggle_state('info')
      log.get_logger().log('Running iteration ' + str(x), level='info')
      log.get_logger().toggle_state('info')
      no_instrumentation = True
      instr_file = ''
      # Only run the pgoe to get the functions name
      if (configuration.is_first_iteration[build + item + flavor] == False):
        configuration.is_first_iteration[build + item + flavor] = True

        # Build and run without any instrumentation
        vanilla_build = B(build, configuration, no_instrumentation)
        vanilla_build.build(configuration, build, item, flavor)

        log.get_logger().log('Running the baseline binary.')
        accu_runtime = .0
        num_vanilla_repetitions = 1
        # Baseline run. TODO Better evaluation of the obtained timings.
        for y in range(0, num_vanilla_repetitions):
          accu_runtime += run_detail(configuration, build, item, flavor, no_instrumentation, y, itemID, database, cur)

        vanilla_avg_rt = accu_runtime / num_vanilla_repetitions
        log.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(vanilla_avg_rt), level='perf')

        analyser_dir = configuration.get_analyser_dir(build, item)
        util.remove_from_pgoe_out_dir(analyser_dir)

        analyser = A(configuration, build, item)
        instr_file = analyser.analyse_detail(configuration, build, item, flavor, y)
        log.get_logger().log('[WHITELIST] $' + str(x) + '$ ' + str(util.lines_in_file(instr_file)), level='perf')

      log.get_logger().log('Starting with the profiler run', level='debug')
      iteration_timer_start = os.times()
      # After baseline measurement is complete, do the instrumented build/run
      no_instrumentation = False
      builder = B(build, configuration, no_instrumentation)
      builder_timer_start = os.times()
      builder.build(configuration, build, item, flavor)
      builder_timer_stop = os.times()
      user_time = builder_timer_stop[2] - builder_timer_start[2]
      system_time = builder_timer_stop[3] - builder_timer_start[3]
      log.get_logger().log('[BUILDTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

      #Run Phase
      instr_rt = run_detail(configuration, build, item, flavor, no_instrumentation, x, itemID, database, cur)

      # Compute overhead of instrumentation
      ovh_percentage = instr_rt / vanilla_avg_rt
      log.get_logger().log('[OVERHEAD] $' + str(x) + '$ ' + str(ovh_percentage), level='perf')

      #Analysis Phase
      analyser = A(configuration, build, item)
      instr_file = analyser.analyse_detail(configuration, build, item, flavor, x)
      log.get_logger().log('[WHITELIST] $' + str(x) + '$ ' + str(util.lines_in_file(instr_file)), level='perf')
      iteration_timer_stop = os.times()
      user_time = iteration_timer_stop[2] - iteration_timer_start[2]
      system_time = iteration_timer_stop[3] - iteration_timer_start[3]
      log.get_logger().log('[ITERTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

  except Exception as e:
    log.get_logger().log('run_setup problem', level='debug')
    raise RuntimeError(str(e))


def run(path_to_config) -> None:
  #log.get_logger().set_state('info')
  log.get_logger().log('Running with configuration: ' + str(path_to_config))
  home_dir = util.get_cwd()

  try:
    config_loader = CLoader()
    configuration = config_loader.load_conf(path_to_config)
    configuration.initialize_stopping_iterator()
    configuration.initialize_first_iteration()
    log.get_logger().log('Loaded configuration')
    '''
        Initialize Database
    '''
    database = db("BenchPressDB.sqlite")
    cur = database.create_cursor(database.conn)
    '''
       Create tables if not exists
    '''
    database.create_table(cur, tables.sql_create_application_table)
    database.create_table(cur, tables.sql_create_builds_table)
    database.create_table(cur, tables.sql_create_items_table)
    database.create_table(cur, tables.sql_create_experiment_table)
    log.get_logger().log('Created necessary tables in database')

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
      database.insert_data_experiment(cur, experiment_data)

      if (int(job_details[ISWITHINSTR]) == 0 and int(job_details[ITERATIONNUMBER]) < 4):

        # Build and run without any instrumentation
        vanilla_build = B(job_details[BUILDNAME], configuration)
        vanilla_build.build_no_instr = True
        vanilla_build.build(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR])

        # Run - this binary does not contain any instrumentation.
        run_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR], True,
                   int(job_details[ITERATIONNUMBER]) + 1, job_details[ITEMID], database, cur)

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
                   job_details[ITEMID], database, cur)

      if (int(job_details[ISWITHINSTR]) == 1):
        analyser = A(configuration, job_details[BUILDNAME], job_details[ITEM])
        analyser.analyse_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR],
                                int(job_details[ITERATIONNUMBER]))

        builder = B(job_details[BUILDNAME], configuration)
        builder.build(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR])

        # Run Phase
        run_detail(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR], False,
                   int(job_details[ITERATIONNUMBER]) + 1, job_details[ITEMID], database, cur)
    else:
      log.get_logger().log('Running the local case')

      for build in configuration.get_builds():
        log.get_logger().log('Build: ' + str(build))
        application = (util.generate_random_string(), build, '', '')
        database.insert_data_application(cur, application)

      for item in configuration.get_items(build):
        log.get_logger().log('Running for item ' + str(item))

        if configuration.has_local_flavors(build, item):
          for flavor in configuration.get_flavors(build, item):
            log.get_logger().log('Running for local flavor ' + flavor, level='debug')

            dbbuild = (util.generate_random_string(), build, '', flavor, build)
            database.insert_data_builds(cur, dbbuild)

            # Insert into DB the benchmark data
            benchmark_name = configuration.get_benchmark_name(item)
            log.get_logger().log('benchmark_name: ' + benchmark_name, level='debug')
            # The FunctorManager manages loaded functors and generates the respective names
            func_manager = fm.FunctorManager(configuration)

            # XXX My implementation returns the full path, including the file extension.
            #     In case something in the database goes wild, this could be it.
            analyse_functor = func_manager.get_analyzer_file(build, item, flavor)
            build_functor = func_manager.get_builder_file(build, item, flavor)
            run_functor = func_manager.get_runner_file(build, item, flavor)
            # TODO implement the get_submitter_file(build, item, flavor) method!

            submitter_functor = configuration.get_runner_func(
                build, item) + '/slurm_submitter_' + benchmark_name + flavor
            exp_dir = configuration.get_analyser_exp_dir(build, item)

            itemID = util.generate_random_string()
            itemDBData = (itemID, benchmark_name, analyse_functor, build_functor, '', run_functor,
                          submitter_functor, exp_dir, build)
            database.insert_data_items(cur, itemDBData)

            #run_setup(configuration, build, item, flavor, itemID, database, cur)
            run_streamline(configuration, build, item, flavor, itemID, database, cur)

        # If global flavor
        else:
          for flavor in configuration.global_flavors:
            run_setup(configuration, build, item, flavor, itemID, database, cur)
    util.change_cwd(home_dir)

  except RuntimeError as rt_err:
    util.change_cwd(home_dir)
    log.get_logger().log(
        'Runner.run caught exception. Message: ' + str(rt_err), level='warn')
    log.get_logger().dump_tape()
