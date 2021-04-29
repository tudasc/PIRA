"""
File: ConfigLoaderNewTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the ConfigurationLoader module.
"""

import lib.Logging as L
from lib.ConfigurationLoader import ConfigurationLoader, SimplifiedConfigurationLoader
from lib.Configuration import PiraConfigAdapter, PiraConfigII, InvocationConfig
import os
import unittest


logger = L.get_logger()
logger.set_state('debug')
logger.set_state('info')
logger.set_state('warn')

# These assertable values are "old" and refer to the config version 1.0
dep_aw_items = ['item01', 'item02']

dep_aw_builds = ['/home/something/top_dir']

dep_aw_flavors = {'item01': ['local-flav1', 'vanilla'], 'item02': ['local-flav1']}

dep_aw_ins_anal = {
    'item01': ['/ins_anal/directory/for/functors', '/where/to/put/cube/files', '/path/to/analysis/tool'],
    'item02': ['/item02/path/to/functors', '/shared/work/cubes', '/directory/where_to/find/analyzer']
}

dep_aw_builders = {'item01': '/builder/item01/directory', 'item02': '/another/builder/directory/for/item02'}

dep_aw_run = {
    'item01': {
        'args': [],
        'runner': '/path/to/runner_functors/item01',
        'submitter': '/another/path/to/item01/submitter',
        'batch_script': '/some/madeup/script.sh'
    },
    'item02': {
        'args': ['-i 200', '-g 100'],
        'runner': '/item02/runner/functors.dir',
        'submitter': '',
        'batch_script': ''
    }
}


