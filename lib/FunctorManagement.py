"""
File: FunctorManagement.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to load and manage the user-supplied functors.
"""

import typing
import lib.Utility as u
from lib.Configuration import PiraConfiguration
import lib.Logging as log
from lib.Exception import PiraException


class FunctorManagementException(PiraException):
  """The exception indicates a problem with the funtor management"""

  def __init__(self, msg):
    super().__init__(msg)


class FunctorManager:
  """ Entity to query for functors. Needs to be initialized with a PiraConfiguration once per PIRA configuration file.  """

  class __FunctorManagerImpl:

    def __init__(self, cfg: PiraConfiguration) -> None:
      self.config = cfg
      self.functor_cache = {}

    def get_or_load_functor(self, build: str, item: str, flavor: str, func: str):
      '''
      We use the wholename, i.e. fully qualified path to the functor, as the key
      in our functor cache.
      '''
      if func is 'basebuild':
        path, name, wnm = self.get_builder(build, item, flavor, True)
      elif func is 'build':
        path, name, wnm = self.get_builder(build, item, flavor)
      elif func is 'clean':
        path, name, wnm = self.get_cleaner(build, item, flavor)
      elif func is 'analyze':
        path, name, wnm = self.get_analyzer(build, item, flavor)
      elif func is 'run':
        path, name, wnm = self.get_runner(build, item, flavor)
      else:
        raise Exception('No such option available to load functor for. Value = ' + func)

      try:
        _ = self.functor_cache[wnm]
      except KeyError:
        self.functor_cache[wnm] = u.load_functor(path, name)

      log.get_logger().log(
          'FunctorManager::get_or_load: The retrieved ' + func + ' functor: ' + str(self.functor_cache[wnm]),
          level='debug')

      return self.functor_cache[wnm]

    def get_builder(self, build: str, item: str, flavor: str, base: bool = False) -> typing.Tuple[str, str, str]:
      p = self.config.get_builder_path(build, item)
      n = self.get_builder_name(build, item, flavor)
      if base:
        n = u.concat_a_b_with_sep('no_instr', n, '_')
      wnm = self.get_builder_file(build, item, flavor)
      return p, n, wnm

    def get_cleaner(self, build: str, item: str, flavor: str) -> typing.Tuple[str, str, str]:
      p = self.config.get_cleaner_path(build, item)
      n = self.get_cleaner_name(build, item, flavor)
      wnm = self.get_cleaner_file(build, item, flavor)
      return p, n, wnm

    def get_analyzer(self, build: str, item: str, flavor: str) -> typing.Tuple[str, str, str]:
      p = self.config.get_analyzer_path(build, item)
      n = self.get_analyzer_name(build, item, flavor)
      wnm = self.get_analyzer_file(build, item, flavor)
      return p, n, wnm

    def get_runner(self, build: str, item: str, flavor: str) -> typing.Tuple[str, str, str]:
      p = self.config.get_runner_path(build, item)
      n = self.get_runner_name(build, item, flavor)
      wnm = self.get_runner_file(build, item, flavor)
      return p, n, wnm

    def get_raw_name(self, build: str, item: str, flavor: str) -> str:
      b_nm = self.config.get_benchmark_name(item)
      raw_nm = u.concat_a_b_with_sep(b_nm, flavor, '_')
      return raw_nm

    def get_cleaner_name(self, build: str, item: str, flavor: str) -> str:
      raw_nm = self.get_raw_name(build, item, flavor)
      cl_nm = u.concat_a_b_with_sep('clean', raw_nm, '_')
      return cl_nm

    def get_cleaner_file(self, build: str, item: str, flavor: str) -> str:
      path = self.config.get_cleaner_path(build, item)
      nm = self.get_cleaner_name(build, item, flavor)
      file_path = u.concat_a_b_with_sep(path, nm, '/')
      full_path = u.concat_a_b_with_sep(file_path, 'py', '.')
      return full_path

    def get_builder_name(self, build: str, item: str, flavor: str) -> str:
      raw_nm = self.get_raw_name(build, item, flavor)
      # FIXME: remove as soon as the new uniform naming is in place
      return raw_nm
      cl_nm = u.concat_a_b_with_sep('build', raw_nm, '_')
      return cl_nm

    def get_builder_file(self, build: str, item: str, flavor: str) -> str:
      path = self.config.get_builder_path(build, item)
      nm = self.get_builder_name(build, item, flavor)
      file_path = u.concat_a_b_with_sep(path, nm, '/')
      full_path = u.concat_a_b_with_sep(file_path, 'py', '.')
      return full_path

    def get_analyzer_name(self, build: str, item: str, flavor: str) -> str:
      raw_nm = self.get_raw_name(build, item, flavor)
      cl_nm = u.concat_a_b_with_sep('analyse', raw_nm, '_')
      return cl_nm

    def get_analyzer_file(self, build: str, item: str, flavor: str) -> str:
      path = self.config.get_analyzer_path(build, item)
      nm = self.get_analyzer_name(build, item, flavor)
      file_path = u.concat_a_b_with_sep(path, nm, '/')
      full_path = u.concat_a_b_with_sep(file_path, 'py', '.')
      return full_path

    def get_runner_name(self, build: str, item: str, flavor: str) -> str:
      raw_nm = self.get_raw_name(build, item, flavor)
      cl_nm = u.concat_a_b_with_sep('runner', raw_nm, '_')
      return cl_nm

    def get_runner_file(self, build: str, item: str, flavor: str) -> str:
      path = self.config.get_runner_path(build, item)
      nm = self.get_runner_name(build, item, flavor)
      file_path = u.concat_a_b_with_sep(path, nm, '/')
      full_path = u.concat_a_b_with_sep(file_path, 'py', '.')
      return full_path

  instance = None

  def __init__(self, cfg=None):
    if not FunctorManager.instance:
      if cfg is None:
        raise FunctorManagementException('Cannot create from None')

      FunctorManager.instance = FunctorManager.__FunctorManagerImpl(cfg)
    else:
      if cfg is not None:
        FunctorManager.instance.cfg = cfg
        FunctorManager.instance.functor_cache.clear()

  @classmethod
  def from_config(cls, p_config: PiraConfiguration):
    """  Needs to be called once per configuration.  """
    return cls(p_config)

  def __getattr__(self, name):
    return getattr(self.instance, name)
