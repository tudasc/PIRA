"""
File: BuilderTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Unit test for the Builder class.
"""

import unittest
import lib.Builder as B
import lib.Configuration as C
import lib.ConfigurationLoader as CO


class BuilderTest(unittest.TestCase):

  def setUp(self):
    C.InvocationConfig.create_from_kwargs({'config' : '../inputs/configs/basic_config_005.json'})
    ld = CO.SimplifiedConfigurationLoader()
    self.cfg = ld.load_conf()
    pass

  def test_init(self):
    tc = C.TargetConfig(self.cfg.get_place('/tmp'), '/tmp', 'test_item', 'ct', 'asdf')
    builder = B.Builder(tc, True)
    self.assertIsNotNone(builder)
    self.assertIsNone(builder.error)
    self.assertIsNone(builder.instrumentation_file)
    self.assertTrue(builder.build_instr)
    self.assertEqual(builder.directory, '/tmp')

  def test_init_tc_none(self):
    with self.assertRaises(B.BuilderException) as cm_b:
      builder = B.Builder(None, True)
    b_exc = cm_b.exception
    self.assertEqual(str(b_exc), 'Builder::ctor: Target Configuration was None')

  @unittest.skip('Builder::set_up mainly changes directories. How to test?')
  def test_set_up(self):
    self.assertFalse(True)

  def test_construct_pira_kwargs_fail_instr(self):
    tc = C.TargetConfig(self.cfg.get_place('/tmp'), '/tmp', 'test_item', 'ct', 'asdf')
    builder = B.Builder(tc, True, '/tmp/instr_file')
    self.assertIsNotNone(builder)
    self.assertIsNotNone(builder.instrumentation_file)

    with self.assertRaises(B.BuilderException) as cm_b:
      p_kwargs = builder.construct_pira_kwargs()

    exc = cm_b.exception
    self.assertEqual(str(exc), 'Should not construct non-instrument kwargs in instrumentation mode.')

  def test_construct_pira_kwargs(self):
    tc = C.TargetConfig(self.cfg.get_place('/tmp'), '/tmp', 'test_item', 'ct', 'asdf')
    builder = B.Builder(tc, False, '/tmp/instr_file')
    self.assertIsNotNone(builder)
    self.assertIsNotNone(builder.instrumentation_file)

    p_kwargs = builder.construct_pira_kwargs()
    self.assertEqual(p_kwargs['CC'], '\"clang\"')
    self.assertEqual(p_kwargs['CXX'], '\"clang++\"')
    self.assertEqual(p_kwargs['PIRANAME'], 'pira.built.exe')
    self.assertEqual(p_kwargs['NUMPROCS'], 8)

  @unittest.skip('Implement this test, when fully switched to internal Score-P')
  def test_construct_pira_instr_kwargs(self):
    tc = C.TargetConfig(self.cfg.get_place('/tmp'), '/tmp', 'test_item', 'ct', 'asdf')
    builder = B.Builder(tc, True, '/tmp/instr_file')
    self.assertIsNotNone(builder)
    self.assertIsNotNone(builder.instrumentation_file)

    p_kwargs = builder.construct_pira_instr_kwargs()
    self.assertEqual(p_kwargs['CC'],'\"clang -finstrument-functions -finstrument-functions-whitelist-inputfile=/tmp/instr_file\"')
    self.assertEqual(p_kwargs['CXX'],'\"clang++ -finstrument-functions -finstrument-functions-whitelist-inputfile=/tmp/instr_file\"')
    # self.assertEqual(p_kwargs['CLFLAGS'], '\" scorep.init.o ')
    # self.assertEqual(p_kwargs['CXXLFLAGS'], )
    self.assertEqual(p_kwargs['PIRANAME'], 'pira.built.exe')
    self.assertEqual(p_kwargs['NUMPROCS'], 8)
    self.assertEqual(p_kwargs['filter-file'], '/tmp/instr_file')

  def test_construct_pira_instr_kwargs(self):
    tc = C.TargetConfig(self.cfg.get_place('/tmp'), '/tmp', 'test_item', 'ct', 'asdf')
    builder = B.Builder(tc, False)
    self.assertIsNotNone(builder)

    with self.assertRaises(B.BuilderException) as cm_b:
      p_kwargs = builder.construct_pira_instr_kwargs()

    exc = cm_b.exception
    self.assertEqual(str(exc), 'Should not construct instrument kwargs in non-instrumentation mode.')

  @unittest.skip('This actually calls the functor.')
  def test_build_flavors(self):
    pass
