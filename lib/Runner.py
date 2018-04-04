from ConfigLoaderNew import ConfigurationLoader as Conf
from Builder import Builder as B
from Analyzer import Analyzer as A
import Logging as log
import Utility as util
import Logging as logging
from lib.db import database as db
import lib.tables as tables


def runner(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur):
        benchmark_name = config.get_benchmark_name(benchmark)
        build_functor = util.load_functor(config.get_runner_func(build,benchmark),'runner_'+benchmark_name[0]+'_'+flavor)
        if build_functor.get_method()['active']:
            build_functor.active(benchmark, **kwargs)

        else:
            try:
                command = build_functor.passive(benchmark, **kwargs)
                util.change_cwd(benchmark)
                exp_dir = config.get_analyser_exp_dir(build,benchmark)
                #benchmark_name = config.get_benchmark_name(benchmark)
                if isNoInstrumentationRun == False:
                    DBIntVal = 1
                    DBCubeFilePath = exp_dir+'-'+flavor+'-'+str(iterationNumber)
                    util.set_env('SCOREP_EXPERIMENT_DIRECTORY',exp_dir+'-'+flavor+'-'+str(iterationNumber))
                    util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY','true')
                    util.set_env('SCOREP_PROFILING_BASE_NAME',flavor+'-'+benchmark_name[0])
                else:
                    DBIntVal = 0
                    DBCubeFilePath = exp_dir+'-'+flavor+'-'+str(iterationNumber)+'noInstrRun'
                    util.set_env('SCOREP_EXPERIMENT_DIRECTORY',exp_dir+'-'+flavor+'-'+str(iterationNumber)+'noInstrRun')
                    util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY','true')

                runTime = util.shell(command)
                #Insert into DB
                experiment_data = (util.generate_random_string(),benchmark_name[0],iterationNumber,DBIntVal,DBCubeFilePath,str(runTime),itemID)
                database.insert_data_experiment(cur,experiment_data)
            except Exception as e:
                logging.get_logger().log(e.message, level='warn')

def submitter(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur):
    #print('In submitter');
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
    #print(submitter_functor)


def run_detail(config,build,benchmark,flavor,isNoInstrumentationRun,iterationNumber,itemID,database,cur):
    kwargs = {'compiler': ''}

    if config.get_is_submitter(build,benchmark):
        submitter(flavor,build,benchmark,kwargs,config,itemID,database,cur);
    else:
        runner(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur)

def run_setup(configuration,build,item,flavor,itemID,database,cur):
    for x in range(0, 5):
        #if configuration.builds[build]['flavours']:
        #Only run the pgoe to get the functions name
        if(configuration.is_first_iteration[build+item+flavor] == False):
            configuration.is_first_iteration[build+item+flavor]=True

            #Build and run without any instrumentation
            BuildNoInstr = B(build,configuration)
            BuildNoInstr.build_no_instr = True;
            BuildNoInstr.build(configuration,build,item,flavor)

            # Run - this binary does not contain any instrumentation.
            for y in range(0,5):
                run_detail(configuration,build,item,flavor,True,y,itemID,database,cur)

            analyser_dir = configuration.get_analyser_dir(build,item)
            #Remove anything in the output dir of the analysis tool
            util.remove(analyser_dir+"/"+"out")

            analyser = A(configuration,build,item)
            analyser.analyse_detail(configuration,build,item,flavor,y)

        builder = B(build, configuration)
        builder.build(configuration,build,item,flavor)

        #Run Phase
        run_detail(configuration,build,item,flavor,False,x,itemID,database,cur)

        #Analysis Phase
        analyser = A(configuration,build,item)
        analyser.analyse_detail(configuration,build,item,flavor,x)

def run(path_to_config):
    try:
        config_loader = Conf()
        configuration = config_loader.load_conf(path_to_config)
        configuration.initialize_stopping_iterator()
        configuration.initialize_first_iteration()

        '''
        Initialize Database
        '''
        database = db("BenchPressDB")
        cur = database.create_cursor(database.conn)

        '''
        Create tables
        '''
        database.create_table(cur,tables.sql_create_application_table)
        database.create_table(cur,tables.sql_create_builds_table)
        database.create_table(cur,tables.sql_create_items_table)
        database.create_table(cur,tables.sql_create_experiment_table)

        #insert to application table

        '''
        if ((configuration.global_flavors.__len__() == 0) and (configuration.global_submitter.__len__() == 0)):
            application = ("GameofLife",'','')
            database.insert_data_application(cur,application)
        '''
        for build in configuration.builds:
            #if ((configuration.global_flavors.__len__() != 0) and (configuration.global_submitter.__len__() == 0)):
            application = (util.generate_random_string(),build,'','')
            database.insert_data_application(cur,application)
            for item in configuration.builds[build]['items']:
                if configuration.builds[build]['flavours']:
                    for flavor in configuration.builds[build]['flavours']:
                        dbbuild = (util.generate_random_string(),build,'',flavor,build)
                        database.insert_data_builds(cur,dbbuild)

                        #Insert into DB the benchmark data
                        benchmark_name = configuration.get_benchmark_name(item)
                        itemID = util.generate_random_string()
                        analyse_functor = configuration.get_analyse_func(build,item)+'/analyse_'+benchmark_name[0]+flavor
                        build_functor = configuration.get_flavor_func(build,item)+'/'+benchmark_name[0]+flavor
                        run_functor = configuration.get_runner_func(build,item)+'/runner_'+benchmark_name[0]+flavor

                        submitter_functor = configuration.get_runner_func(build,item)+'/slurm_submitter_'+benchmark_name[0]+flavor
                        exp_dir = configuration.get_analyser_exp_dir(build,item)
                        itemDBData = (itemID,benchmark_name[0],analyse_functor,build_functor,'',run_functor,submitter_functor,exp_dir,build)
                        database.insert_data_items(cur,itemDBData)

                        run_setup(configuration,build,item,flavor,itemID,database,cur)

                #If global flavor
                else:
                    for flavor in configuration.global_flavors:
                        run_setup(configuration,build,item,flavor,itemID,database,cur)

            log.get_logger().dump_tape()

    except StandardError as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
