"""
File: RunnerFactoryTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to create different Runner objects, depending on the configuration.
"""

from lib.RunnerFactory import PiraRunnerFactory
from lib.Configuration import PiraConfiguration, ExtrapConfiguration, InvocationConfiguration, PiraConfigurationII, PiraConfigurationAdapter, PiraItem, PiraConfigurationErrorException
from lib.Runner import LocalRunner, LocalScalingRunner
from lib.ProfileSink import NopSink, ExtrapProfileSink, PiraOneProfileSink
from lib.ArgumentMapping import CmdlineLinearArgumentMapper

import unittest
import os

class TestRunnerFactory(unittest.TestCase):
  def setUp(self):
    self._path_to_config = '/tmp'
    self._pira_dir = os.path.join(os.path.expanduser('~'), '.pira')
    self._compile_t_filter = True
    self._pira_iters = 3
    self._num_reps = 4
    self._ic = InvocationConfiguration(self._path_to_config, self._compile_t_filter, self._pira_iters, self._num_reps)
    self._pira_one_cfg = PiraConfiguration()

    self._pira_two_cfg = PiraConfigurationII()
    self._it_dir = '/tmp/test_item'
    item = PiraItem('/tmp/test_item')
    item.set_analyzer_dir('/analyzer')
    item.set_cubes_dir('/cubes')
    item.set_flavors(['dflt'])
    item.set_functors_base_path('/functors')
    item.set_mode('ct')

    run_opts = CmdlineLinearArgumentMapper({'x': [1]})

    item.set_run_options(run_opts)
    self._item = item

    self._pira_two_cfg.add_item(self._it_dir, item)
    self._pira_two_cfg._empty = False # This is usually done in ConfigurationLoader
    self._pira_two_adapter = PiraConfigurationAdapter(self._pira_two_cfg)


  def test_init_empty_config(self):
    prf = PiraRunnerFactory(self._ic, PiraConfiguration())
    self.assertIsNotNone(prf)
    self.assertTrue(isinstance(prf, PiraRunnerFactory))

    prfII = PiraRunnerFactory(self._ic, PiraConfigurationII())
    self.assertIsNotNone(prf)
    self.assertTrue(isinstance(prfII, PiraRunnerFactory))

  def test_init_nonempty_config(self):
    prf = PiraRunnerFactory(self._ic, self._pira_two_cfg)
    self.assertIsNotNone(prf)
    self.assertTrue(isinstance(prf, PiraRunnerFactory))

    prfII = PiraRunnerFactory(self._ic, self._pira_two_adapter)
    self.assertIsNotNone(prfII)
    self.assertTrue(isinstance(prf, PiraRunnerFactory))

  def test_get_simple_local_runner_empty_config(self):
    prf = PiraRunnerFactory(self._ic, PiraConfiguration())
    self.assertIsNotNone(prf)

    runner = prf.get_simple_local_runner()
    self.assertIsNotNone(runner)
    self.assertTrue(isinstance(runner, LocalRunner))
    self.assertTrue(runner.has_sink())

  def test_get_scalability_runner_empty_config(self):
    prf = PiraRunnerFactory(self._ic, PiraConfiguration())
    self.assertIsNotNone(prf)

    ep_cfg = ExtrapConfiguration('/extrap', 'pre', 'post')

    with self.assertRaises(PiraConfigurationErrorException):
      prf.get_scalability_runner(ep_cfg)

    prfII = PiraRunnerFactory(self._ic, PiraConfigurationII())
    self.assertIsNotNone(prfII)

    with self.assertRaises(PiraConfigurationErrorException):
      prfII.get_scalability_runner(ep_cfg)

  def test_get_scalability_runner_nonempty_config(self):
    prfII = PiraRunnerFactory(self._ic, self._pira_two_cfg)
    self.assertIsNotNone(prfII)
    
    ep_cfg = ExtrapConfiguration('/extrap', 'pre', 'post')

    runner = prfII.get_scalability_runner(ep_cfg)
    self.assertIsNotNone(runner)
    self.assertTrue(isinstance(runner, LocalScalingRunner))

  def test_get_scalability_runner_config_adapter(self):
    prfII = PiraRunnerFactory(self._ic, self._pira_two_adapter)
    self.assertIsNotNone(prfII)
    
    ep_cfg = ExtrapConfiguration('/extrap', 'pre', 'post')

    runner = prfII.get_scalability_runner(ep_cfg)
    self.assertIsNotNone(runner)
    self.assertTrue(isinstance(runner, LocalScalingRunner))
