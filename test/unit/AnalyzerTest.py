"""
File: AnalyzerTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Tests for the Analyzer module.
"""
import lib.Analyzer as A
import lib.FunctorManagement as F
import lib.ConfigurationLoader as C
import lib.Utility as U
from lib.Configuration import PiraConfig, PiraConfigII, PiraConfigAdapter, PiraItem, TargetConfig, InvocationConfig, InstrumentConfig
from lib.ArgumentMapping import CmdlineLinearArgumentMapper
from lib.ProfileSink import ProfileSinkBase

import unittest
import os

class TestProfileSink(ProfileSinkBase):
  def __init__(self):
    super().__init__()
    self._tc = None
    self._ic = None

  def process(self, exp_dir: str, target_config: TargetConfig, instr_config: InstrumentConfig):
    self._sink_target = exp_dir
    self._tc = target_config
    self._ic = instr_config

  def has_config_output(self):
    return False


class TestAnalyzer(unittest.TestCase):

  def setUp(self):
    # Pira I configuration (we probably drop the support anyway...)
    self._p_cfg = PiraConfig()

    # Pira II configuration and adapter
    self._pira_two_cfg = PiraConfigII()
    # get runtime folder
    self.pira_dir = U.get_default_pira_dir()
    # insert user runtime folder into test config
    self.test_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../inputs/configs/basic_config_005.json')
    data = None
    with open(self.test_config, 'r') as file:
      data = file.read()
    data = data.replace('/tmp', self.pira_dir)
    with open(self.test_config, 'w') as file:
      file.write(data)

    self._it_dir = self.pira_dir
    item = PiraItem(os.path.join(self.pira_dir, 'test_item'))
    item.set_analyzer_dir('/analyzer')
    item.set_cubes_dir('/cubes')
    item.set_flavors(['dflt'])
    item.set_functors_base_path('/functors')
    item.set_mode('ct')

    InvocationConfig.create_from_kwargs({'config' : '../inputs/configs/basic_config_005.json'})
    run_opts = CmdlineLinearArgumentMapper({'x': [1]})
    item.set_run_options(run_opts)
    self._item = item

    self._pira_two_cfg.add_item(self._it_dir, item)
    self._pira_two_cfg._empty = False # This is usually done in ConfigurationLoader
    self._pira_two_adapter = PiraConfigAdapter(self._pira_two_cfg)

  def tearDown(self):
    # reset test config
    data = None
    with open(self.test_config, 'r') as file:
      data = file.read()
    data = data.replace(self.pira_dir, '/tmp')
    with open(self.test_config, 'w') as file:
      file.write(data)

  def test_empty_pira_config(self):
    with self.assertRaises(A.PiraAnalyzerException):
      analyzer = A.Analyzer(PiraConfig())

  def test_empty_pira_configII(self):
    with self.assertRaises(A.PiraAnalyzerException):
      analyzer = A.Analyzer(PiraConfigII())

  def test_empty_pira_config_adapter(self):
    with self.assertRaises(A.PiraAnalyzerException):
      analyzer = A.Analyzer(PiraConfigAdapter(PiraConfigII()))

  def test_pira_configII(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    self.assertIsNotNone(analyzer)

  def test_pira_config_adapter(self):
    analyzer = A.Analyzer(self._pira_two_adapter)
    self.assertIsNotNone(analyzer)

  def test_config_empty_sink(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    tc = TargetConfig(self._it_dir, self._it_dir, self._it_dir, 'dflt', 'asdf')
    with self.assertRaises(RuntimeError):
      analyzer.analyze(tc, 0, True)

  def test_empty_target_config(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    with self.assertRaises(RuntimeError):
      analyzer.analyze(None, 0, True)

  def test_run_analyzer_command(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    with self.assertRaises(Exception):
      analyzer.run_analyzer_command('some/command','analyzer/dir','ct','benchmark','exp/dir',0,'cfg/file',False)

  def test_run_analyzer_command_no_instr(self):
    analyzer = A.Analyzer(self._pira_two_cfg)
    with self.assertRaises(Exception):
      analyzer.run_analyzer_command_noInstr('some/command','analyzer/dir','ct','benchmark')


  def test_analyze_local(self):
    ld = C.SimplifiedConfigurationLoader()
    cfg = ld.load_conf()
    analyzer = A.Analyzer(cfg)
    fm = F.FunctorManager(cfg)

    a_f = fm.get_or_load_functor(self.pira_dir, 'test_item', 'ct', 'analyze')
    self.assertIsNotNone(a_f)
    self.assertTrue(a_f.get_method()['passive'])
    self.assertEqual(a_f.get_it(), 0)


    tc = TargetConfig(cfg.get_place(self.pira_dir), self.pira_dir, 'test_item', 'ct', 'asdf')
    with self.assertRaises(RuntimeError) as assert_cm:
      analyzer.analyze(tc, 0, True)
    rt_err = assert_cm.exception
    self.assertEqual(str(rt_err), 'Analyzer::analyze: Profile Sink in Analyzer not set!')

    analyzer.set_profile_sink(TestProfileSink())
    analyzer.analyze(tc, 0, True)
    self.assertEqual(a_f.get_it(), 1)

  @unittest.skip('Skip the test of the slurm Analyzer as we do not have any implementation for now.')
  def test_analyze_slurm(self):
    pass