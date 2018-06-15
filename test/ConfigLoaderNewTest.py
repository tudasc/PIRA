import sys
sys.path.append('../')

import unittest
import typing

from lib.ConfigLoaderNew import ConfigurationLoader as CL
import lib.Logging as logging
import lib.Utility as util

logger = logging.get_logger()
logger.set_state('debug')
logger.set_state('info')
logger.set_state('warn')

aw_items = ['item01', 'item02']

aw_builds = ['/home/something/top_dir']

aw_flavors = {'item01': ['local-flav1', 'vanilla'], 'item02': ['local-flav1']}

aw_ins_anal = {
    'item01': ['/ins_anal/directory/for/functors', '/where/to/put/cube/files', '/path/to/analysis/tool'],
    'item02': ['/item02/path/to/functors', '/shared/work/cubes', '/directory/where_to/find/analyzer']
}

aw_builders = {'item01': '/builder/item01/directory', 'item02': '/another/builder/directory/for/item02'}

aw_run = {
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
    cls.loader = CL()

  def test_load_conf_not_none(self):
    cfg = self.loader.load_conf('../examples/item_based.json')
    self.assertIsNotNone(cfg)

  def test_conf_builds(self):
    cfg = self.loader.load_conf('../examples/item_based.json')
    bs = cfg.get_builds()
    self.assertIsNotNone(bs)
    for b in bs:
      self.assertIn(b, aw_builds)

  def test_conf_items(self):
    cfg = self.loader.load_conf('../examples/item_based.json')
    for b in cfg.get_builds():
      itms = cfg.get_items(b)
      self.assertIsNotNone(itms)
      for i in itms:
        self.assertIn(i, aw_items)

  def test_config_item01(self):
    cfg = self.loader.load_conf('../examples/item_based.json')
    # As the dicts are unordered, we set the keys manually!
    b = '/home/something/top_dir'
    i_01 = 'item01'

    builder = cfg.get_flavor_func(b, i_01)
    self.assertIsNotNone(builder)
    self.assertIn(builder, aw_builders[i_01])

    expected_item = 'item01'
    anal_func_dir = cfg.get_analyse_func(b, i_01)
    self.assertEqual(anal_func_dir, aw_ins_anal[expected_item][0])
    cube_path = cfg.get_analyser_exp_dir(b, i_01)
    self.assertEqual(cube_path, aw_ins_anal[expected_item][1])
    tool_path = cfg.get_analyser_dir(b, i_01)
    self.assertEqual(tool_path, aw_ins_anal[expected_item][2])

    runner = cfg.get_runner_func(b, i_01)
    self.assertEqual(runner, aw_run[expected_item]['runner'])
    submitter = cfg.get_submitter_func(b, i_01)
    self.assertEqual(submitter, aw_run[expected_item]['submitter'])
    bs = cfg.get_batch_script_func(b, i_01)
    self.assertEqual(bs, aw_run[expected_item]['batch_script'])

    flvs = cfg.get_flavors(b, i_01)
    self.assertEqual(flvs, aw_flavors[expected_item])

    args = cfg.get_args(b, i_01)
    self.assertListEqual(args, aw_run[expected_item]['args'])

  def test_config_item02(self):
    cfg = self.loader.load_conf('../examples/item_based.json')
    # As the dicts are unordered, we set the keys manually!
    b = '/home/something/top_dir'
    i_02 = 'item02'

    builder = cfg.get_flavor_func(b, i_02)
    self.assertIsNotNone(builder)
    self.assertIn(builder, aw_builders[i_02])

    expected_item = 'item02'
    anal_func_dir = cfg.get_analyse_func(b, i_02)
    self.assertEqual(anal_func_dir, aw_ins_anal[expected_item][0])
    cube_path = cfg.get_analyser_exp_dir(b, i_02)
    self.assertEqual(cube_path, aw_ins_anal[expected_item][1])
    tool_path = cfg.get_analyser_dir(b, i_02)
    self.assertEqual(tool_path, aw_ins_anal[expected_item][2])

    runner = cfg.get_runner_func(b, i_02)
    self.assertEqual(runner, aw_run[expected_item]['runner'])
    submitter = cfg.get_submitter_func(b, i_02)
    self.assertEqual(submitter, aw_run[expected_item]['submitter'])
    bs = cfg.get_batch_script_func(b, i_02)
    self.assertEqual(bs, aw_run[expected_item]['batch_script'])

    flvs = cfg.get_flavors(b, i_02)
    self.assertEqual(flvs, aw_flavors[expected_item])

    args = cfg.get_args(b, i_02)
    self.assertListEqual(args, aw_run[expected_item]['args'])
    self.assertFalse(cfg.is_submitter(b, i_02))

  def test_global_flavors(self):
    # TODO implement tests for retrieving global flavors
    pass

  def test_generated_items(self):
    # TODO build_directory, cube_directory, analyzer_dir, ..?
    pass


if __name__ == '__main__':
  unittest.main()
