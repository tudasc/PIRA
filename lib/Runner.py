from ConfigLoaderNew import ConfigurationLoader as Conf
from Builder import Builder as B
from Analyzer import Analyzer as A
import Logging as log
import Utility as util
import Logging as logging
from lib.db import database as db
import lib.tables as tables

# Some contants to manage slurm submitter tmp file read
JOBID = 0
BENCHMARKNAME = 1
ITERATIONNUMBER = 2
ISWITHINSTR = 3
CUBEFILEPATH = 4
ITEMID = 5
BUILDNAME = 6
ITEM = 7
FLAVOR = 8


def runner(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
           database, cur):
  benchmark_name = config.get_benchmark_name(benchmark)
  is_for_db = False
  build_functor = util.load_functor(
      config.get_runner_func(build, benchmark),
      util.build_runner_functor_filename(is_for_db, benchmark_name[0], flavor))

  if build_functor.get_method()['active']:
    kwargs['util'] = util
    build_functor.active(benchmark, **kwargs)

  else:
    try:
      command = build_functor.passive(benchmark, **kwargs)
      util.change_cwd(benchmark)
      exp_dir = config.get_analyser_exp_dir(build, benchmark)
      log.get_logger().log('Retrieved analyser experiment directory: ' + exp_dir, level='debug')

      if is_no_instrumentation_run:
        DBIntVal = 0
        DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir, flavor, iteration_number,
                                                          is_no_instrumentation_run)
        util.set_scorep_exp_dir(exp_dir, flavor, iteration_number, is_no_instrumentation_run)
        util.set_overwrite_scorep_exp_dir()

      else:
        DBIntVal = 1
        DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir, flavor, iteration_number,
                                                          is_no_instrumentation_run)
        util.set_scorep_exp_dir(exp_dir, flavor, iteration_number, is_no_instrumentation_run)
        util.set_overwrite_scorep_exp_dir()
        util.set_scorep_profiling_basename(flavor, benchmark_name[0])

      # Run the actual command
      runTime = util.shell(command)
      # Insert into DB
      experiment_data = (util.generate_random_string(), benchmark_name[0], iteration_number, DBIntVal,
                           DBCubeFilePath, str(runTime), itemID)
      database.insert_data_experiment(cur, experiment_data)

    except Exception as e:
      logging.get_logger().log(e.message, level='warn')


def submitter(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
              database, cur):
  benchmark_name = config.get_benchmark_name(benchmark)
  submitter_functor = util.load_functor(
      config.get_runner_func(build, benchmark), 'slurm_submitter_' + benchmark_name[0] + '_' + flavor)
  exp_dir = config.get_analyser_exp_dir(build, benchmark)

  if is_no_instrumentation_run:
    DBIntVal = 0
    DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir, flavor, iteration_number,
                                                      is_no_instrumentation_run)
    util.set_scorep_exp_dir(exp_dir, flavor, iteration_number, is_no_instrumentation_run)
    util.set_overwrite_scorep_exp_dir()

  else:
    DBIntVal = 1
    DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir, flavor, iteration_number,
                                                      is_no_instrumentation_run)
    util.set_scorep_exp_dir(exp_dir, flavor, iteration_number, is_no_instrumentation_run)
    util.set_overwrite_scorep_exp_dir()
    util.set_scorep_profiling_basename(flavor, benchmark_name[0])

  tup = [(flavor, config.get_batch_script_func(build, benchmark))]
  kwargs = {"util": util, "runs_per_job": 1, "dependent": 0}
  job_id = submitter_functor.dispatch(tup, **kwargs)
  util.create_batch_queued_temp_file(job_id, benchmark_name[0], iteration_number, DBIntVal, DBCubeFilePath,
                                     itemID, build, benchmark, flavor)
  log.get_logger().log('Submitted job. Exiting. Re-invoke when job is finished.')
  exit(0)


def run_detail(config, build, benchmark, flavor, is_no_instrumentation_run, iteration_number, itemID, database,
               cur):
  kwargs = {'compiler': ''}

  if config.get_is_submitter(build, benchmark):
    submitter(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
              database, cur)
  else:
    runner(flavor, build, benchmark, kwargs, config, is_no_instrumentation_run, iteration_number, itemID,
           database, cur)


