import sys
sys.path.append('..')

import unittest
import typing

import lib.Measurement as m
import lib.ConfigLoaderNew as cln


class TestMeasurement(unittest.TestCase):

  def setUp(self):
    self.cfg_loader = cln.ConfigurationLoader()
    self.cfg = self.cfg_loader.load_conf('input/2_items_local_only.json')


  def test_init_run_cfg(self):
    r_cfg = m.RunConfiguration(0, False, 'asdf')
    self.assertEqual(r_cfg.get_iteration(), 0)
    self.assertEqual(r_cfg.is_instr(), False)
    self.assertEqual(r_cfg.get_db_item_id(), 'asdf')


  def test_scorep_mh_init(self):
    s_mh = m.ScorepSystemHelper(cln.ConfigurationNew())
    self.assertIn('.cubex', s_mh.known_files)
    self.assertDictEqual(s_mh.data, {})
    self.assertEqual('False', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('', s_mh.cur_mem_size)
    self.assertEqual('', s_mh.cur_base_name)
    self.assertEqual('', s_mh.cur_filter_file)
    self.assertEqual('', s_mh.cur_exp_directory)


  def test_scorep_mh_set_up_instr(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    s_mh.set_up('/this/is/top_dir', 'item01', 'item01-flavor01', 0, True)

    self.assertIn('cube_dir', s_mh.data)
    self.assertEqual('500M', s_mh.cur_mem_size)
    self.assertEqual('True', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('item01-flavor01-item01', s_mh.cur_base_name)
    self.assertEqual('/tmp/where/cube/files/are/item01-item01-flavor01-0', s_mh.cur_exp_directory)


  def test_scorep_mh_set_up_instr(self):
    s_mh = m.ScorepSystemHelper(self.cfg)
    s_mh.set_up('/this/is/top_dir', 'item01', 'item01-flavor01', 0, False)

    self.assertDictEqual({}, s_mh.data)
    self.assertEqual('', s_mh.cur_mem_size)
    self.assertEqual('False', s_mh.cur_overwrite_exp_dir)
    self.assertEqual('', s_mh.cur_base_name)
    self.assertEqual('', s_mh.cur_exp_directory)
   

if __name__ == '__main__':
  unittest.main()
