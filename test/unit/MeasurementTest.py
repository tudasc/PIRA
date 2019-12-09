"""
File: MeasurementTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the argument mapping
"""

import sys
sys.path.append('..')

import unittest
import typing

import lib.Measurement as m
import lib.ConfigurationLoader as cln
import lib.DefaultFlags as dff
from lib.Configuration import PiraConfiguration, TargetConfiguration, InstrumentConfig


class TestRunResult(unittest.TestCase):
  """
  Tests the RunResult class for its math
  """
  def test_empty_init(self):
    rr = m.RunResult()

    self.assertFalse(rr.is_multi_value())
    self.assertRaises(RuntimeError, rr.get_average)
    self.assertRaises(RuntimeError, rr.compute_overhead, m.RunResult())

  def test_single_value(self):
    rr = m.RunResult(4.0, 1)
    rr2 = m.RunResult(2.0, 1)

    self.assertFalse(rr.is_multi_value())
    self.assertEqual(rr.get_average(), 4.0)
    self.assertEqual(rr.compute_overhead(rr2), 2.0)

  def test_multi_values(self):
    rr = m.RunResult()
    rr2 = m.RunResult()

    for v in range(1,4):
      rr.add_values(float(v), 1)
      rr2.add_values(float(2*v), 1)

    self.assertTrue(rr.is_multi_value())
    # Simple averages
    self.assertEqual(rr.get_average(0), 1)
    self.assertEqual(rr.get_average(1), 2)
    self.assertEqual(rr.get_average(2), 3)

    # Overheads
    self.assertEqual(rr.compute_overhead(rr2, 0), 0.5)
    self.assertEqual(rr.compute_overhead(rr2, 1), 0.5)
    self.assertEqual(rr.compute_overhead(rr2, 2), 0.5)

class TestScorepHelper(unittest.TestCase):
  """
  Tests the ScorepSystemHelper class and, currently, also the DefaultFlags.
  TODO Separate the building portion of Score-P and the measurement system part.
  """
  def setUp(self):
    self.cfg_loader = cln.ConfigurationLoader()
    self.cfg = self.cfg_loader.load_conf('input/unit_input_004.json')
    self.target_cfg = TargetConfiguration('/this/is/top_dir', '/this/is/top_dir', 'item01', 'item01-flavor01', '')
    self.instr_cfg = InstrumentConfig(True, 0)

  def test_scorep_mh_init(self):
    s_mh = m.ScorepSystemHelper(PiraConfiguration())
    self.assertIn('.cubex', s_mh.known_files)
    self.assertDictEqual(s_mh.data, {})
    self.assertEqual('False', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('', s_mh.cur_mem_size)
    self.assertEqual('', s_mh.cur_base_name)
    self.assertEqual('', s_mh.cur_filter_file)
    self.assertEqual('', s_mh.cur_exp_directory)

  def test_scorep_mh_set_up_instr(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg, True)

    self.assertIn('cube_dir', s_mh.data)
    self.assertEqual('500M', s_mh.cur_mem_size)
    self.assertEqual('True', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('item01-flavor01-item01', s_mh.cur_base_name)
    self.assertEqual('/tmp/where/cube/files/are/item01-item01-flavor01-0', s_mh.cur_exp_directory)

  def test_scorep_mh_set_up_no_instr(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    self.instr_cfg._is_instrumentation_run = False
    s_mh.set_up(self.target_cfg, self.instr_cfg, True)

    self.assertDictEqual({}, s_mh.data)
    self.assertEqual('', s_mh.cur_mem_size)
    self.assertEqual('False', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('', s_mh.cur_base_name)
    self.assertEqual('', s_mh.cur_exp_directory)

  def test_scorep_mh_dir_invalid(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg, True)

    self.assertEqual('/tmp/where/cube/files/are/item01-item01-flavor01-0', s_mh.cur_exp_directory)
    self.assertRaises(m.MeasurementSystemException, s_mh.set_exp_dir, '+/invalid/path/haha', 'item01-flavor01', 0)
    self.assertRaises(m.MeasurementSystemException, s_mh.set_exp_dir, '/inv?alid/path/haha', 'item01-flavor01', 0)

  def test_get_instr_file_flags(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg, True)
    instr_file = 'myFile.filt'
    ct_filter = True

    cc = m.ScorepSystemHelper.get_scorep_compliant_CC_command(instr_file, ct_filter)
    self.assertEqual('\"clang -finstrument-functions -finstrument-functions-whitelist-inputfile='+instr_file+'\"', cc)
    cpp = m.ScorepSystemHelper.get_scorep_compliant_CXX_command(instr_file, ct_filter)
    self.assertEqual('\"clang++ -finstrument-functions -finstrument-functions-whitelist-inputfile='+instr_file+'\"', cpp)

  def test_get_no_instr_file_flags(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg, False)
    instr_file = 'myFile.filt'
    ct_filter = False

    kw_dict = dff.BackendDefaults().get_default_kwargs()
    cc = kw_dict['CC']
    self.assertEqual('\"clang\"', cc)
    cpp = kw_dict['CXX']
    self.assertEqual('\"clang++\"', cpp)


if __name__ == '__main__':
  unittest.main()
