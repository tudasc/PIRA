"""
File: Builder.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to build the target software.
"""

import lib.Utility as U
import lib.Logging as L
import lib.FunctorManagement as F
import lib.DefaultFlags as D
from lib.Configuration import TargetConfiguration
from lib.Measurement import ScorepSystemHelper
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
    if target_config is None:
      raise BuilderException('Builder::ctor: Target Configuration was None')

    self.target_config = target_config
    self.directory = target_config.get_place()
    self.old_cwd = ''
    self.build_instr = instrument
    self.instrumentation_file = instr_file
    self._compile_time_filtering = target_config.is_compile_time_filtering()
    self.error = None

  def build(self) -> None:
    try:
      self.set_up()
      self.build_detail()
      self.tear_down()

    except BuilderException as e:
      L.get_logger().log('Builder::build: Caught exception ' + str(e), level='warn')
      if self.error:
        raise Exception('Severe Problem in Builder::build')

  def set_up(self) -> None:
    L.get_logger().log('Builder::set_up for ' + self.directory)
    directory_good = U.check_provided_directory(self.directory)
    if directory_good:
      self.old_cwd = U.get_cwd()
      U.change_cwd(self.directory)
    else:
      self.error = True
      raise Exception('Builder::set_up: Could not change to directory')

  def tear_down(self) -> None:
    U.change_cwd(self.old_cwd)

  def build_detail(self) -> None:
    kwargs = {'compiler': 'clang++'}
    self.build_flavors(kwargs)

  def construct_pira_instr_kwargs(self) -> typing.Dict:
    L.get_logger().log('Builder::construct_pira_instr_keywords', level='debug')
    if not self.build_instr:
      raise BuilderException('Should not construct instrument kwargs in non-instrumentation mode.')

    pira_cc = ScorepSystemHelper.get_scorep_compliant_CC_command(self.instrumentation_file,
                                                                 self._compile_time_filtering)
    pira_cxx = ScorepSystemHelper.get_scorep_compliant_CXX_command(self.instrumentation_file,
                                                                   self._compile_time_filtering)
    pira_clflags = ScorepSystemHelper.get_scorep_needed_libs_c()
    pira_cxxlflags = ScorepSystemHelper.get_scorep_needed_libs_cxx()
    default_provider = D.BackendDefaults()
    pira_name = default_provider.get_default_exe_name()

    pira_kwargs = {
        'CC': pira_cc,
        'CXX': pira_cxx,
        'CLFLAGS': pira_clflags,
        'CXXLFLAGS': pira_cxxlflags,
        'PIRANAME': pira_name,
        'NUMPROCS': default_provider.get_default_number_of_processes(),
        'filter-file': self.instrumentation_file
    }
    L.get_logger().log('Builder::construct_pira_instr_keywords Returning.', level='debug')
    return pira_kwargs

  def construct_pira_kwargs(self) -> typing.Dict:
    L.get_logger().log('Builder::construct_pira_keywords', level='debug')
    if self.build_instr:
      raise BuilderException('Should not construct non-instrument kwargs in instrumentation mode.')

    default_provider = D.BackendDefaults()

    kwargs = default_provider.get_default_kwargs()
    kwargs['CLFLAGS'] = ''
    kwargs['CXXLFLAGS'] = ''

    L.get_logger().log('Builder::construct_pira_keywords Returning.', level='debug')
    return kwargs

  def check_build_prerequisites(self) -> None:
    return
    ScorepSystemHelper.check_build_prerequisites()

  def build_flavors(self, kwargs) -> None:
    L.get_logger().log(
        'Builder::build_flavors: Building for ' + self.target_config.get_target() + ' in ' +
        self.target_config.get_flavor(),
        level='debug')
    build = self.target_config.get_build()
    benchmark = self.target_config.get_target()
    flavor = self.target_config.get_flavor()
    f_man = F.FunctorManager()  # Returns the currently loaded FM
    clean_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'clean')
    kwargs = {}

    if self.build_instr:
      L.get_logger().log('Builder::build_flavors: Instrumentation', level='debug')
      try:
        self.check_build_prerequisites()
        L.get_logger().log('Builder::build_flavors: Prerequisite check successfull.')
      except Exception as e:
        raise BuilderException('Precheck failed.\n' + str(e))

      if not self.target_config.is_compile_time_filtering():
        L.get_logger().log('Builder::build_flavors: Runtime filtering enabled.')
        self.target_config.set_instr_file(self.instrumentation_file)

      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'build')
      kwargs = self.construct_pira_instr_kwargs()
      ScorepSystemHelper.prepare_MPI_filtering(self.instrumentation_file)

    else:
      L.get_logger().log('Builder::build_flavors: No instrumentation', level='debug')
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'basebuild')
      kwargs = self.construct_pira_kwargs()

    if build_functor.get_method()['active']:
      L.get_logger().log('Builder::build_flavors: Running the passive functor.', level='debug')
      build_functor.active(benchmark, **kwargs)

    else:
      try:
        L.get_logger().log('Builder::build_flavors: Running the passive functor.', level='debug')
        ''' The build command uses CC and CXX to pass flags that are needed by PIRA for the given toolchain. '''
        build_command = build_functor.passive(benchmark, **kwargs)
        clean_command = clean_functor.passive(benchmark, **kwargs)
        L.get_logger().log(
            'Builder::build_flavors: Clean in ' + benchmark + '\n  Using ' + clean_command, level='debug')
        U.shell(clean_command)
        L.get_logger().log('Builder::build_flavors: Building: ' + build_command, level='debug')
        U.shell(build_command)

      except Exception as e:
        L.get_logger().log('Builder::build_flavors: ' + str(e), level='error')
