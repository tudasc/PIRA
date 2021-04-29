"""
File: RunnerFactoryTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to create different Runner objects, depending on the configuration.
"""

from lib.RunnerFactory import PiraRunnerFactory
from lib.Configuration import PiraConfig, ExtrapConfig, InvocationConfig, PiraConfigII, \
  PiraConfigAdapter, PiraItem, PiraConfigErrorException
from lib.Runner import LocalRunner, LocalScalingRunner
from lib.ArgumentMapping import CmdlineLinearArgumentMapper
import lib.Utility as U
import unittest
import os


class TestRunnerFactory(unittest.TestCase):
  def setUp(self):
    self._pira_dir = U.get_default_pira_dir()
    self._path_to_config = os.path.join(self._pira_dir, 'config')
    self._compile_t_filter = True
    self._pira_iters = 3
    self._num_reps = 4
    self._pira_one_cfg = PiraConfig()
    self._hybrid_filter_iters = 0
    self._pira_two_cfg = PiraConfigII()
    self._item_name = 'test_item'
    self._it_dir = os.path.join(self._pira_dir, self._item_name)
    item = PiraItem(self._item_name)
    item.set_analyzer_dir('/analyzer')
    item.set_cubes_dir('/cubes')
    item.set_flavors(['dflt'])
    item.set_functors_base_path('/functors')
    item.set_mode('ct')

    InvocationConfig.create_from_kwargs({'config' : 'test/gol_config.json'})
    run_opts = CmdlineLinearArgumentMapper({'x': [1]})
    item.set_run_options(run_opts)
    self._item = item

    self._pira_two_cfg.add_item(self._it_dir, item)
    self._pira_two_cfg._empty = False  # This is usually done in ConfigurationLoader
    self._pira_two_adapter = PiraConfigAdapter(self._pira_two_cfg)

  def test_init_empty_config(self):
    prf = PiraRunnerFactory(PiraConfig())
    self.assertIsNotNone(prf)
    self.assertTrue(isinstance(prf, PiraRunnerFactory))

    prfII = PiraRunnerFactory(PiraConfigII())
    self.assertIsNotNone(prf)
    self.assertTrue(isinstance(prfII, PiraRunnerFactory))

  def test_init_nonempty_config(self):
    prf = PiraRunnerFactory(self._pira_two_cfg)
    self.assertIsNotNone(prf)
    self.assertTrue(isinstance(prf, PiraRunnerFactory))

    prfII = PiraRunnerFactory(self._pira_two_adapter)
    self.assertIsNotNone(prfII)
    self.assertTrue(isinstance(prf, PiraRunnerFactory))

  def test_get_simple_local_runner_empty_config(self):
    prf = PiraRunnerFactory(PiraConfig())
    self.assertIsNotNone(prf)

    runner = prf.get_simple_local_runner()
    self.assertIsNotNone(runner)
    self.assertTrue(isinstance(runner, LocalRunner))
    self.assertTrue(runner.has_sink())

  def test_get_scalability_runner_empty_config(self):
    prf = PiraRunnerFactory(PiraConfig())
    self.assertIsNotNone(prf)

    ep_cfg = ExtrapConfig('/extrap', 'pre', 'post')

    with self.assertRaises(PiraConfigErrorException):
      prf.get_scalability_runner(ep_cfg)

    prfII = PiraRunnerFactory(PiraConfigII())
    self.assertIsNotNone(prfII)

    with self.assertRaises(PiraConfigErrorException):
      prfII.get_scalability_runner(ep_cfg)

  def test_get_scalability_runner_nonempty_config(self):
    prfII = PiraRunnerFactory(self._pira_two_cfg)
    self.assertIsNotNone(prfII)

    ep_cfg = ExtrapConfig('/extrap', 'pre', 'post')

    runner = prfII.get_scalability_runner(ep_cfg)
    self.assertIsNotNone(runner)
    self.assertTrue(isinstance(runner, LocalScalingRunner))

  def test_get_scalability_runner_config_adapter(self):
    prfII = PiraRunnerFactory(self._pira_two_adapter)
    self.assertIsNotNone(prfII)

    ep_cfg = ExtrapConfig('/extrap', 'pre', 'post')

    runner = prfII.get_scalability_runner(ep_cfg)
    self.assertIsNotNone(runner)
    self.assertTrue(isinstance(runner, LocalScalingRunner))
