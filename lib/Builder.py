"""
File: Builder.py
Author: JP Lehr, Sachin Manawadi
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to build the target software.
"""

import lib.Utility as util
import lib.Logging as log
import lib.FunctorManagement as fm
from lib.Configuration import TargetConfiguration
from lib.Measurement import ScorepSystemHelper
import lib.DefaultFlags as defaults
from lib.Exception import PiraException

import typing


class BuilderException(PiraException):

  def __init__(self, message):
    super().__init__(message)


class Builder:
  """
  Class which builds the benchmark executable, given a TargetConfiguration
  """

  def __init__(self, target_config: TargetConfiguration, instrument: bool, instr_file: str = None) -> None:
    self.target_config = target_config
    self.directory = target_config.get_build()
    self.old_cwd = ''
    self.build_instr = instrument
    self.instrumentation_file = instr_file
    self._compile_time_filtering = target_config.is_compile_time_filtering()
    self.error = None

  def build(self):
    try:
      self.set_up()
      self.build_detail()
      self.tear_down()

    except BuilderException as e:
      log.get_logger().log('Builder::build: Caught exception ' + str(e), level='warn')
      if self.error:
        raise Exception('Severe Problem in Builder::build')

  def set_up(self) -> None:
    log.get_logger().log('Builder::set_up for ' + self.directory)
    directory_good = util.check_provided_directory(self.directory)
    if directory_good:
      self.old_cwd = util.get_cwd()
      util.change_cwd(self.directory)
    else:
      self.error = True
      raise Exception('Builder::set_up: Could not change to directory')

  def tear_down(self) -> None:
    util.change_cwd(self.old_cwd)

  def build_detail(self) -> None:
    kwargs = {'compiler': 'clang++'}
    self.build_flavors(kwargs)

  def construct_pira_instr_kwargs(self):
    log.get_logger().log('Builder::construct_pira_instr_keywords', level='debug')
    pira_cc = ScorepSystemHelper.get_scorep_compliant_CC_command(self.instrumentation_file,
                                                                 self._compile_time_filtering)
    pira_cxx = ScorepSystemHelper.get_scorep_compliant_CXX_command(self.instrumentation_file,
                                                                   self._compile_time_filtering)
    pira_clflags = ScorepSystemHelper.get_scorep_needed_libs_c()
    pira_cxxlflags = ScorepSystemHelper.get_scorep_needed_libs_cxx()
    default_provider = defaults.BackendDefaults()
    pira_name = default_provider.get_default_exe_name()

    pira_kwargs = {
        'CC': pira_cc,
        'CXX': pira_cxx,
        'CLFLAGS': pira_clflags,
        'CXXLFLAGS': pira_cxxlflags,
        'PIRANAME': pira_name
    }
    log.get_logger().log('Builder::construct_pira_instr_keywords Returning.', level='debug')
    return pira_kwargs

  def construct_pira_kwargs(self):
    log.get_logger().log('Builder::construct_pira_keywords', level='debug')
    default_provider = defaults.BackendDefaults()

    kwargs = default_provider.get_default_kwargs()
    kwargs['CLFLAGS'] = ''
    kwargs['CXXLFLAGS'] = ''

    log.get_logger().log('Builder::construct_pira_keywords Returning.', level='debug')
    return kwargs

  def check_build_prerequisites(self):
    ScorepSystemHelper.check_build_prerequisites()

  def build_flavors(self, kwargs) -> None:
    log.get_logger().log(
        'Builder::build_flavors: Building for ' + self.target_config.get_target() + ' in ' +
        self.target_config.get_flavor(),
        level='debug')
    build = self.target_config.get_build()
    benchmark = self.target_config.get_target()
    flavor = self.target_config.get_flavor()
    f_man = fm.FunctorManager()  # Returns the currently loaded FM
    clean_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'clean')
    kwargs = {}

    if self.build_instr:
      log.get_logger().log('Builder::build_flavors: Instrumentation', level='debug')
      try:
        self.check_build_prerequisites()
      except Exception as e:
        raise BuilderException('Precheck failed.\n' + str(e))

      log.get_logger().log('Builder::build_flavors: Prerequisite check successfull.')
      if not self.target_config.is_compile_time_filtering():
        self.target_config.set_instr_file(self.instrumentation_file)

      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'build')
      kwargs = self.construct_pira_instr_kwargs()
    else:
      log.get_logger().log('Builder::build_flavors: No instrumentation', level='debug')
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'basebuild')
      kwargs = self.construct_pira_kwargs()

    if build_functor.get_method()['active']:
      log.get_logger().log('Builder::build_flavors: Running the passive functor.', level='debug')
      build_functor.active(benchmark, **kwargs)

    else:
      try:
        log.get_logger().log('Builder::build_flavors: Running the passive functor.', level='debug')
        ''' The build command uses CC and CXX to pass flags that are needed by PIRA for the given toolchain. '''
        build_command = build_functor.passive(benchmark, **kwargs)
        clean_command = clean_functor.passive(benchmark, **kwargs)
        log.get_logger().log(
            'Builder::build_flavors: Clean in ' + benchmark + '\n  Using ' + clean_command, level='debug')
        util.shell(clean_command)
        log.get_logger().log('Builder::build_flavors: Building: ' + build_command, level='debug')
        util.shell(build_command)

      except Exception as e:
        log.get_logger().log('Builder::build_flavors: ' + str(e), level='error')
