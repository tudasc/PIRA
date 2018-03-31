from ConfigLoader import ConfigurationLoader as CL
from ConfigLoaderNew import ConfigurationLoader as Conf
from Builder import Builder as B
from Analyzer import Analyzer as A
import Logging as log
import Utility as util
import Logging as logging
from lib.db import database as db
import lib.tables as tables


def runner(flavors,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber):
    for flavor in flavors:
        build_functor = util.load_functor(config.get_runner_func(build,benchmark),'runner_'+flavor)
        if build_functor.get_method()['active']:
            build_functor.active(benchmark, **kwargs)

        else:
            try:
                command = build_functor.passive(benchmark, **kwargs)
                util.change_cwd(benchmark)
                exp_dir = config.get_analyser_exp_dir(build,benchmark)
                benchmark_name = config.get_benchmark_name(benchmark)
                if isNoInstrumentationRun == False:
                    util.set_env('SCOREP_EXPERIMENT_DIRECTORY',exp_dir+'-'+flavor+'-'+str(iterationNumber))
                    util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY','true')
                    util.set_env('SCOREP_PROFILING_BASE_NAME',flavor+'-'+benchmark_name[0])
                else:
                    util.set_env('SCOREP_EXPERIMENT_DIRECTORY',exp_dir+'-'+flavor+'-'+str(iterationNumber)+'noInstrRun')
                    util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY','true')


                '''
                isdirectory_good = util.check_provided_directory(exp_dir)
                if(isdirectory_good):
                    #if(util.check_file(exp_dir+"profile.cubex")):
                    benchmark_name = config.get_benchmark_name(benchmark)
                    util.set_env('SCOREP_PROFILING_BASE_NAME',exp_dir+'\\'+flavor+'-'+benchmark_name[0])
                '''
                #command = '/home/sachin/MasterThesis/GameOfLife/serial_non_template/gol'
                runTime = util.shell(command)
                print "Exection runt-time "+ runTime
                #text_file = open("Output.txt", "w")
                #text_file.write(outputstr)
                #text_file.close()

            except Exception as e:
                logging.get_logger().log(e.message, level='warn')

def submitter(flavors,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber):
    print('In submitter');
    for flavor in flavors:
        submitter_functor = util.load_functor(config.get_runner_func(build,benchmark),'slurm_submitter_'+flavor)
        exp_dir = config.get_analyser_exp_dir(build,benchmark)
        benchmark_name = config.get_benchmark_name(benchmark)
        if isNoInstrumentationRun == False:
            util.set_env('SCOREP_EXPERIMENT_DIRECTORY',exp_dir+'-'+flavor+'-'+str(iterationNumber))
            util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY','true')
            util.set_env('SCOREP_PROFILING_BASE_NAME',flavor+'-'+benchmark_name[0])
        else:
            util.set_env('SCOREP_EXPERIMENT_DIRECTORY',exp_dir+'-'+flavor+'-'+str(iterationNumber)+'noInstrRun')
            util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY','true')


        tup = [(flavor,'/home/sm49xeji/job.sh')]
        kwargs={"util":util,"runs_per_job":1,"dependent":0}
        submitter_functor.dispatch(tup,**kwargs)
        print(submitter_functor)
        #exit(0)


def run_detail(config,build,benchmark,isNoInstrumentationRun,iterationNumber):
    kwargs = {'compiler': ''}

    if config.builds[build]['flavours']:
        if config.get_is_submitter(build,benchmark):
            submitter(config.builds[build]['flavours'],build,benchmark,kwargs,config);
        else:
            runner(config.builds[build]['flavours'],build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber)

    else:
        if config.get_is_submitter(build,benchmark):
            submitter(config.builds[build]['flavours'],build,benchmark,kwargs,config);
        else:
            runner(config.global_flavors,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber)


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
                    #while configuration.stop_iteration[build+item+flavor] == False:
                    for x in range(0, 5):
                        #Check if its the first iteration
                        if configuration.builds[build]['flavours']:
                            for benchmark in configuration.builds[build]['items']:
                                #Only run the pgoe to get the functions name
                                if(configuration.is_first_iteration[build+item+flavor] == False):
                                    configuration.is_first_iteration[build+item+flavor]=True

                                    #Build and run without any instrumentation
                                    BuildNoInstr = B(build,configuration)
                                    BuildNoInstr.build_no_instr = True;
                                    BuildNoInstr.build()

                                    # Run - this binary does not contain any instrumentation.
                                    for y in range(0,5):
                                        run_detail(configuration,build,benchmark,True,y)
                                    analyser = A(configuration,build,benchmark)
                                    analyser.analyse_detail(configuration,build,benchmark,y)

                        builder = B(build, configuration)
                        builder.build()

                        if configuration.builds[build]['flavours']:
                            for benchmark in configuration.builds[build]['items']:
                    #Run Phase
                                run_detail(configuration,build,benchmark,False,x)

                    #Analysis Phase
                                analyser = A(configuration,build,benchmark)
                                analyser.analyse_detail(configuration,build,benchmark,x)

            log.get_logger().dump_tape()

    except StandardError as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
