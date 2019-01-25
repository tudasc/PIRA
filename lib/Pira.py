import os
from lib.ConfigLoaderNew import ConfigurationLoader as CLoader
from lib.ConfigLoaderNew import TargetConfiguration as TargetConfiguration
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

class Runner:
  pass


class LocalRunner(Runner):

  """This is the new runner class. It implements the original idea of the entity being responsible for executing the target.
  TODO: Move this class to its own file, once it is working.
  """
  class InstrumentConfig:
    def __init__(self, is_instrumentation_run=False, instrumentation_iteration=None):
      self._is_instrumentation_run = is_instrumentation_run
      self._instrumentation_iteration = instrumentation_iteration
    
    def get_instrumentation_iteration(self):
      return self._instrumentation_iteration
    
    def is_instrumentation_run(self):
      return self._is_instrumentation_run
    
  def __init__(self, configuration: cln.PiraConfiguration):
    self._config = configuration
  
  def run(self, target_config: TargetConfiguration, instrument_config: InstrumentConfig):
    benchmark_name = cln.PiraConfiguration.get_benchmark_name(target_config.get_target())
    functor_manager = fm.FunctorManager()
    run_functor = functor_manager.get_or_load_functor(target_config.get_build(), target_config.get_target(), target_config.get_flavor(), 'run')
    kwargs = {}

    if run_functor.get_method()['active']:
      kwargs['util'] = util
      run_functor.active(target_config.get_target(), **kwargs)
      log.get_logger().log('For the active functor we can barely measure runtime', level='warn')
      return .0
    
    try:
      util.change_cwd(target_config.get_build())
      scorep_helper = ms.ScorepSystemHelper(self._config)
      scorep_helper.set_up(target_config, instrument_config)
      command = run_functor.passive(target_config.get_target(), **kwargs)
      _, runtime = util.shell(command, time_invoc=True)
      return runtime
    
    except Exception as e:
      log.get_logger().log('Problem in LocalRunner::run\n' + str(e))


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
    return self.run(target_config, LocalRunner.InstrumentConfig(True, instr_iteration))
    

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


def do_baseline_run(target_config, iterations):
  """Executes the vanilla binary for a specific number of times and returns a dict with the timings gathered.

  :configuration: The PIRA configuration
  :build: Current top-level build
  :item: TODO
  :flavor: TODO
  :iteration: TODO
  :db_item_id: TODO
  :returns: TODO

  """
  log.get_logger().log('Running the baseline binary.')
  accu_runtime = .0
  num_vanilla_repetitions = iterations # XXX This should be a command line argument?
  no_instrumentation = True
  # Baseline run. TODO Better evaluation of the obtained timings.
  for y in range(0, num_vanilla_repetitions):
    accu_runtime += run_detail(target_config, no_instrumentation, y)

  vanilla_avg_rt = accu_runtime / num_vanilla_repetitions
  log.get_logger().log('[Vanilla][RUNTIME] Vanilla avg: ' + str(vanilla_avg_rt), level='perf')

  return ms.RunResult(accu_runtime, iterations, vanilla_avg_rt)


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
    run_result = runner.do_baseline_run(target_config, iterations)
    vanilla_avg_rt = run_result.get_average()
    log.get_logger().log('RunResult: ' + str(run_result) + ' | avg: ' + str(run_result.get_average()), level='debug')
    instr_file = ''

    for x in range(0, 15):
      log.get_logger().toggle_state('info')
      log.get_logger().log('Running iteration ' + str(x), level='info')
      log.get_logger().toggle_state('info')

      # Only run the pgoe to get the functions name
      log.get_logger().log('Starting with the profiler run', level='debug')
      iteration_timer_start = os.times()

      #Analysis Phase
      instr_file = analyzer.analyze(target_config, x)
      log.get_logger().log('[WHITELIST] $' + str(x) + '$ ' + str(util.lines_in_file(instr_file)), level='perf')
      util.shell('stat ' + instr_file)

      # After baseline measurement is complete, do the instrumented build/run
      no_instrumentation = False
      instr_builder = B(target_config, no_instrumentation)
      tracker.m_track('Instrument Build', instr_builder, 'build')

      #Run Phase
      instr_rt = runner.do_profile_run(target_config, x)
      #instr_rt = run_detail(configuration, build, item, flavor, no_instrumentation, x, itemID, database, cur)

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
    log.get_logger().log('Problem during preparation of run.\nMessage:\n' + str(e), level='debug')
    raise RuntimeError(str(e))

def run_streamline(configuration, build, item, flavor, itemID, database, cur) -> None:
  try:
    log.get_logger().log('run_setup phase.', level='debug')
    log.get_logger().dump_tape(cli=True)
    no_instrumentation = True
    # XXX Let's see if this code is unnecessary
    #configuration.is_first_iteration[build + item + flavor] = no_instrumentation

    # Build and run without any instrumentation
    vanilla_builder = B(build, configuration, no_instrumentation)

    tracker = tt.TimeTracker()
    tracker.m_track('Vanilla Build', vanilla_builder, 'build', configuration, build, item, flavor)
    # vanilla_build.build(configuration, build, item, flavor)

    # XXX This should eventually be part of a Runner class.
    do_baseline_run(configuration, build, item, flavor, num_vanilla_repetitions, db_item_id)

    analyser_dir = configuration.get_analyser_dir(build, item)
    util.remove_from_pgoe_out_dir(analyser_dir)

    #    analyser = A(configuration, build, item)
    #    instr_file = analyser.analyse_detail(configuration, build, item, flavor, y)
    #    log.get_logger().log('[WHITELIST] $0$ ' + str(util.lines_in_file(instr_file)), level='perf')

    #configuration.is_first_iteration[build + item + flavor] = True
    for x in range(0, 15):
      run_cfg = ms.RunConfiguration(x, True, db_item_id)

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
      util.shell('stat ' + instr_file)

      # After baseline measurement is complete, do the instrumented build/run
      no_instrumentation = False
      builder = B(build, configuration, no_instrumentation)
      tracker.m_track('Instrument Build', builder, 'build', configuration, build, item, flavor)
      #      builder_timer_start = os.times()
      #      builder.build(configuration, build, item, flavor)
      #      builder_timer_stop = os.times()
      #      user_time = builder_timer_stop[2] - builder_timer_start[2]
      #      system_time = builder_timer_stop[3] - builder_timer_start[3]
      #      log.get_logger().log('[BUILDTIME] $' + str(x) + '$ ' + str(user_time) + ', ' + str(system_time), level='perf')

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
    '''
        Initialize Database
    '''
    #database = db("BenchPressDB.sqlite")
    #db_cur = database.create_cursor(database.conn)
    '''
       Create tables if not exists
    '''
    #database.create_table(db_cur, tables.sql_create_application_table)
    #database.create_table(db_cur, tables.sql_create_builds_table)
    #database.create_table(db_cur, tables.sql_create_items_table)
    #database.create_table(db_cur, tables.sql_create_experiment_table)
    #log.get_logger().log('Created necessary tables in database')

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
      func_manager = fm.FunctorManager(configuration)
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
          benchmark_name = cln.PiraConfiguration.get_benchmark_name(item)
          log.get_logger().log('benchmark_name: ' + benchmark_name, level='debug')

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
