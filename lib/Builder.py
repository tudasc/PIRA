"""
File: Builder.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to build the target software.
"""

import lib.Utility as util
import lib.Logging as log
import lib.FunctorManagement as fm
# XXX Remove this once it is refactored.
from lib.Configuration import TargetConfiguration, PiraConfiguration
from lib.Measurement import ScorepSystemHelper
import lib.DefaultFlags as defaults

import typing


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
    self.error = None

  def build(self):
    try:
      self.set_up()
      self.build_detail()
      self.tear_down()

    except Exception as e:
      log.get_logger().log('Builder::build: Caught exception ' + str(e), level='info')
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
    pira_cc = ScorepSystemHelper.get_scorep_compliant_CC_command(self.instrumentation_file)
    pira_cxx = ScorepSystemHelper.get_scorep_compliant_CXX_command(self.instrumentation_file)
    pira_clflags = ScorepSystemHelper.get_scorep_needed_libs()
    pira_cxxlflags = ScorepSystemHelper.get_scorep_needed_libs()
    pira_name = 'pira.built.exe'

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
    pira_cc = defaults.get_default_c_compiler_name()
    pira_cxx = defaults.get_default_cpp_compiler_name()
    pira_name = 'pira.built.exe'

    kwargs = {'CC': pira_cc, 'CXX': pira_cxx, 'CLFLAGS': '', 'CXXLFLAGS': '', 'PIRANAME': pira_name}
    log.get_logger().log('Builder::construct_pira_keywords Returning.', level='debug')
    return kwargs

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
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'build')
      kwargs = self.construct_pira_instr_kwargs()
    else:
      log.get_logger().log('Builder::build_flavors: No instrumentation', level='debug')
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'basebuild')
      kwargs = self.construct_pira_kwargs()

    if build_functor.get_method()['active']:
      build_functor.active(benchmark, **kwargs)
    else:
      try:
        log.get_logger().log('Builder::build_flavors: Running the passive functor.', level='debug')
        util.change_cwd(build)
        ''' TODO The build command uses CC and CXX to pass flags that are needed by PIRA for the given toolchain. '''
        build_command = build_functor.passive(benchmark, **kwargs)
        clean_command = clean_functor.passive(benchmark, **kwargs)
        log.get_logger().log(
            'Builder::build_flavors: Clean in ' + benchmark + '\n  Using ' + clean_command, level='debug')
        util.shell(clean_command)
        log.get_logger().log('Builder::build_flavors: Building: ' + build_command, level='debug')
        util.shell(build_command)

      except Exception as e:
        log.get_logger().log('Builder::build_flavors: ' + str(e), level='warn')
