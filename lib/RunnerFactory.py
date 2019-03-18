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
from lib.Runner import LocalRunner, LocalScalingRunner
from lib.ProfileSink import NopSink, ExtrapProfileSink


class PiraRunnerFactory:

  def __init__(self, invocation_cfg: InvocationConfiguration, configuration: PiraConfiguration):
    self._config = configuration
    self._invoc_cfg = invocation_cfg

  def get_simple_local_runner(self):
    return LocalRunner(self._config, NopSink(), self._invoc_cfg.get_num_repetitions())

  def get_scalability_runner(self, extrap_config: ExtrapConfiguration):
    # TODO Make use of ArgumentMapper here
    attached_sink = ExtrapProfileSink(extrap_config.get_dir(), 'param', extrap_config.get_prefix(), '', 'profile.cubex')
    return LocalScalingRunner(self._config, attached_sink, self._invoc_cfg.get_num_repetitions())
