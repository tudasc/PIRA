"""
File: RunnerFactory.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to create different Runner objects, depending on the configuration.
"""

import lib.Logging as L
from lib.Configuration import PiraConfig, ExtrapConfig
from lib.Configuration import PiraConfigII, PiraConfigAdapter, PiraConfigErrorException
from lib.Runner import LocalRunner, LocalScalingRunner
from lib.ProfileSink import NopSink, ExtrapProfileSink, PiraOneProfileSink


class PiraRunnerFactory:

  def __init__(self, configuration: PiraConfig):
    self._config = configuration


  def get_simple_local_runner(self):
    return LocalRunner(self._config, PiraOneProfileSink())

  def get_scalability_runner(self, extrap_config: ExtrapConfig):
    if self._config.is_empty():
      raise PiraConfigErrorException('Configuration is None in RunnerFactory')

    pc_ii = None
    params = None
    ro = None
    if isinstance(self._config, PiraConfigAdapter):
      L.get_logger().log('PiraRunnerFactory::get_scalability_runner: Configuration is PiraConfigurationAdapter')
      pc_ii = self._config.get_adapted()
    elif isinstance(self._config, PiraConfigII):
      pc_ii = self._config

    if pc_ii is not None:
      L.get_logger().log('PiraRunnerFactory::get_scalability_runner: pc_ii is not none.')

    if pc_ii is not None and isinstance(pc_ii, PiraConfigII):
      L.get_logger().log('PiraRunnerFactory::get_scalability_runner: pc_ii is PiraConfigurationII')
      params = {}
      L.get_logger().log('PiraRunnerFactory::get_scalability_runner: Preparing params')
      for k in pc_ii.get_directories():
        L.get_logger().log('PiraRunnerFactory::get_scalability_runner: ' + str(k))
        for pi in pc_ii.get_items(k):
          L.get_logger().log('PiraRunnerFactory::get_scalability_runner: ' + str(pi))
          # This should be only one element anyway.
          # for p in pi.get_run_options():
          ro = pi.get_run_options()
    #        for pa in p.get_params():
    #          params[pa] = True
    #  L.get_logger().log('PiraRunnerFactory::get_scalability_runner: ' + str(params))
    if params is None:
      raise RuntimeError('PiraRunnerFactory::get_scalability_runner: Cannot use extra-p with old configuration')

    attached_sink = ExtrapProfileSink(extrap_config.get_dir(), ro.get_argmap(), extrap_config.get_prefix(), 'pofi',
                                      'profile.cubex')
    return LocalScalingRunner(self._config, attached_sink)
