"""
File: Analyzer.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to encapsulate the underlying analysis engine.
"""

import lib.Utility as util
import lib.Logging as logging
import lib.TimeTracking as tt
import lib.FunctorManagement as fmg


class Analyzer:

  def __init__(self, configuration) -> None:
    self.config = configuration
    self.error = None

  def analyze_local(self, flavor, build, benchmark, kwargs, iterationNumber) -> str:
    fm = fmg.FunctorManager()
    analyze_functor = fm.get_or_load_functor(build, benchmark, flavor, 'analyze')

    if analyze_functor.get_method()['active']:
      analyze_functor.active(benchmark, **kwargs)

    else:
      logging.get_logger().log('Using passive mode')
      try:
        exp_dir = self.config.get_analyser_exp_dir(build, benchmark)
        analyzer_dir = self.config.get_analyser_dir(build, benchmark)
        isdirectory_good = util.check_provided_directory(analyzer_dir)
        # XXX We need to identify a 'needed set of variables' that can be relied on begin passed
        kwargs = {'analyzer_dir': analyzer_dir}
        command = analyze_functor.passive(benchmark, **kwargs)

        logging.get_logger().log('Analyzer with command: ' + command)
        logging.get_logger().log('Checking ' + analyzer_dir + ' | is good: ' + str(isdirectory_good))

        benchmark_name = self.config.get_benchmark_name(benchmark)

        if isdirectory_good:
          util.change_cwd(analyzer_dir)
          instr_files = util.build_instr_file_path(analyzer_dir, flavor, benchmark_name)
          logging.get_logger().log('The built instrumentation file path is: ' + instr_files)
          prev_instr_file = util.build_previous_instr_file_path(analyzer_dir, flavor, benchmark_name)

        if util.check_file(instr_files):
          util.rename(instr_files, prev_instr_file)
          #tt.m_track('analysis', util, 'run_analyser_command', command, analyser_dir, flavor, benchmark_name, exp_dir, iterationNumber-1)
          util.run_analyser_command(command, analyzer_dir, flavor, benchmark_name, exp_dir,
                                    iterationNumber-1)
          logging.get_logger().log('Analyzer command finished', level='debug')
        else:
          util.run_analyser_command_noInstr(command, analyzer_dir, flavor, benchmark_name)

        self.tear_down(build, exp_dir)
        return instr_files

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

  def tear_down(self, old_dir, exp_dir):
    isdirectory_good = util.check_provided_directory(exp_dir)
    if isdirectory_good:
      try:
        util.change_cwd(old_dir)
      except Exception as e:
        logging.get_logger().log(str(e), level='error')

  #def analyse_detail(self, config, build, benchmark, flavor, iterationNumber) -> str:
  def analyze(self, target_config, iteration_number: int) -> str:
    kwargs = {'compiler': ''}
    # No need to analyse on the slurm. May be a future extension
    '''
        if config.is_submitter(build,benchmark):
            self.analyse_slurm(flavor,build,benchmark,kwargs,config)
        else:
        '''
    flavor = target_config.get_flavor()
    build = target_config.get_build()
    benchmark = target_config.get_target()
    return self.analyze_local(flavor, build, benchmark, kwargs, iteration_number)

  def run_analyzer(self, flavors, build, benchmark, kwargs):
    pass
