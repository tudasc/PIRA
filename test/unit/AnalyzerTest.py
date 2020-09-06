"""
File: AnalyzerTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the Analyzer module.
"""

import lib.Analyzer as A
import lib.FunctorManagement as F
import lib.ConfigurationLoader as C

from lib.Configuration import PiraConfiguration, PiraConfigurationII, PiraConfigurationAdapter, PiraItem, TargetConfiguration
from lib.ArgumentMapping import CmdlineLinearArgumentMapper
from lib.ProfileSink import ProfileSinkBase
import unittest

class TestProfileSink(ProfileSinkBase):
  def __init__(self):
    super().__init__()
    self._tc = None
    self._ic = None

  def process(self, exp_dir: str, target_config: TargetConfiguration, instr_config):
    self._sink_target = exp_dir
    self._tc = target_config
    self._ic = instr_config

  def has_config_output(self):
    return False


class TestAnalyzer(unittest.TestCase):

  def setUp(self):
    # Pira I configuration (we probably drop the support anyway...)
    self._p_cfg = PiraConfiguration()

    # Pira II configuration and adapter
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

  def test_empty_pira_config(self):
    with self.assertRaises(A.PiraAnalyzerException):
      analyzer = A.Analyzer(PiraConfiguration())

  def test_empty_pira_configII(self):
    with self.assertRaises(A.PiraAnalyzerException):
      analyzer = A.Analyzer(PiraConfigurationII())

  def test_empty_pira_config_adapter(self):
    with self.assertRaises(A.PiraAnalyzerException):
      analyzer = A.Analyzer(PiraConfigurationAdapter(PiraConfigurationII()))

  def test_pira_configII(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    self.assertIsNotNone(analyzer)

  def test_pira_config_adapter(self):
    analyzer = A.Analyzer(self._pira_two_adapter)
    self.assertIsNotNone(analyzer)

  def test_config_empty_sink(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    tc = TargetConfiguration(self._it_dir, self._it_dir, self._it_dir, 'dflt', 'asdf')
    with self.assertRaises(RuntimeError):
      analyzer.analyze(tc, 0)

  def test_empty_target_config(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    with self.assertRaises(RuntimeError):
      analyzer.analyze(None, 0)

  def test_analyze_local(self):
    ld = C.SimplifiedConfigurationLoader()
    cfg = ld.load_conf('../inputs/configs/basic_config_005.json')

    analyzer = A.Analyzer(cfg)
    fm = F.FunctorManager(cfg)

    a_f = fm.get_or_load_functor('/tmp', 'test_item', 'ct', 'analyze')
    self.assertIsNotNone(a_f)
    self.assertTrue(a_f.get_method()['passive'])
    self.assertEqual(a_f.get_it(), 0)


    tc = TargetConfiguration(cfg.get_place('/tmp'), '/tmp', 'test_item', 'ct', 'asdf')
    with self.assertRaises(RuntimeError) as assert_cm:
      analyzer.analyze(tc, 0)
    rt_err = assert_cm.exception
    self.assertEqual(str(rt_err), 'Analyzer::analyze: Profile Sink in Analyzer not set!')

    analyzer.set_profile_sink(TestProfileSink())
    analyzer.analyze(tc, 0)
    self.assertEqual(a_f.get_it(), 1)

  @unittest.skip('Skip the test of the slurm Analyzer as we do not have any implementation for now.')
  def test_analyze_slurm(self):
    pass
