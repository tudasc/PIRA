"""
File: RunnerFactory.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to create different Runner objects, depending on the configuration.
"""

import sys
sys.path.append('..')

from lib.Configuration import PiraConfiguration, ExtrapConfiguration
from lib.Runner import LocalRunner, LocalScalingRunner
from lib.ProfileSink import NopSink, ExtrapProfileSink


class PiraRunnerFactory:

  def __init__(self, configuration: PiraConfiguration):
    self._config = configuration

  def get_simple_local_runner(self):
    return LocalRunner(self._config, NopSink())

  def get_scalability_runner(self, extrap_config):
    attached_sink = ExtrapProfileSink(extrap_config.get_dir(), 'param', extrap_config.get_prefix(), '', 'profile.cubex')
    return LocalScalingRunner(self._config, attached_sink)
