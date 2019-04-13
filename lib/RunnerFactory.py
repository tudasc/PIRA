"""
File: RunnerFactory.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to create different Runner objects, depending on the configuration.
"""

import sys
sys.path.append('..')

from lib.Configuration import PiraConfiguration, ExtrapConfiguration, InvocationConfiguration
from lib.Configuration import PiraConfigurationII, PiraConfigurationAdapter
from lib.Runner import LocalRunner, LocalScalingRunner
from lib.ProfileSink import NopSink, ExtrapProfileSink
import lib.Logging as log


class PiraRunnerFactory:

  def __init__(self, invocation_cfg: InvocationConfiguration, configuration: PiraConfiguration):
    self._config = configuration
    self._invoc_cfg = invocation_cfg

  def get_simple_local_runner(self):
    return LocalRunner(self._config, NopSink(), self._invoc_cfg.get_num_repetitions())

  def get_scalability_runner(self, extrap_config: ExtrapConfiguration):
    pc_ii = None
    params = None
    ro = None
    if isinstance(self._config, PiraConfigurationAdapter):
      pc_ii = self._config.get_adapted()

    if pc_ii is not None and isinstance(pc_ii, PiraConfigurationII):
      params = {}
      log.get_logger().log('PiraRunnerFactory::get_scalability_runner: Preparing params')
      for k in pc_ii.get_directories():
        for pi in pc_ii.get_items(k):
          # This should be only one element anyway.
          # for p in pi.get_run_options():
          ro = pi.get_run_options()
    #        for pa in p.get_params():
    #          params[pa] = True
    #  log.get_logger().log('PiraRunnerFactory::get_scalability_runner: ' + str(params))
    if params is None:
      raise RuntimeError('PiraRunnerFactory::get_scalability_runner: Cannot use extra-p with old configuration')

    attached_sink = ExtrapProfileSink(extrap_config.get_dir(), ro.get_argmap(), extrap_config.get_prefix(), 'pofi',
                                      'profile.cubex', self._invoc_cfg.get_num_repetitions())
    return LocalScalingRunner(self._config, attached_sink, self._invoc_cfg.get_num_repetitions())
