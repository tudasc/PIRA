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
from lib.Configuration import PiraConfiguration, TargetConfiguration, InstrumentConfig


class TestMeasurement(unittest.TestCase):

  def setUp(self):
    self.cfg_loader = cln.ConfigurationLoader()
    self.cfg = self.cfg_loader.load_conf('input/2_items_local_only.json')
    self.target_cfg = TargetConfiguration('/this/is/top_dir', 'item01', 'item01-flavor01', '')
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


if __name__ == '__main__':
  unittest.main()
