import Utility as util
import Logging as logging
import shutil


class Analyzer:
    def __init__(self, configuration,build,benchmark):
        self.directory = build
        self.config = configuration
        self.benchmark = benchmark
        self.old_cwd = build
        self.error = None

    def analyse(self,flavors,build,benchmark,kwargs,config):
        for flavor in flavors:
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
                        util.shell(command+' '+exp_dir+'profile.cubex')
                        self.tear_down(exp_dir)
                    #command = '/home/sachin/MasterThesis/GameOfLife/serial_non_template/gol'
                    #util.shell(command)

                except Exception as e:
                    logging.get_logger().log(e.message, level='error')


    def set_up(self):
       pass
    def tear_down(self,exp_dir):
        isdirectory_good = util.check_provided_directory(exp_dir)
        if isdirectory_good:
            try:
                shutil.rmtree(exp_dir)
                util.change_cwd(self.old_cwd)
            except Exception as e:
                logging.get_logger().log(e.message, level='error')

    def analyse_detail(self, config,build,benchmark):
        kwargs = {'compiler': ''}

        if config.builds[build]['flavours']:
            self.analyse(config.builds[build]['flavours'],build,benchmark,kwargs,config)

        else:
            self.analyse(config.global_flavors,build,benchmark,kwargs,config)

    def run_analyzer(self,flavors,build,benchmark,kwargs):
        pass