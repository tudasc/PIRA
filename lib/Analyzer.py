import lib.Utility as util
import lib.Logging as logging


class Analyzer:

  def __init__(self, configuration, build, benchmark):
    self.directory = build
    self.config = configuration
    self.benchmark = benchmark
    self.old_cwd = build
    self.error = None

  def analyse(self, flavor, build, benchmark, kwargs, config, iterationNumber):
    benchmark_name = config.get_benchmark_name(benchmark)
    anal_func_filename = util.build_analyse_functor_filename(False, benchmark_name, flavor)
    logging.get_logger().log('Loading analysis functor at: ' + anal_func_filename)

    analyse_functor = util.load_functor(config.get_analyse_func(build, benchmark), anal_func_filename)
    if analyse_functor.get_method()['active']:
      analyse_functor.active(benchmark, **kwargs)

    else:
      logging.get_logger().log('Using passive mode')
      try:
        exp_dir = config.get_analyser_exp_dir(build, benchmark)
        analyser_dir = config.get_analyser_dir(build, benchmark)
        isdirectory_good = util.check_provided_directory(analyser_dir)
        # XXX We need to identify a 'needed set of variables' that can be relied on begin passed
        kwargs = {'analyzer_dir': analyser_dir}
        command = analyse_functor.passive(benchmark, **kwargs)

        logging.get_logger().log('Analyzer with command: ' + command)
        logging.get_logger().log('Checking ' + analyser_dir + ' | is good: ' + str(isdirectory_good))
        if isdirectory_good:
          util.change_cwd(analyser_dir)
          instr_files = util.build_instr_file_path(analyser_dir, flavor, benchmark_name)
          logging.get_logger().log('The built instrumentation file path is: ' + instr_files)
          prev_instr_file = util.build_previous_instr_file_path(analyser_dir, flavor, benchmark_name)

        if util.check_file(instr_files):
          util.rename(instr_files, prev_instr_file)
          util.run_analyser_command(command, analyser_dir, flavor, benchmark_name, exp_dir,
                                    iterationNumber)
        else:
          util.run_analyser_command_noInstr(command, analyser_dir, flavor, benchmark_name)
        self.tear_down(exp_dir)

      except Exception as e:
        logging.get_logger().log(str(e), level='error')

        raise Exception('Problem in Analyzer')

  def analyse_slurm(self, flavors, build, benchmark, kwargs, config):
    for flavor in flavors:
      try:
        analyse_functor = util.load_functor(
            config.get_analyse_slurm_func(build, benchmark), 'analyse_slurm_submitter_' + flavor)
        tup = [(flavor, '/home/sm49xeji/job_analyse.sh')]
        kwargs = {"util": util, "runs_per_job": 1, "dependent": 1}
        analyse_functor.dispatch(tup, **kwargs)
        #print(analyse_functor)

      except Exception as e:
        logging.get_logger().log(str(e), level='error')

        raise Exception('Problem in Analyzer')

  def set_up(self):
    pass

  def tear_down(self, exp_dir):
    isdirectory_good = util.check_provided_directory(exp_dir)
    if isdirectory_good:
      try:
        util.change_cwd(self.old_cwd)
      except Exception as e:
        logging.get_logger().log(e.message, level='error')

  def analyse_detail(self, config, build, benchmark, flavor, iterationNumber):
    kwargs = {'compiler': ''}
    # No need to analyse on the slurm. May be a future extension
    '''
        if config.is_submitter(build,benchmark):
            self.analyse_slurm(flavor,build,benchmark,kwargs,config)
        else:
        '''
    self.analyse(flavor, build, benchmark, kwargs, config, iterationNumber)

  def run_analyzer(self, flavors, build, benchmark, kwargs):
    pass