class TestConfigLoader(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.loader = ConfigurationLoader()
    InvocationConfig.create_from_kwargs({'config' : './input/unit_input_001.json'})

  def test_load_conf_not_none(self):
    cfg = self.loader.load_conf()
    self.assertIsNotNone(cfg)

  def test_conf_builds(self):
    cfg = self.loader.load_conf()
    bs = cfg.get_builds()
    self.assertIsNotNone(bs)
    for b in bs:
      self.assertIn(b, dep_aw_builds)

  def test_conf_items(self):
    cfg = self.loader.load_conf()
    for b in cfg.get_builds():
      itms = cfg.get_items(b)
      self.assertIsNotNone(itms)
      for i in itms:
        self.assertIn(i, dep_aw_items)

  def test_config_item01(self):
    cfg = self.loader.load_conf()
    # As the dicts are unordered, we set the keys manually!
    b = '/home/something/top_dir'
    i_01 = 'item01'

    builder = cfg.get_flavor_func(b, i_01)
    self.assertIsNotNone(builder)
    self.assertIn(builder, dep_aw_builders[i_01])

    expected_item = 'item01'
    anal_func_dir = cfg.get_analyze_func(b, i_01)
    self.assertEqual(anal_func_dir, dep_aw_ins_anal[expected_item][0])
    cube_path = cfg.get_analyzer_exp_dir(b, i_01)
    self.assertEqual(cube_path, dep_aw_ins_anal[expected_item][1])
    tool_path = cfg.get_analyzer_dir(b, i_01)
    self.assertEqual(tool_path, dep_aw_ins_anal[expected_item][2])

    runner = cfg.get_runner_func(b, i_01)
    self.assertEqual(runner, dep_aw_run[expected_item]['runner'])
    submitter = cfg.get_submitter_func(b, i_01)
    self.assertEqual(submitter, dep_aw_run[expected_item]['submitter'])
    bs = cfg.get_batch_script_func(b, i_01)
    self.assertEqual(bs, dep_aw_run[expected_item]['batch_script'])

    flvs = cfg.get_flavors(b, i_01)
    self.assertEqual(flvs, dep_aw_flavors[expected_item])

    args = cfg.get_args(b, i_01)
    self.assertListEqual(args[0], dep_aw_run[expected_item]['args'])

  def test_config_item02(self):
    cfg = self.loader.load_conf()
    # As the dicts are unordered, we set the keys manually!
    b = '/home/something/top_dir'
    i_02 = 'item02'

    builder = cfg.get_flavor_func(b, i_02)
    self.assertIsNotNone(builder)
    self.assertIn(builder, dep_aw_builders[i_02])

    expected_item = 'item02'
    anal_func_dir = cfg.get_analyze_func(b, i_02)
    self.assertEqual(anal_func_dir, dep_aw_ins_anal[expected_item][0])
    cube_path = cfg.get_analyzer_exp_dir(b, i_02)
    self.assertEqual(cube_path, dep_aw_ins_anal[expected_item][1])
    tool_path = cfg.get_analyzer_dir(b, i_02)
    self.assertEqual(tool_path, dep_aw_ins_anal[expected_item][2])

    runner = cfg.get_runner_func(b, i_02)
    self.assertEqual(runner, dep_aw_run[expected_item]['runner'])
    submitter = cfg.get_submitter_func(b, i_02)
    self.assertEqual(submitter, dep_aw_run[expected_item]['submitter'])
    bs = cfg.get_batch_script_func(b, i_02)
    self.assertEqual(bs, dep_aw_run[expected_item]['batch_script'])

    flvs = cfg.get_flavors(b, i_02)
    self.assertEqual(flvs, dep_aw_flavors[expected_item])

    args = cfg.get_args(b, i_02)
    self.assertListEqual(args[0], dep_aw_run[expected_item]['args'])
    self.assertFalse(cfg.is_submitter(b, i_02))

  @unittest.skip('Global flavors are currently not implemented')
  def test_global_flavors(self):
    # TODO implement tests for retrieving global flavors
    self.assertFalse('Need to check global flavors')

  @unittest.skip('Global flavors are currently not implemented')
  def test_generated_items(self):
    # TODO build_directory, cube_directory, analyzer_dir, ..?
    self.assertFalse('Need to check global flavors')


n_functor_path = {'item01': '/directory/for/functors/item01', 'item02': '/directory/for/functors/item02'}
n_analysis_path = '/path/to/analysis/tool'
n_cube_path = {'item01': '/where/to/put/cube/files', 'item02': '/where/to/put/cube/files/item02'}
n_flavors = {'item01': ['local-flav1', 'vanilla'], 'item02': ['test-flav']}


class TestSimplifiedConfigLoader(unittest.TestCase):

  #@classmethod
  def setUp(self):
    self.loader = SimplifiedConfigurationLoader()
    InvocationConfig.create_from_kwargs({'config' : './input/unit_input_002.json'})

  def test_load_conf_not_none(self):
    cfg = self.loader.load_conf()
    self.assertIsNotNone(cfg)

  def test_conf_builds(self):
    cfg = self.loader.load_conf()
    bs = cfg.get_builds()
    self.assertIsNotNone(bs)
    for b in bs:
      self.assertIn(b, ['/this/is/my/home'])

  def test_conf_items(self):
    cfg = self.loader.load_conf()
    for b in cfg.get_builds():
      itms = cfg.get_items(b)
      self.assertIsNotNone(itms)
      for i in itms:
        self.assertIn(i, dep_aw_items)

  def test_config_item01(self):
    cfg = self.loader.load_conf()
    # As the dicts are unordered, we set the keys manually!
    b = '/this/is/my/home'
    i_01 = 'item01'

    expected_item = 'item01'
    anal_func_dir = cfg.get_analyzer_path(b, i_01)
    self.assertEqual(anal_func_dir, n_functor_path[expected_item])
    cube_path = cfg.get_analyzer_exp_dir(b, i_01)
    self.assertEqual(cube_path, n_cube_path[expected_item])
    tool_path = cfg.get_analyzer_dir(b, i_01)
    self.assertEqual(tool_path, n_analysis_path)

    runner = cfg.get_runner_func(b, i_01)
    self.assertEqual(runner, n_functor_path[expected_item])

    flvs = cfg.get_flavors(b, i_01)
    self.assertEqual(flvs, n_flavors[expected_item])

    args = cfg.get_args(b, i_01)
    # FIXME correct asserted args
    self.assertListEqual(args, [('param1', 'val1', 'param2', 'val3'), ('param1', 'val1', 'param2', 'val4'),
                                ('param1', 'val2', 'param2', 'val3'), ('param1', 'val2', 'param2', 'val4'),
                                ('param2', 'val3', 'param1', 'val1'), ('param2', 'val3', 'param1', 'val2'),
                                ('param2', 'val4', 'param1', 'val1'), ('param2', 'val4', 'param1', 'val2')])

  def test_config_item02(self):
    cfg = self.loader.load_conf()
    # As the dicts are unordered, we set the keys manually!
    b = '/this/is/my/home'
    i_02 = 'item02'

    builder = cfg.get_builder_path(b, i_02)
    self.assertIsNotNone(builder)
    self.assertIn(builder, n_functor_path[i_02])

    expected_item = 'item02'
    anal_func_dir = cfg.get_analyzer_path(b, i_02)
    self.assertEqual(anal_func_dir, n_functor_path[expected_item])
    cube_path = cfg.get_analyzer_exp_dir(b, i_02)
    self.assertEqual(cube_path, n_cube_path[expected_item])
    tool_path = cfg.get_analyzer_dir(b, i_02)
    self.assertEqual(tool_path, n_analysis_path)

    runner = cfg.get_runner_func(b, i_02)
    self.assertEqual(runner, n_functor_path[expected_item])

    flvs = cfg.get_flavors(b, i_02)
    self.assertEqual(flvs, n_flavors[expected_item])

    args = cfg.get_args(b, i_02)
    # FIXME correct asserted args
    self.assertListEqual([tuple(x) for x in args], [('param1', 'val1'), ('param1', 'val2'), ('param1', 'val3')])

  def test_config_linear_mapper(self):
    InvocationConfig.create_from_kwargs({'config' : './input/unit_input_003.json'})
    cfg = self.loader.load_conf()
    # As the dicts are unordered, we set the keys manually!
    b = '/this/is/my/home'
    i_01 = 'item01'

    self.assertIsNotNone(cfg)

    builder = cfg.get_builder_path(b, i_01)
    self.assertIsNotNone(builder)
    self.assertIn(builder, n_functor_path[i_01])

    expected_item = 'item01'
    anal_func_dir = cfg.get_analyzer_path(b, i_01)
    self.assertEqual(anal_func_dir, n_functor_path[expected_item])
    cube_path = cfg.get_analyzer_exp_dir(b, i_01)
    self.assertEqual(cube_path, '/where/to/put/cube/files/item01')
    tool_path = cfg.get_analyzer_dir(b, i_01)
    self.assertEqual(tool_path, n_analysis_path)

    runner = cfg.get_runner_func(b, i_01)
    self.assertEqual(runner, n_functor_path[expected_item])

    flvs = cfg.get_flavors(b, i_01)
    self.assertEqual(flvs, ['test'])

    args = cfg.get_args(b, i_01)
    # FIXME correct asserted args
    expected = [ ('param1', 'val1', [], 'param2', 'yval1', []),
                  ('param1', 'val2', [], 'param2', 'yval2', []),
                  ('param1', 'val3', [], 'param2', 'yval3', []) ]
    #self.assertListEqual(args, [('param1', 'val1', 'param2', 'yval1'), ('param1', 'val2', 'param2', 'yval2'),
    #                            ('param1', 'val3', 'param2', 'yval3')])

    for (exp, arg) in zip(expected, args):
      self.assertEqual(exp, tuple(arg))

  def test_basic_config_001(self):
    InvocationConfig.create_from_kwargs({'config' : '../inputs/configs/basic_config_001.json'})
    cfg = self.loader.load_conf()
    self.assertIsNotNone(cfg)
    self.assertFalse(cfg.is_empty())

  def test_relative_paths(self):
    InvocationConfig.create_from_kwargs({'config' : '../inputs/configs/basic_config_005.json'})
    cfg = self.loader.load_conf()
    self.assertFalse(cfg.is_empty())
    self.assertTrue(isinstance(cfg, PiraConfigAdapter))
    self.assertTrue(isinstance(cfg.get_adapted(), PiraConfigII))

  def test_env_var_expansion(self):
    expected_base = '/base'
    expected_analyzer = '/analyzer_dir'
    expected_cubes = '/cubes_dir'
    expected_functors = '/functors_dir'

    os.environ['PIRA_TEST_ENV_VAR_BASE'] = expected_base
    os.environ['PIRA_TEST_ENV_VAR_ANALYZER'] = expected_analyzer
    os.environ['PIRA_TEST_ENV_VAR_CUBES'] = expected_cubes
    os.environ['PIRA_TEST_ENV_VAR_FUNCTORS'] = expected_functors


    b = expected_base
    i = 'test_item'
    InvocationConfig.create_from_kwargs({'config' : '../inputs/configs/basic_config_006.json'})
    cfg = self.loader.load_conf()
    self.assertIsNotNone(cfg)
    self.assertFalse(cfg.is_empty())

    base_dir = cfg.get_place(b)
    self.assertEqual(base_dir, expected_base)

    analyzer_dir = cfg.get_analyzer_dir(b, i)
    self.assertEqual(analyzer_dir, expected_analyzer)

    cubes_dir = cfg.get_analyzer_exp_dir(b, i)
    self.assertEqual(cubes_dir, expected_cubes)

    functor_dir = cfg.get_cleaner_path(b, i)
    self.assertEqual(functor_dir, expected_functors)

if __name__ == '__main__':
  unittest.main()
