"""
File: MeasurementTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Tests for the argument mapping
"""
import shutil
import os
import unittest
import lib.Measurement as M
import lib.ConfigurationLoader as C
import lib.DefaultFlags as D
from lib.Configuration import PiraConfig, TargetConfig, InstrumentConfig, InvocationConfig
import lib.Utility as U

class TestRunResult(unittest.TestCase):
  """
  Tests the RunResult class for its math
  """
  def test_empty_init(self):
    rr = M.RunResult()

    self.assertFalse(rr.is_multi_value())
    self.assertRaises(RuntimeError, rr.get_average)
    self.assertRaises(RuntimeError, rr.compute_overhead, M.RunResult())

  def test_single_value(self):
    rr = M.RunResult(4.0, 1)
    rr2 = M.RunResult(2.0, 1)

    self.assertFalse(rr.is_multi_value())
    self.assertEqual(rr.get_average(), 4.0)
    self.assertEqual(rr.compute_overhead(rr2), 2.0)

  def test_multi_values(self):
    rr = M.RunResult()
    rr2 = M.RunResult()

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
    # get runtime folder
    pira_dir = U.get_default_pira_dir()
    self.cubes_dir = os.path.join(pira_dir, 'test_cubes')
    # insert user runtime folder into test config
    data = None
    with open('input/unit_input_004.json', 'r') as file:
      data = file.read()
    data = data.replace('/tmp/where/cube/files/are', self.cubes_dir)
    with open('input/unit_input_004.json', 'w') as file:
      file.write(data)

    InvocationConfig.create_from_kwargs({'config' : 'input/unit_input_004.json'})
    self.cfg_loader = C.ConfigurationLoader()
    self.cfg = self.cfg_loader.load_conf()
    self.target_cfg = TargetConfig('/this/is/top_dir', '/this/is/top_dir', 'item01', 'item01-flavor01', '')
    self.instr_cfg = InstrumentConfig(True, 0)



  def tearDown(self):
    # reset test config
    data = None
    with open('input/unit_input_004.json', 'r') as file:
      data = file.read()
    data = data.replace(self.cubes_dir, '/tmp/where/cube/files/are')
    with open('input/unit_input_004.json', 'w') as file:
      file.write(data)
    shutil.rmtree(self.cubes_dir, ignore_errors=True)


  def test_scorep_mh_init(self):
    s_mh = M.ScorepSystemHelper(PiraConfig())
    self.assertIn('.cubex', s_mh.known_files)
    self.assertDictEqual(s_mh.data, {})
    self.assertEqual('False', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('', s_mh.cur_mem_size)
    self.assertEqual('', s_mh.cur_base_name)
    self.assertEqual('', s_mh.cur_filter_file)
    self.assertEqual('', s_mh.cur_exp_directory)

  def test_scorep_mh_set_up_instr(self):
    s_mh = M.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg)

    self.assertIn('cube_dir', s_mh.data)
    self.assertEqual('500M', s_mh.cur_mem_size)
    self.assertEqual('True', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('item01-flavor01-item01', s_mh.cur_base_name)
    self.assertEqual(self.cubes_dir + '/item01-item01-flavor01-0', s_mh.cur_exp_directory)

  def test_scorep_mh_set_up_no_instr(self):
    s_mh = M.ScorepSystemHelper(self.cfg)
    self.instr_cfg._is_instrumentation_run = False
    s_mh.set_up(self.target_cfg, self.instr_cfg)

    self.assertDictEqual({}, s_mh.data)
    self.assertEqual('', s_mh.cur_mem_size)
    self.assertEqual('False', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('', s_mh.cur_base_name)
    self.assertEqual('', s_mh.cur_exp_directory)

  def test_scorep_mh_dir_invalid(self):
    s_mh = M.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg)

    self.assertEqual(self.cubes_dir + '/item01-item01-flavor01-0', s_mh.cur_exp_directory)
    self.assertRaises(M.MeasurementSystemException, s_mh.set_exp_dir, '+/invalid/path/haha', 'item01-flavor01', 0)
    self.assertRaises(M.MeasurementSystemException, s_mh.set_exp_dir, '/inv?alid/path/haha', 'item01-flavor01', 0)

  def test_get_instr_file_flags(self):
    s_mh = M.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg)
    instr_file = 'myFile.filt'
    ct_filter = True

    cc = M.ScorepSystemHelper.get_scorep_compliant_CC_command(instr_file)
    self.assertEqual('\"clang -finstrument-functions -finstrument-functions-whitelist-inputfile='+instr_file+'\"', cc)
    cpp = M.ScorepSystemHelper.get_scorep_compliant_CXX_command(instr_file)
    self.assertEqual('\"clang++ -finstrument-functions -finstrument-functions-whitelist-inputfile='+instr_file+'\"', cpp)

  def test_get_no_instr_file_flags(self):
    s_mh = M.ScorepSystemHelper(self.cfg)
    s_mh.set_up(self.target_cfg, self.instr_cfg)
    instr_file = 'myFile.filt'
    ct_filter = False

    kw_dict = D.BackendDefaults().get_default_kwargs()
    cc = kw_dict['CC']
    self.assertEqual('\"clang\"', cc)
    cpp = kw_dict['CXX']
    self.assertEqual('\"clang++\"', cpp)


if __name__ == '__main__':
  unittest.main()
