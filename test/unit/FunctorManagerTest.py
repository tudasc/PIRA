"""
File: FunctorManagementTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the argument mapping
"""

import lib.ConfigurationLoader as C
from lib.Configuration import InvocationConfig
import lib.FunctorManagement as F
import lib.Configuration as CO
import unittest

class TestFunctorManagerConstruction(unittest.TestCase):
  """
  These tests consider the construction and correct return of singleton functor managers
  """
  def setUp(self):
    InvocationConfig.create_from_kwargs({'config' : './input/unit_input_001.json'})

  def test_construction_from_None(self):
    F.FunctorManager.instance = None
    self.assertIsNone(F.FunctorManager.instance)
    self.assertRaises(F.FunctorManagementException, F.FunctorManager, None)

  def test_construction_from_empty_config(self):
    with self.assertRaises(F.FunctorManagementException):
      fm = F.FunctorManager(CO.PiraConfig())

    with self.assertRaises(F.FunctorManagementException):
      fm = F.FunctorManager(CO.PiraConfigII())

    with self.assertRaises(F.FunctorManagementException):
      fm = F.FunctorManager(CO.PiraConfigAdapter(CO.PiraConfigII()))


  def test_construction_from_config(self):
    cfg_loader = C.ConfigurationLoader()
    fm = F.FunctorManager(cfg_loader.load_conf())
    fm.reset()

  def test_construction_from_classmethod(self):
    cfg_loader = C.ConfigurationLoader()
    fm = F.FunctorManager.from_config(cfg_loader.load_conf())
    fm.reset()

  def test_construction_is_singleton(self):
    F.FunctorManager.instance = None
    self.assertIsNone(F.FunctorManager.instance)
    cfg_loader = C.ConfigurationLoader()
    fm = F.FunctorManager.from_config(cfg_loader.load_conf())
    fm2 = F.FunctorManager()
    self.assertEqual(fm.instance, fm2.instance)
    fm.reset()


class TestFunctorManager(unittest.TestCase):
  """
  These tests perform basic query functions on the FunctorManager to compare the
  awaited filesystem paths are returned for the different flavors
  """
  def setUp(self):
    InvocationConfig.create_from_kwargs({'config' : './input/unit_input_001.json'})
    self.build = '/home/something/top_dir'
    self.b_i_01 = '/builder/item01/directory'
    self.ia_i_01 = '/ins_anal/directory/for/functors'
    self.r_i_01 = '/path/to/runner_functors/item01'
    self.i_01 = 'item01'
    self.flavor = 'vanilla'
    self.cl = C.ConfigurationLoader()
    self.cfg = self.cl.load_conf()
    self.fm = F.FunctorManager(self.cfg)

  def tearDown(self):
    self.fm.reset()

  def test_get_clean_functor_filename(self):
    expected_file_name = 'clean_item01_vanilla'

    cl_func_name = self.fm.get_cleaner_name(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_func_name, expected_file_name)

  def test_get_clean_functor_wholefile(self):
    expected_file_name = 'clean_item01_vanilla.py'
    cl_file = self.fm.get_cleaner_file(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_file, self.b_i_01 + '/' + expected_file_name)

  def test_get_build_functor_filename(self):
    expected_file_name = 'item01_vanilla'

    # TODO Probably want to refactor that. If all the other functors prepend the respective task
    #      to their file name, we should do this with the build functor as well.
    #      However, for the time being just refactor the software design.
    cl_func_name = self.fm.get_builder_name(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_func_name, expected_file_name)

  def test_get_build_functor_wholefile(self):
    expected_file_name = 'item01_vanilla.py'
    cl_file = self.fm.get_builder_file(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_file, self.b_i_01 + '/' + expected_file_name)

  def test_get_analyze_functor_filename(self):
    expected_file_name = 'analyze_item01_vanilla'

    cl_func_name = self.fm.get_analyzer_name(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_func_name, expected_file_name)

  def test_get_analyze_functor_wholefile(self):
    expected_file_name = 'analyze_item01_vanilla.py'
    cl_file = self.fm.get_analyzer_file(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_file, self.ia_i_01 + '/' + expected_file_name)

  def test_get_run_functor_filename(self):
    expected_file_name = 'runner_item01_vanilla'

    # TODO Refactor from 'runner' to 'run' to comply with the overall design
    #      and prepend-schema.
    cl_func_name = self.fm.get_runner_name(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_func_name, expected_file_name)

  def test_get_run_functor_wholefile(self):
    expected_file_name = 'runner_item01_vanilla.py'
    cl_file = self.fm.get_runner_file(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_file, self.r_i_01 + '/' + expected_file_name)

  def test_get_builder(self):
    expected_file_name = 'item01_vanilla'
    path, name, whole_nm = self.fm.get_builder(self.build, self.i_01, self.flavor)
    self.assertEqual(path, self.b_i_01)
    self.assertEqual(name, expected_file_name)
    self.assertEqual(whole_nm, self.b_i_01 + '/' + expected_file_name + '.py')

  def test_get_cleaner(self):
    expected_file_name = 'clean_item01_vanilla'
    path, name, whole_nm = self.fm.get_cleaner(self.build, self.i_01, self.flavor)
    self.assertEqual(path, self.b_i_01)
    self.assertEqual(name, expected_file_name)
    self.assertEqual(whole_nm, self.b_i_01 + '/' + expected_file_name + '.py')

  def test_get_runner(self):
    expected_file_name = 'runner_item01_vanilla'
    path, name, whole_nm = self.fm.get_runner(self.build, self.i_01, self.flavor)
    self.assertEqual(path, self.r_i_01)
    self.assertEqual(name, expected_file_name)
    self.assertEqual(whole_nm, self.r_i_01 + '/' + expected_file_name + '.py')

  def test_get_analyzer(self):
    expected_file_name = 'analyze_item01_vanilla'
    path, name, whole_nm = self.fm.get_analyzer(self.build, self.i_01, self.flavor)
    self.assertEqual(path, self.ia_i_01)
    self.assertEqual(name, expected_file_name)
    self.assertEqual(whole_nm, self.ia_i_01 + '/' + expected_file_name + '.py')


class FunctorManagerFromConfig(unittest.TestCase):
  def setUp(self):
    self.base_path = '../inputs/configs'
    self.cfg001 = 'basic_config_001.json'
    self.cfg002 = 'basic_config_002.json'
    self.cfg003 = 'basic_config_003.json'
    self.cfg004 = 'basic_config_004.json'
    self.scl = C.SimplifiedConfigurationLoader()
    self.fm = None

  def tearDown(self):
    self.fm.reset()

  def get_filename(self, filename):
    return self.base_path + '/' + filename

  @unittest.skip('This requires the correct implementation of PiraConfiguration.is_valid()')
  def test_get_invalid_path(self):
    InvocationConfig.create_from_kwargs({'config' : self.get_filename(self.cfg003)})
    self.assertRaises(CO.PiraConfigErrorException, F.FunctorManager, self.scl.load_conf())

  def test_get_valid_path(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())

  def test_get_runner_functor(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())

  def test_get_builder_functor(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())

  def test_get_analyzer_functor(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())

  def test_get_builder_command(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())

  def test_get_runner_command(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())

  def test_get_analyzer_command(self):
    InvocationConfig.create_from_kwargs({'config': self.get_filename(self.cfg004)})
    self.fm = F.FunctorManager(self.scl.load_conf())


if __name__ == "__main__":
  unittest.main()