def run_setup(configuration, build, item, flavor, itemID, database, cur):
  for x in range(0, 5):
    no_instrumentation = True
    # Only run the pgoe to get the functions name
    if (configuration.is_first_iteration[build + item + flavor] == False):
      configuration.is_first_iteration[build + item + flavor] = True

      # Build and run without any instrumentation
      BuildNoInstr = B(build, configuration)
      BuildNoInstr.build_no_instr = True
      BuildNoInstr.build(configuration, build, item, flavor)

      log.get_logger().log('Running the baseline binary.')
      # Run - this binary does not contain any instrumentation.
      for y in range(0, 5):
        run_detail(configuration, build, item, flavor, no_instrumentation, y, itemID, database, cur)

      analyser_dir = configuration.get_analyser_dir(build, item)
      #Remove anything in the output dir of the analysis tool

      util.remove_from_pgoe_out_dir(analyser_dir)

      analyser = A(configuration, build, item)
      analyser.analyse_detail(configuration, build, item, flavor, y)

    builder = B(build, configuration)
    builder.build(configuration, build, item, flavor)

    #Run Phase
    no_instrumentation = False
    run_detail(configuration, build, item, flavor, no_instrumentation, x, itemID, database, cur)

    #Analysis Phase
    analyser = A(configuration, build, item)
    analyser.analyse_detail(configuration, build, item, flavor, x)


def run(path_to_config):
  log.get_logger().set_state('info')
  log.get_logger().log('Running with configuration: ' + str(path_to_config))

  try:
    config_loader = Conf()
    configuration = config_loader.load_conf(path_to_config)
    configuration.initialize_stopping_iterator()
    configuration.initialize_first_iteration()
    log.get_logger().log('Loaded configuration')
    '''
        Initialize Database
    '''
    database = db("BenchPressDB")
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
    if util.check_queued_job():
      log.get_logger().log('Running the submitter case.')
      # read file to get build, item, flavor, iteration, itemID, and runtime
      job_details = util.read_batch_queued_job()

      # get run-time of the submitted job
      runtime = util.get_runtime_of_submitted_job(job_details[JOBID])
      util.read_batch_queued_job()

      # Insert into DB
      experiment_data = (util.generate_random_string(), job_details[BENCHMARKNAME],
                         job_details[ITERATIONNUMBER], job_details[ISWITHINSTR], job_details[CUBEFILEPATH],
                         runtime, job_details[ITEMID])
      database.insert_data_experiment(cur, experiment_data)

      if (int(job_details[ISWITHINSTR]) == 0 and int(job_details[ITERATIONNUMBER]) < 4):

        # Build and run without any instrumentation
        BuildNoInstr = B(job_details[BUILDNAME], configuration)
        BuildNoInstr.build_no_instr = True
        BuildNoInstr.build(configuration, job_details[BUILDNAME], job_details[ITEM], job_details[FLAVOR])

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

      for build in configuration.builds:
        application = (util.generate_random_string(), build, '', '')
        database.insert_data_application(cur, application)

      for item in configuration.builds[build]['items']:
        log.get_logger().print_info('Running for item ' + str(item))

        if configuration.builds[build]['flavours']:
          log.get_logger().log('Using locally defined flavors', level='debug')

          for flavor in configuration.builds[build]['flavours']:
            log.get_logger().log('Running for local flavor ' + flavor, level='debug')

            dbbuild = (util.generate_random_string(), build, '', flavor, build)
            database.insert_data_builds(cur, dbbuild)

            # Insert into DB the benchmark data
            benchmark_name = configuration.get_benchmark_name(item)
            itemID = util.generate_random_string()
            analyse_functor = configuration.get_analyse_func(
                build, item) + util.build_analyse_functor_filename(True, benchmark_name[0], flavor)
            build_functor = configuration.get_flavor_func(build, item) + util.build_builder_functor_filename(
                True, False, benchmark_name[0], flavor)
            run_functor = configuration.get_runner_func(build, item) + util.build_runner_functor_filename(
                True, benchmark_name[0], flavor)
            submitter_functor = configuration.get_runner_func(
                build, item) + '/slurm_submitter_' + benchmark_name[0] + flavor
            exp_dir = configuration.get_analyser_exp_dir(build, item)
            itemDBData = (itemID, benchmark_name[0], analyse_functor, build_functor, '', run_functor,
                          submitter_functor, exp_dir, build)
            database.insert_data_items(cur, itemDBData)

            run_setup(configuration, build, item, flavor, itemID, database, cur)

        # If global flavor
        else:
          for flavor in configuration.global_flavors:
            run_setup(configuration, build, item, flavor, itemID, database, cur)
    log.get_logger().dump_tape('/home/j_lehr/all_repos/tape.log')

  except StandardError as se:
    log.get_logger().log(
        'Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message, level='warn')
    log.get_logger().dump_tape('/home/j_lehr/all_repos/tape.log')
    log.get_logger().dump_tape()
