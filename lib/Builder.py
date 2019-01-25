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

import typing

class Builder:
  """
  Class which builds a benchmark and the run configuration.
  """
  def __init__(self, target_config: TargetConfiguration, instrument: bool) -> None:
    self.target_config = target_config
    self.directory = target_config.get_build()
    self.old_cwd = ''
    self.build_no_instr = not instrument
    self.error = None

  def build(self):
    try:
      self.set_up()
      self.build_detail()
      self.tear_down()

    except Exception as e:
      log.get_logger().log('Caught exception ' + str(e), level='info')
      if self.error:
        raise Exception('Severe Problem in Builder.build')

  def set_up(self) -> None:
    log.get_logger().log('Builder::set_up for ' + self.directory)
    directory_good = util.check_provided_directory(self.directory)
    if directory_good:
      self.old_cwd = util.get_cwd()
      util.change_cwd(self.directory)
    else:
      self.error = True
      raise Exception('Could not change to directory')

  def tear_down(self) -> None:
    util.change_cwd(self.old_cwd)

  def build_detail(self) -> None:
    kwargs = {'compiler': 'clang++'}
    self.build_flavours(kwargs)

  def build_flavours(self, kwargs) -> None:
    log.get_logger().log('Building for ' + self.target_config.get_flavor(), level='debug')
    # benchmark == item
    benchmark_name = PiraConfiguration.get_benchmark_name(self.target_config.get_target())
    log.get_logger().log('Obtained benchmark_name: ' + benchmark_name, level='debug')
    build = self.target_config.get_build()
    benchmark = self.target_config.get_target()
    flavor = self.target_config.get_flavor()
    f_man = fm.FunctorManager() # Returns the currently loaded FM
    clean_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'clean')
    log.get_logger().log('Retrieved clean_functor')

    if self.build_no_instr:
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'basebuild')
    else:
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'build')

    if build_functor.get_method()['active']:
      build_functor.active(benchmark, **kwargs)
    else:
      try:
        log.get_logger().log('Running the passive functor.', level='debug')
        util.change_cwd(build)
        build_command = build_functor.passive(benchmark, **kwargs)
        clean_command = clean_functor.passive(benchmark, **kwargs)
        log.get_logger().log('Making clean in ' + benchmark, level='debug')
        util.shell(clean_command)
        log.get_logger().log('Building with command: ' + build_command, level='debug')
        util.shell(build_command)

      except Exception as e:
        log.get_logger().log(str(e), level='warn')

  def generate_run_configurations(self):
    """
        Generates scripts which are to be submitted to the batch system.
        These are stored in the format ((Benchmark, Flavor), Script_File_Name).
        :return: List of script files
    """
    run_configs = []
    kwargs = {'util': util}
    for flavor in self.config.get_flavors():
      for benchmark in self.config.get_benchmarks():
        run_generator = util.load_functor(self.config.get_flavor_run_generator(flavor))
        # This is always active mode. We need to generate scripts and return the filename.
        rc = run_generator.generate(benchmark, **kwargs)
        run_configs.append(((benchmark, flavor), rc))
    return run_configs
