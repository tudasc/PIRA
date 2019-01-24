import sys
sys.path.append('../')

import unittest
import typing

import lib.ConfigLoaderNew as CL
import lib.FunctorManagement as FM


class TestFunctorManagerConstruction(unittest.TestCase):

  """These tests consider the construction and correct return of singleton functor managers"""
  
  def test_construction_from_None(self):
    FM.FunctorManager.instance = None
    self.assertIsNone(FM.FunctorManager.instance)
    self.assertRaises(FM.FunctorManagementException, FM.FunctorManager, None)

  def test_construction_from_None(self):
    self.assertIsNotNone(FM.FunctorManager.instance)
    fm = FM.FunctorManager()
    self.assertIsNotNone(fm)

  def test_construction_from_config(self):
    cfg_loader = CL.ConfigurationLoader()
    fm = FM.FunctorManager(cfg_loader.load_conf('../examples/item_based.json'))

  def test_construction_from_classmethod(self):
    cfg_loader = CL.ConfigurationLoader()
    fm = FM.FunctorManager.from_config(cfg_loader.load_conf('../examples/item_based.json'))

  def test_construction_is_singleton(self):
    FM.FunctorManager.instance = None
    self.assertIsNone(FM.FunctorManager.instance)
    cfg_loader = CL.ConfigurationLoader()
    fm = FM.FunctorManager.from_config(cfg_loader.load_conf('../examples/item_based.json'))
    fm2 = FM.FunctorManager()
    self.assertEqual(fm.instance, fm2.instance)


class TestFunctorManager(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.cl = CL.ConfigurationLoader()
    cls.fm = FM.FunctorManager(cls.cl.load_conf('../examples/item_based.json'))

  def setUp(self):
    self.build = '/home/something/top_dir'
    self.b_i_01 = '/builder/item01/directory'
    self.ia_i_01 = '/ins_anal/directory/for/functors'
    self.r_i_01 = '/path/to/runner_functors/item01'
    self.i_01 = 'item01'
    self.flavor = 'vanilla'

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
    expected_file_name = 'analyse_item01_vanilla'

    cl_func_name = self.fm.get_analyzer_name(self.build, self.i_01, self.flavor)
    self.assertEqual(cl_func_name, expected_file_name)

  def test_get_analyze_functor_wholefile(self):
    expected_file_name = 'analyse_item01_vanilla.py'
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
    expected_file_name = 'analyse_item01_vanilla'
    path, name, whole_nm = self.fm.get_analyzer(self.build, self.i_01, self.flavor)
    self.assertEqual(path, self.ia_i_01)
    self.assertEqual(name, expected_file_name)
    self.assertEqual(whole_nm, self.ia_i_01 + '/' + expected_file_name + '.py')

  def test_get_or_load_functor(self):
    self.assertFalse('We need to test actually loading functors!')



if __name__ == "__main__":
  unittest.main()
