"""
File: Analyzer.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to encapsulate the underlying analysis engine.
"""

import lib.Utility as U
import lib.Logging as L
import lib.TimeTracking as T 
import lib.FunctorManagement as F
import lib.DefaultFlags as D
import lib.Exception as E


class PiraAnalyzerException(E.PiraException):
  def __init__(self, m):
    super().__init__(m)

class Analyzer:

  def __init__(self, configuration) -> None:
    if configuration.is_empty():
      raise PiraAnalyzerException('Constructing analyzer from empty configuration not supported.')

    self.config = configuration
    self.error = None
    self._profile_sink = None

  def set_profile_sink(self, sink) -> None:
    self._profile_sink = sink

  def analyze_local(self, flavor: str, build: str, benchmark: str, kwargs: dict, iterationNumber: int) -> str:
    fm = F.FunctorManager()
    analyze_functor = fm.get_or_load_functor(build, benchmark, flavor, 'analyze')
    analyzer_dir = self.config.get_analyzer_dir(build, benchmark)
    kwargs['analyzer_dir'] = analyzer_dir

    # The invoke args can be retrieved from the configuration object.
    # Since the invoke args are iterable, we can create all necessary argument tuples here.

    # We construct a json file that contains the necesary information to be parsed vy the
    # PGIS tool. That way, we can make it easily traceable and debug from manual inspection.
    # This will be the new standard way of pusing information to PGIS.
    pgis_cfg_file = None
    if self._profile_sink.has_config_output():
      pgis_cfg_file = self._profile_sink.output_config(benchmark, analyzer_dir)

    if analyze_functor.get_method()['active']:
      analyze_functor.active(benchmark, **kwargs)

    else:
      L.get_logger().log('Analyzer::analyze_local: Using passive mode')
      try:
        exp_dir = self.config.get_analyzer_exp_dir(build, benchmark)
        isdirectory_good = U.check_provided_directory(analyzer_dir)
        command = analyze_functor.passive(benchmark, **kwargs)

        L.get_logger().log('Analyzer::analyze_local: Command = ' + command)

        benchmark_name = self.config.get_benchmark_name(benchmark)

        if isdirectory_good:
          U.change_cwd(analyzer_dir)
          L.get_logger().log('Analyzer::analyzer_local: Flavor = ' + flavor + ' | benchmark_name = ' +
                                   benchmark_name)
          instr_files = U.build_instr_file_path(analyzer_dir, flavor, benchmark_name)
          L.get_logger().log('Analyzer::analyzer_local: instrumentation file = ' + instr_files)
          prev_instr_file = U.build_previous_instr_file_path(analyzer_dir, flavor, benchmark_name)

        tracker = T.TimeTracker()
        
        # TODO: Alternate between expansion and pure filtering.

        if iterationNumber > 0 and U.is_file(instr_files):
          L.get_logger().log('Analyzer::analyze_local: instr_file available')
          U.rename(instr_files, prev_instr_file)
          tracker.m_track('Analysis', U, 'run_analyzer_command', command, analyzer_dir, flavor, benchmark_name,

                          exp_dir, iterationNumber, pgis_cfg_file)
          L.get_logger().log('Analyzer::analyze_local: command finished', level='debug')
        else:

          tracker.m_track('Initial analysis', U, 'run_analyzer_command_noInstr', command, analyzer_dir, flavor,
                          benchmark_name)
          U.run_analyzer_command_noInstr(command, analyzer_dir, flavor, benchmark_name)

        self.tear_down(build, exp_dir)
        return instr_files

      except Exception as e:
        L.get_logger().log(str(e), level='error')
        raise Exception('Problem in Analyzer')

  def analyze_slurm(self, flavors, build, benchmark, kwargs, config):
    L.get_logger().log('Analyzer::analyze_slurm: Not implemented. Aborting.', level='error')
    assert(False)

  def set_up(self):
    pass

  def tear_down(self, old_dir, exp_dir):
    isdirectory_good = U.check_provided_directory(exp_dir)
    if isdirectory_good:
      try:
        U.change_cwd(old_dir)
      except Exception as e:
        L.get_logger().log(str(e), level='error')

  def analyze(self, target_config, iteration_number: int) -> str:
    # The sink needs to be set for the Analyzer to run
    if self._profile_sink is None:
      raise RuntimeError('Analyzer::analyze: Profile Sink in Analyzer not set!')

    if target_config is None:
      raise RuntimeError('Analyzer::analyze: TargetConfiguration object is None!')

    default_provider = D.BackendDefaults()
    kwargs = default_provider.get_default_kwargs()

    flavor = target_config.get_flavor()
    build = target_config.get_build()
    benchmark = target_config.get_target()
    return self.analyze_local(flavor, build, benchmark, kwargs, iteration_number)
