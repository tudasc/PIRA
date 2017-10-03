from ConfigLoader import ConfigurationLoader as CL
from ConfigLoaderNew import ConfigurationLoader as Conf
from Builder import Builder as B
from Analyzer import Analyzer as A
import Logging as log
import Utility as util
import Logging as logging
from lib.db import database as db
import lib.tables as tables


def runner(flavors,build,benchmark,kwargs,config):
    for flavor in flavors:
        build_functor = util.load_functor(config.get_runner_func(build,benchmark),'runner_'+flavor)
        if build_functor.get_method()['active']:
            build_functor.active(benchmark, **kwargs)

        else:
            try:
                command = build_functor.passive(benchmark, **kwargs)
                util.change_cwd(benchmark)
                util.shell(command)
                #command = '/home/sachin/MasterThesis/GameOfLife/serial_non_template/gol'
                #util.shell(command)

            except Exception as e:
                logging.get_logger().log(e.message, level='warn')

def submitter():
    pass

def run_detail(config,build,benchmark):
    kwargs = {'compiler': ''}

    if config.builds[build]['flavours']:
        runner(config.builds[build]['flavours'],build,benchmark,kwargs,config)

    else:
        runner(config.global_flavors,build,benchmark,kwargs,config)

def run(path_to_config):
    try:
        config_loader = Conf()
        configuration = config_loader.load_conf(path_to_config)

        '''
        Initialize Database
        '''
        database = db("db_file1")
        cur = database.create_cursor(database.conn)

        '''
        Create tables
        '''
        database.create_table(cur,tables.sql_create_application_table)
        database.create_table(cur,tables.sql_create_builds_table)
        database.create_table(cur,tables.sql_create_items_table)
        database.create_table(cur,tables.sql_create_experiment_table)
        #top_level_directories = configuration.get_directories()

        '''
        insert to application table
        '''
        if ((configuration.global_flavors.__len__() == 0) and (configuration.global_submitter.__len__() == 0)):
            application = ("GameofLife",'','')
            database.insert_data_application(cur,application)

        for directory in configuration.directories:
            builder = B(directory, configuration)

            builder.build()
            if configuration.builds[directory]['flavours']:
                for benchmark in configuration.builds[directory]['items']:
                    run_detail(configuration,directory,benchmark)
                    analyser = A(configuration,directory,benchmark)
                    analyser.analyse_detail(configuration,directory,benchmark)

        #write analysis phase

            #run_configs = builder.generate_run_configurations()

            #run_dispatcher = configuration.get_submitter()

            # TODO Make these configuration options configurable (cli and .json)
            #runs_per_job = configuration.get_num_runs_per_job()
            #kwargs = {'util': util, 'runs_per_job': runs_per_job, 'dependent': True}
            #run_dispatcher.dispatch(run_configs, **kwargs)


            log.get_logger().dump_tape()

    except StandardError as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
