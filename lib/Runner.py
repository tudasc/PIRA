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
                exp_dir = config.get_analyser_exp_dir(build,benchmark)
                isdirectory_good = util.check_provided_directory(exp_dir)
                if(isdirectory_good):
                    if(util.check_file(exp_dir+"profile.cubex")):
                        benchmark_name = config.get_benchmark_name(benchmark)
                        util.rename(exp_dir+"profile.cubex",exp_dir+flavor+'-'+benchmark_name[0]+".cubex")

                #command = '/home/sachin/MasterThesis/GameOfLife/serial_non_template/gol'
                #util.shell(command)

            except Exception as e:
                logging.get_logger().log(e.message, level='warn')

def submitter(flavors,build,benchmark,kwargs,config):
    print('In submitter');
    for flavor in flavors:
        submitter_functor = util.load_functor(config.get_runner_func(build,benchmark),'slurm_submitter_'+flavor)
        tup = [(flavor,'/home/sm49xeji/job.sh')]
        kwargs={"util":util,"runs_per_job":1,"dependent":0}
        submitter_functor.dispatch(tup,**kwargs)
        print(submitter_functor)
        #exit(0)


def run_detail(config,build,benchmark):
    kwargs = {'compiler': ''}

    if config.builds[build]['flavours']:
        if config.get_is_submitter(build,benchmark):
            submitter(config.builds[build]['flavours'],build,benchmark,kwargs,config);
        else:
            runner(config.builds[build]['flavours'],build,benchmark,kwargs,config)

    else:
        if config.get_is_submitter(build,benchmark):
            submitter(config.builds[build]['flavours'],build,benchmark,kwargs,config);
        else:
            runner(config.global_flavors,build,benchmark,kwargs,config)

def run(path_to_config):
    try:
        config_loader = Conf()
        configuration = config_loader.load_conf(path_to_config)
        configuration.initialize_stopping_iterator()
        configuration.initialize_first_iteration()

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

        for build in configuration.builds:
            for item in configuration.builds[build]['items']:
                for flavor in configuration.builds[build]['flavours']:
                    while configuration.stop_iteration[build+item+flavor] == False:

                        #Check if its the first iteration
                        if configuration.builds[build]['flavours']:
                            for benchmark in configuration.builds[build]['items']:
                                #Only run the pgoe to get the functions name
                                if(configuration.is_first_iteration[build+item+flavor] == False):
                                    configuration.is_first_iteration[build+item+flavor]=True
                                    analyser = A(configuration,build,benchmark)
                                    analyser.analyse_detail(configuration,build,benchmark)

                        builder = B(build, configuration)
                        builder.build()

                        if configuration.builds[build]['flavours']:
                            for benchmark in configuration.builds[build]['items']:
                    #Run Phase
                                run_detail(configuration,build,benchmark)

                    #Analysis Phase
                                analyser = A(configuration,build,benchmark)
                                analyser.analyse_detail(configuration,build,benchmark)

            log.get_logger().dump_tape()

    except StandardError as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
