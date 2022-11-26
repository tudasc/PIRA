"""
File: CheckerTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Tests for the Checker-module
"""

import unittest
import lib.Utility as U
import lib.Logging as L
import lib.Checker as C
import lib.ConfigurationLoader as CL
from lib.Configuration import PiraConfig, PiraConfigErrorException, PiraConfigII, PiraItem, PiraConfigAdapter, InvocationConfig


functor_files = [
  "/home/pira/build_dir/item1/functors/analyze_item1_ct.py",
  "/home/pira/build_dir/item1/functors/clean_item1_ct.py",
  "/home/pira/build_dir/item1/functors/no_instr_item1_ct.py",
  "/home/pira/build_dir/item1/functors/item1_ct.py",
  "/home/pira/build_dir/item1/functors/runner_item1_ct.py",

  "/home/pira/build_dir/item2/functors/analyze_item2.py",
  "/home/pira/build_dir/item2/functors/clean_item2.py",
  "/home/pira/build_dir/item2/functors/no_instr_item2.py",
  "/home/pira/build_dir/item2/functors/item2.py",
  "/home/pira/build_dir/item2/functors/runner_item2.py",
]

directories_to_create = [
  "/home/pira/build_dir/item1/analyzer",
  "/home/pira/build_dir/item1/functors",
  "/home/pira/build_dir/item2/analyzer",
  "/home/pira/build_dir/item2/functors"
]

tempdir = U.get_tempdir()

dep_aw_ins_anal = {
  'item1': [tempdir + '/home/pira/build_dir/item1/functors',
            tempdir + '/home/pira/build_dir/item1/cubes',
            tempdir + '/home/pira/build_dir/item1/analyzer'],
  'item2': [tempdir + '/home/pira/build_dir/item2/functors',
            tempdir + '/home/pira/build_dir/item2/cubes',
            tempdir + '/home/pira/build_dir/item2/analyzer']
}

build_dirs_v2 = {"item1": tempdir + "/home/pira/build_dir/item1",
                 "item2": tempdir + "/home/pira/build_dir/item2"}
items_v2 = ["item1","item2"]

class CheckerTestCase(unittest.TestCase):

  @classmethod
  def setUp(self):
    self.config_v1= PiraConfig()
    self.config_v1.set_build_directories([tempdir + '/home/pira/build_dir'])
    self.config_v1.populate_build_dict(self.config_v1.directories)
    self.config_v1.set_items(['item1', 'item2'], self.config_v1.directories[0])
    self.config_v1.initialize_item_dict(self.config_v1.directories[0], self.config_v1.builds[self.config_v1.directories[0]]['items'])

    for build_dir in self.config_v1.directories:
      for item in self.config_v1.builds[build_dir]['items']:
        self.config_v1.set_item_instrument_analysis(dep_aw_ins_anal[item], build_dir, item)
        self.config_v1.set_item_builders(tempdir + '/home/pira/build_dir/item1/functors', build_dir, item)
        self.config_v1.set_item_args([], build_dir, item)
        self.config_v1.set_item_runner("/" + item + "/runner/functors.dir", build_dir, item)

    self.config_v2 = PiraConfigII()

    pira_item1 = PiraItem("item1")
    pira_item1.set_analyzer_dir(tempdir + "/home/pira/build_dir/item1/analyzer")
    pira_item1.set_cubes_dir(tempdir + "/home/pira/build_dir/item1/cubes")
    pira_item1.set_flavors(["ct"])
    pira_item1.set_functors_base_path(tempdir + "/home/pira/build_dir/item1/functors")
    pira_item1.set_mode("CT")
    self.config_v2.add_item(tempdir + "/home/pira/build_dir/item1/",pira_item1)

    pira_item2 = PiraItem("item2")
    pira_item2.set_analyzer_dir(tempdir + "/home/pira/build_dir/item2/analyzer")
    pira_item2.set_cubes_dir(tempdir + "/home/pira/build_dir/item2/cubes")
    pira_item2.set_flavors([])
    pira_item2.set_functors_base_path(tempdir + "/home/pira/build_dir/item2/functors")
    pira_item2.set_mode("CT")
    self.config_v2.add_item(tempdir + "/home/pira/build_dir/item2/",pira_item2)

    self.config_adapter = PiraConfigAdapter(self.config_v2)
    self.create_tempfiles(self)

    InvocationConfig.create_from_kwargs({'config' : '../inputs/configs/basic_config_005.json'})



  def tearDown(self):
    self.delete_tempfolders()

  def create_tempfiles(self):
    for directory in directories_to_create:
      U.make_dirs(tempdir + directory)

    for filepath in functor_files:
      tempfile = open(tempdir + filepath,'a')
      tempfile.close()

  def delete_tempfolders(self):
    U.remove_dir(tempdir + "/home/pira/")

  def test_checker_v1_valid_config(self):
    InvocationConfig.create_from_kwargs({'config' : 'test/gol_config.json', 'config_version' : 1})
    C.Checker.check_configfile_v1(self.config_v1)

  def test_checker_v1_general_valid_config(self):
    InvocationConfig.create_from_kwargs({'config' : 'test/gol_config.json', 'config_version' : 1})
    C.Checker.check_configfile(self.config_v1)

  def test_checker_v1_dirs_missing(self):
    InvocationConfig.create_from_kwargs({'config' : 'test/gol_config.json', 'config_version' : 1})
    for directory in directories_to_create:
      U.remove_dir(tempdir + directory)
      with self.assertRaises(PiraConfigErrorException): C.Checker.check_configfile_v1(self.config_v1)
      self.create_tempfiles()

  def test_checker_v2_valid_config(self):
    C.Checker.check_configfile_v2(self.config_v2)

  def test_checker_v2_general_valid_config(self):
    C.Checker.check_configfile(self.config_v2)

  def test_checker_v2_adapter_valid_config(self):
    C.Checker.check_configfile_v2(self.config_adapter)

  def test_checker_v2_functors_missing(self):
    for file in functor_files:
      U.remove_file(tempdir + file)
      with self.assertRaises(PiraConfigErrorException): C.Checker.check_configfile_v2(self.config_v2)
      self.create_tempfiles()

  def test_checker_v2_dirs_missing(self):
    for directory in directories_to_create:
      U.remove_dir(tempdir + directory)
      with self.assertRaises(PiraConfigErrorException): C.Checker.check_configfile_v2(self.config_v2)
      self.create_tempfiles()

  def test_check_basic_config_005(self):
    cl = CL.SimplifiedConfigurationLoader()
    cfg = cl.load_conf()
    C.Checker.check_configfile_v2(cfg)


if __name__ == '__main__':
  L.get_logger().set_state('info', False)
  unittest.main()
