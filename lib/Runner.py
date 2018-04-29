from ConfigLoaderNew import ConfigurationLoader as Conf
from Builder import Builder as B
from Analyzer import Analyzer as A
import Logging as log
import Utility as util
import Logging as logging
from lib.db import database as db
import lib.tables as tables

#Some contants to manage slurm submitter tmp file read
JOBID           = 0
BENCHMARKNAME   = 1
ITERATIONNUMBER = 2
ISWITHINSTR     = 3
CUBEFILEPATH    = 4
ITEMID          = 5
BUILDNAME       = 6
ITEM            = 7
FLAVOR          = 8


def runner(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur):
        benchmark_name = config.get_benchmark_name(benchmark)
        #build_functor = util.load_functor(config.get_runner_func(build,benchmark),'runner_'+benchmark_name[0]+'_'+flavor)
        build_functor = util.load_functor(config.get_runner_func(build,benchmark),util.build_runner_functor_filename(False,benchmark_name[0],flavor))
        if build_functor.get_method()['active']:
            build_functor.active(benchmark, **kwargs)

        else:
            try:
                command = build_functor.passive(benchmark, **kwargs)
                util.change_cwd(benchmark)
                exp_dir = config.get_analyser_exp_dir(build,benchmark)

                if isNoInstrumentationRun == False:
                    DBIntVal = 1
                    DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
                    util.set_scorep_exp_dir(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
                    util.set_overwrite_scorep_exp_dir()
                    util.set_scorep_profiling_basename(flavor,benchmark_name[0])

                else:
                    DBIntVal = 0
                    DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
                    util.set_scorep_exp_dir(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
                    util.set_overwrite_scorep_exp_dir()

                runTime = util.shell(command)
                #Insert into DB
                experiment_data = (util.generate_random_string(),benchmark_name[0],iterationNumber,DBIntVal,DBCubeFilePath,str(runTime),itemID)
                database.insert_data_experiment(cur,experiment_data)
            except Exception as e:
                logging.get_logger().log(e.message, level='warn')

def submitter(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur):
    benchmark_name = config.get_benchmark_name(benchmark)
    submitter_functor = util.load_functor(config.get_runner_func(build,benchmark),'slurm_submitter_'+benchmark_name[0]+'_'+flavor)
    exp_dir = config.get_analyser_exp_dir(build,benchmark)

    if isNoInstrumentationRun == False:
        DBIntVal = 1
        DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
        util.set_scorep_exp_dir(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
        util.set_overwrite_scorep_exp_dir()
        util.set_scorep_profiling_basename(flavor,benchmark_name[0])

    else:
        DBIntVal = 0
        DBCubeFilePath = util.build_cube_file_path_for_db(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
        util.set_scorep_exp_dir(exp_dir,flavor,iterationNumber,isNoInstrumentationRun)
        util.set_overwrite_scorep_exp_dir()


    #tup = [(flavor,'/home/sm49xeji/job.sh')]
    tup = [(flavor,config.get_batch_script_func(build,benchmark))]
    kwargs={"util":util,"runs_per_job":1,"dependent":0}
    job_id = submitter_functor.dispatch(tup,**kwargs)
    util.create_batch_queued_temp_file(job_id,benchmark_name[0],iterationNumber,DBIntVal,DBCubeFilePath,itemID,build,benchmark,flavor)
    exit(0)


def run_detail(config,build,benchmark,flavor,isNoInstrumentationRun,iterationNumber,itemID,database,cur):
    kwargs = {'compiler': ''}

    if config.get_is_submitter(build,benchmark):
        submitter(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur);
    else:
        runner(flavor,build,benchmark,kwargs,config,isNoInstrumentationRun,iterationNumber,itemID,database,cur)

def run_setup(configuration,build,item,flavor,itemID,database,cur):
    for x in range(0, 5):
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

            util.remove_from_pgoe_out_dir(analyser_dir)

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
        Create tables if not exists
        '''
        database.create_table(cur,tables.sql_create_application_table)
        database.create_table(cur,tables.sql_create_builds_table)
        database.create_table(cur,tables.sql_create_items_table)
        database.create_table(cur,tables.sql_create_experiment_table)


        #Flow for submitter
        if util.check_queued_job() == True:
            #read file to get build, item, flavor, iteration, itemID, and runtime
            job_details = util.read_batch_queued_job()

            #get run-time of the submitted job
            runtime = util.get_runtime_of_submitted_job(job_details[JOBID])
            util.read_batch_queued_job()

            #Insert into DB
            experiment_data = (util.generate_random_string(),job_details[BENCHMARKNAME],job_details[ITERATIONNUMBER],job_details[ISWITHINSTR],job_details[CUBEFILEPATH],runtime,job_details[ITEMID])
            database.insert_data_experiment(cur,experiment_data)

            if(int(job_details[ISWITHINSTR]) == 0 and int(job_details[ITERATIONNUMBER]) < 4):

                #Build and run without any instrumentation
                BuildNoInstr = B(job_details[BUILDNAME],configuration)
                BuildNoInstr.build_no_instr = True;
                BuildNoInstr.build(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR])

                # Run - this binary does not contain any instrumentation.
                run_detail(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR],True,int(job_details[ITERATIONNUMBER])+1,job_details[ITEMID],database,cur)

            if(int(job_details[ISWITHINSTR]) == 0 and int(job_details[ITERATIONNUMBER]) == 4):
                analyser_dir = configuration.get_analyser_dir(job_details[BUILDNAME],job_details[ITEM])
                #Remove anything in the output dir of the analysis tool
                util.remove_from_pgoe_out_dir(analyser_dir)

                #Generate white-list functions
                analyser = A(configuration,job_details[BUILDNAME],job_details[ITEM])
                analyser.analyse_detail(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR],0)

                builder = B(job_details[BUILDNAME], configuration)
                builder.build(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR])
                run_detail(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR],False,0,job_details[ITEMID],database,cur)

            if(int(job_details[ISWITHINSTR]) == 1):
                analyser = A(configuration,job_details[BUILDNAME],job_details[ITEM])
                analyser.analyse_detail(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR],int(job_details[ITERATIONNUMBER]))


                builder = B(job_details[BUILDNAME], configuration)
                builder.build(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR])

                # Run Phase
                run_detail(configuration,job_details[BUILDNAME],job_details[ITEM],job_details[FLAVOR],False,int(job_details[ITERATIONNUMBER])+1,job_details[ITEMID],database,cur)
        else:
            for build in configuration.builds:
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
                            analyse_functor = configuration.get_analyse_func(build,item)+util.build_analyse_functor_filename(True,benchmark_name[0],flavor)
                            build_functor = configuration.get_flavor_func(build,item)+util.build_builder_functor_filename(True,False,benchmark_name[0],flavor)
                            run_functor = configuration.get_runner_func(build,item)+util.build_runner_functor_filename(True,benchmark_name[0],flavor)
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
