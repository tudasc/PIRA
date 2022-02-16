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
from lib.Configuration import TargetConfig, InvocationConfig as InvocCfg


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

  def analyze(self, target_config: TargetConfig, iteration_number: int, was_rebuilt: bool) -> str:
    # The sink needs to be set for the Analyzer to run
    if self._profile_sink is None:
      raise RuntimeError('Analyzer::analyze: Profile Sink in Analyzer not set!')

    if target_config is None:
      raise RuntimeError('Analyzer::analyze: TargetConfiguration object is None!')

    default_provider = D.BackendDefaults()
    kwargs = default_provider.get_default_kwargs()

    return self.analyze_local(target_config, kwargs, iteration_number, was_rebuilt)


  def analyze_local(self, target_config: TargetConfig, kwargs: dict, iterationNumber: int, was_rebuild: bool)  -> str:
    flavor = target_config.get_flavor()
    build = target_config.get_build()
    benchmark = target_config.get_target()
    hybrid_filter = InvocCfg.get_instance().is_hybrid_filtering()
    fm = F.FunctorManager()
    analyze_functor = fm.get_or_load_functor(build, benchmark, flavor, 'analyze')
    analyzer_dir = self.config.get_analyzer_dir(build, benchmark)
    kwargs['analyzer_dir'] = analyzer_dir

    # The invoke args can be retrieved from the configuration object.
    # Since the invoke args are iterable, we can create all necessary argument tuples here.

    extrap_config_file = None
    if self._profile_sink.has_config_output():
      extrap_config_file = self._profile_sink.output_config(benchmark, analyzer_dir)

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
          prev_instr_file = U.build_previous_instr_file_path(analyzer_dir, flavor, benchmark_name, iterationNumber)

        tracker = T.TimeTracker()
        
        # TODO: Alternate between expansion and pure filtering.
        if iterationNumber > 0 and U.is_file(instr_files):
          L.get_logger().log('Analyzer::analyze_local: instr_file available')
          U.rename(instr_files, prev_instr_file)
          tracker.f_track('Analysis', self.run_analyzer_command, command, analyzer_dir, flavor, benchmark_name,
                          exp_dir, iterationNumber, extrap_config_file, was_rebuild)
          L.get_logger().log('Analyzer::analyze_local: command finished', level='debug')

        else:
          tracker.f_track('Initial analysis', self.run_analyzer_command_no_instr, command, analyzer_dir, flavor,
                          benchmark_name)
            
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


  @staticmethod
  def run_analyzer_command(command: str, analyzer_dir: str, flavor: str, benchmark_name: str, exp_dir: str,
                           iterationNumber: int, extrap_config_file: str, was_rebuilt: bool, hybrid_filter: bool = False) -> None:

    export_performance_models = InvocCfg.get_instance().is_export()
    export_runtime_only = InvocCfg.get_instance().is_export_runtime_only()
    use_cs_instrumentation = InvocCfg.get_instance().use_cs_instrumentation()
    analysis_parameters_path = InvocCfg.get_instance().get_analysis_parameters_path()
    export_str = ' '
    if export_performance_models:
      export_str += ' --export'
      if export_runtime_only:
        export_str += ' --runtime-only'

    ipcg_file = U.get_ipcg_file_name(analyzer_dir, benchmark_name, flavor)
    cubex_dir = U.get_cube_file_path(exp_dir, flavor, iterationNumber - 1)
    cubex_file = U.get_cubex_file(cubex_dir, benchmark_name, flavor)

    # PIRA version 1 runner, i.e., only consider raw runtime of single run
    if extrap_config_file is None:
      if InvocCfg.get_instance().is_lide_enabled():
        # load imbalance detection mode
        L.get_logger().log('Utility::run_analyzer_command: using Load Imbalance Detection Analyzer', level='info')
        if analysis_parameters_path == '':
          L.get_logger().log('Utility::run_analyzer_command: An analysis parameters file is required for PIRA LIDe!', level='error')

        sh_cmd = command + export_str + ' --scorep-out -c ' + cubex_file + ' --lide 1 --parameter-file ' + analysis_parameters_path + ' --debug 1 --export ' + ipcg_file 

      else:
        # vanilla PIRA version 1 runner
        L.get_logger().log('Utility::run_analyzer_command: using PIRA 1 Analyzer', level='info')
        sh_cmd = command + export_str + ' --scorep-out ' + ipcg_file + ' -c ' + cubex_file

      L.get_logger().log('Utility::run_analyzer_command: INSTR: Run cmd: ' + sh_cmd)
      out, _ = U.shell(sh_cmd)
      L.get_logger().log('Utility::run_analyzer_command: Output of analyzer:\n' + out, level='debug')
      return

    if hybrid_filter and not was_rebuilt:
      command += ' --model-filter'

    if use_cs_instrumentation:
      command += ' --use-cs-instrumentation'

    if analysis_parameters_path == '':
      L.get_logger().log('Utility::run_analyzer_command: An analysis parameters file is required for Extra-P mode!', level='error')
    sh_cmd = command + export_str + ' --scorep-out --debug 1 --parameter-file ' + analysis_parameters_path + ' --extrap ' + extrap_config_file + ' ' + ipcg_file
    L.get_logger().log('Utility::run_analyzer_command: INSTR: Run cmd: ' + sh_cmd)
    out, _ = U.shell(sh_cmd)
    L.get_logger().log('Utility::run_analyzer_command: Output of analyzer:\n' + out, level='debug')

  @staticmethod
  def run_analyzer_command_no_instr(command: str, analyzer_dir: str, flavor: str, benchmark_name: str) -> None:
    ipcg_file = U.get_ipcg_file_name(analyzer_dir, benchmark_name, flavor)
    sh_cmd = command + ' --scorep-out --static '

    # load imbalancee detection mode
    if InvocCfg.get_instance().is_lide_enabled():
      sh_cmd = sh_cmd + ' --debug 1 --lide 1 ' + InvocCfg.get_instance().get_analysis_parameters_path()

    sh_cmd = sh_cmd + ' ' + ipcg_file

    L.get_logger().log('Utility::run_analyzer_command_noInstr: NO INSTR: Run cmd: ' + sh_cmd)
    out, _ = U.shell(sh_cmd)
    L.get_logger().log('Utility::run_analyzer_command_noInstr: Output of analyzer:\n' + out, level='debug')

