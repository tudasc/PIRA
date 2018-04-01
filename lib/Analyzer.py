import Utility as util
import Logging as logging


class Analyzer:
    def __init__(self, configuration,build,benchmark):
        self.directory = build
        self.config = configuration
        self.benchmark = benchmark
        self.old_cwd = build
        self.error = None

    def analyse(self,flavor,build,benchmark,kwargs,config,iterationNumber):
        analyse_functor = util.load_functor(config.get_analyse_func(build,benchmark),'analyse_'+flavor)
        if analyse_functor.get_method()['active']:
            analyse_functor.active(benchmark, **kwargs)

        else:
            try:
                command = analyse_functor.passive(benchmark, **kwargs)
                exp_dir = config.get_analyser_exp_dir(build,benchmark)
                analyser_dir = config.get_analyser_dir(build,benchmark)
                isdirectory_good = util.check_provided_directory(analyser_dir)
                if isdirectory_good:
                    util.change_cwd(analyser_dir)
                    benchmark_name = config.get_benchmark_name(benchmark)
                    instr_files = analyser_dir+"/"+'out/instrumented-'+flavor+'-'+benchmark_name[0]+'.txt'
                    prev_instr_file = analyser_dir+"/"+'out/instrumented-'+flavor+'-'+benchmark_name[0]+'previous.txt'

                if(util.check_file(instr_files)):
                    util.rename(instr_files,prev_instr_file)
                    util.shell(command+' '+analyser_dir+"/"+flavor+'-'+benchmark_name[0]+'.ipcg '+exp_dir+'-'+flavor+'-'+str(iterationNumber)+'/'+flavor+'-'+benchmark_name[0]+'.cubex')
                else:
                    util.shell(command+' '+analyser_dir+"/"+flavor+'-'+benchmark_name[0]+'.ipcg ')

                self.tear_down(exp_dir)

            except Exception as e:
                logging.get_logger().log(e.message, level='error')


    def analyse_slurm(self,flavors,build,benchmark,kwargs,config):
        for flavor in flavors:
            try:
                analyse_functor = util.load_functor(config.get_analyse_slurm_func(build,benchmark),'analyse_slurm_submitter_'+flavor)
                tup = [(flavor,'/home/sm49xeji/job_analyse.sh')]
                kwargs={"util":util,"runs_per_job":1,"dependent":1}
                analyse_functor.dispatch(tup,**kwargs)
                print(analyse_functor)

            except Exception as e:
                logging.get_logger().log(e.message, level='error')


    def set_up(self):
       pass

    def tear_down(self,exp_dir):
        isdirectory_good = util.check_provided_directory(exp_dir)
        if isdirectory_good:
            try:
                util.change_cwd(self.old_cwd)
            except Exception as e:
                logging.get_logger().log(e.message, level='error')

    def analyse_detail(self,config,build,benchmark,flavor,iterationNumber):
        kwargs = {'compiler': ''}
        if config.get_is_submitter(build,benchmark):
            self.analyse_slurm(flavor,build,benchmark,kwargs,config)
        else:
            self.analyse(flavor,build,benchmark,kwargs,config,iterationNumber)

    def run_analyzer(self,flavors,build,benchmark,kwargs):
        pass