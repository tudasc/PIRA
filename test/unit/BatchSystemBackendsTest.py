"""
File: BatchSystemBackendsTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the BatchSystemBackends modules.
"""

import unittest
from lib.BatchSystemBackends import *


class BatchSystemInterfaceTests(unittest.TestCase):
  """
  Tests for the BatchSystemInterface class.
  """

  def setUp(self) -> None:
    """
    Setup
    """
    self.bi = BatchSystemInterface(
      backend_type=BatchSystemBackendType.SLURM,
      interface_type=SlurmInterfaces.PYSLURM,
      timings_type=BatchSystemTimingType.SUBPROCESS
    )
    self.key = U.generate_random_string()

  def test_get_interfaces(self):
    """
    Tests for get_interfaces.
    """
    self.assertEqual(self.bi.get_interfaces(), None)

  def test_set_interface(self):
    """
    Tests for set_interface.
    """
    self.assertEqual(self.bi.interface, SlurmInterfaces.PYSLURM)
    self.bi.set_interface(SlurmInterfaces.SBATCH_WAIT)
    self.assertEqual(self.bi.interface, SlurmInterfaces.SBATCH_WAIT)

  def test_configure(self):
    """
    Tests for configure().
    """
    batch_hardware_conf = BatchSystemHardwareConfig(3800, 1, 96)
    batch_gen = BatchSystemGenerator(batch_hardware_conf)
    self.bi.configure(batch_hardware_conf, batch_gen)
    self.assertEqual(self.bi.config, batch_hardware_conf)
    self.assertEqual(self.bi.generator, batch_gen)

  def test_add_preparation_command(self):
    """
    Tests for add_preparation_command
    """
    cmd = "test.exe"
    self.bi.add_preparation_command(self.key, cmd)
    self.assertTrue(self.key in self.bi.preparation_commands)
    self.assertEqual(self.bi.preparation_commands[self.key], cmd)

  def test_add_teardown_command(self):
    """
    Tests for add_teardown_command
    """
    cmd = "test2.exe"
    self.bi.add_teardown_command(self.key, cmd)
    self.assertTrue(self.key in self.bi.teardown_commands)
    self.assertEqual(self.bi.teardown_commands[self.key], cmd)
    
  def test_add_timed_command(self):
    """
    Test for add_timed_command
    """
    cmd = "test3.exe"
    self.bi.add_timed_command(self.key, cmd)
    self.assertTrue(self.key in self.bi.timed_commands)
    self.assertTrue((self.key, None) in self.bi.results)
    self.assertEqual(self.bi.timed_commands[self.key], cmd)
    self.assertEqual(self.bi.results[(self.key, None)], None)

  def test_get_results(self):
    """
    Test for get_results
    """
    # setup
    cmd = "test4.exe"
    self.bi.add_timed_command(self.key, cmd)
    # results asserts
    self.assertEqual(self.bi.results[(self.key, None)], None)
    self.bi.results[(self.key, None)] = 42
    self.assertEqual(self.bi.get_results(self.key, None), 42)

  def test_cleanup(self):
    """
    Test for cleanup()
    """
    cmd = "test5.exe"
    self.bi.add_preparation_command(self.key, cmd)
    self.bi.add_teardown_command(self.key, cmd)
    self.bi.add_timed_command(self.key, cmd)
    U.write_file(f"{U.get_default_pira_dir()}/pira-slurm-UNITTESTFILE.txt",
                 "Test - You can remove this without worrying.")
    self.bi.cleanup()
    self.assertEqual(self.bi.results, {})
    self.assertEqual(self.bi.preparation_commands, {})
    self.assertEqual(self.bi.teardown_commands, {})
    self.assertEqual(self.bi.timed_commands, {})
    self.assertFalse(U.is_file(f"{U.get_default_pira_dir()}/pira-slurm-UNITTESTFILE.txt"))


class SlurmBackendTest(unittest.TestCase):
  """
  Tests for the lib.SlurmBackend class
  """

  def setUp(self) -> None:
    """
    Setup
    """
    self.si = SlurmBackend(
      backend_type=BatchSystemBackendType.SLURM,
      interface_type=SlurmInterfaces.PYSLURM,
      timing_type=BatchSystemTimingType.SUBPROCESS
    )
    slurm_conf = SlurmConfig(job_array_start=1, job_array_end=3)  # use the defaults mostly
    slurm_gen = SlurmGenerator(slurm_conf)
    self.si.configure(slurm_conf, slurm_gen)
    self.key = U.generate_random_string()

  def test_get_interfaces(self):
    """
    Tests for get_interfaces.
    """
    self.assertEqual(self.si.get_interfaces(), SlurmInterfaces)

  def test_set_interface(self):
    """
    Tests for set_interface.
    """
    self.assertEqual(self.si.interface, SlurmInterfaces.PYSLURM)
    self.si.set_interface(SlurmInterfaces.SBATCH_WAIT)
    self.assertEqual(self.si.interface, SlurmInterfaces.SBATCH_WAIT)

  def test_configure(self):
    """
    Tests for configure().
    """
    slurm_conf = SlurmConfig(job_array_start=1, job_array_end=3)  # use the defaults mostly
    slurm_gen = SlurmGenerator(slurm_conf)
    self.si.configure(slurm_conf, slurm_gen)
    self.assertEqual(self.si.config, slurm_conf)
    self.assertEqual(self.si.generator, slurm_gen)

  def test_add_preparation_command(self):
    """
    Tests for add_preparation_command
    """
    cmd = "test.exe"
    self.si.add_preparation_command(self.key, cmd)
    self.assertTrue(self.key in self.si.preparation_commands)
    self.assertEqual(self.si.preparation_commands[self.key], cmd)

  def test_add_teardown_command(self):
    """
    Tests for add_teardown_command
    """
    cmd = "test2.exe"
    self.si.add_teardown_command(self.key, cmd)
    self.assertTrue(self.key in self.si.teardown_commands)
    self.assertEqual(self.si.teardown_commands[self.key], cmd)

  def test_add_timed_command(self):
    """
    Test for add_timed_command
    """
    cmd = "test3.exe"
    self.si.add_timed_command(self.key, cmd)
    self.assertTrue(self.key in self.si.timed_commands)
    self.assertTrue((self.key, 1) in self.si.results)
    self.assertTrue((self.key, 2) in self.si.results)
    self.assertTrue((self.key, 3) in self.si.results)
    self.assertEqual(self.si.timed_commands[self.key], cmd)
    self.assertEqual(self.si.results[(self.key, 1)], None)
    self.assertEqual(self.si.results[(self.key, 2)], None)
    self.assertEqual(self.si.results[(self.key, 3)], None)

  def test_get_results(self):
    """
    Test for get_results
    """
    # setup
    cmd = "test4.exe"
    self.si.add_timed_command(self.key, cmd)
    # results asserts
    self.assertEqual(self.si.results[(self.key, 1)], None)
    self.assertEqual(self.si.results[(self.key, 2)], None)
    self.assertEqual(self.si.results[(self.key, 3)], None)
    self.si.results[(self.key, 1)] = 42
    self.si.results[(self.key, 2)] = 43
    self.si.results[(self.key, 3)] = 44
    self.assertEqual(self.si.get_results(self.key, 1), 42)
    self.assertEqual(self.si.get_results(self.key, 2), 43)
    self.assertEqual(self.si.get_results(self.key, 3), 44)

  def test_cleanup(self):
    """
    Test for cleanup()
    """
    cmd = "test5.exe"
    self.si.add_preparation_command(self.key, cmd)
    self.si.add_teardown_command(self.key, cmd)
    self.si.add_timed_command(self.key, cmd)
    self.si.cleanup()
    self.assertEqual(self.si.results, {})
    self.assertEqual(self.si.preparation_commands, {})
    self.assertEqual(self.si.teardown_commands, {})
    self.assertEqual(self.si.timed_commands, {})

  def test_populate_result_dict_subprocess(self):
    """
    Tests for populate_result_dict with timing_type Subprocess.
    """
    self.si.timing_type = BatchSystemTimingType.SUBPROCESS
    # generate some test input
    self.si.add_timed_command(self.key, "test6.txt")
    jobid = str(int(time.time()))
    self.si.job_id_map[self.key] = jobid
    for i in range(1, 3+1, 1):
      with open(f"{U.get_default_pira_dir()}/pira-slurm-{jobid}-{self.key}-{i}.json", "w") as f:
        json.dump({
                    'cutime': 1234,
                    'cstime': 4321,
                    'elapsed': i,
                    'output': 'thisissomeoutput'
                  }, f, indent=4)
    # at begin the results should be not set
    self.assertEqual(self.si.results[(self.key, 1)], None)
    self.assertEqual(self.si.results[(self.key, 2)], None)
    self.assertEqual(self.si.results[(self.key, 3)], None)
    # files should be read into the result variable
    # each result is tuple of (elapsed time, output)
    self.si.populate_result_dict()
    self.assertEqual(self.si.results[(self.key, 1)], (float(1), "thisissomeoutput"))
    self.assertEqual(self.si.results[(self.key, 2)], (float(2), "thisissomeoutput"))
    self.assertEqual(self.si.results[(self.key, 3)], (float(3), "thisissomeoutput"))
    # and files should be deleted
    for i in range(1, 3+1, 1):
      U.remove_file(f"{U.get_default_pira_dir()}/pira-slurm-{jobid}-{self.key}-{i}.json")

  def test_populate_result_dict_os_time(self):
    """
    Test for populate_result_dict with timing_type os_time
    """
    self.si.timing_type = BatchSystemTimingType.OS_TIME
    # generate some test input
    self.si.add_timed_command(self.key, "test7.txt")
    jobid = str(int(time.time()))
    self.si.job_id_map[self.key] = jobid
    for i in range(1, 3+1, 1):
      with open(f"{U.get_default_pira_dir()}/pira-slurm-err.{jobid}_{i}", "w") as f:
        f.write("thisissomeoutput\n")
        # write the actual timing like from /usr/bin/time --format=%e
        f.write(f"{i}.0\n")
    # at begin the results should be not set
    self.assertEqual(self.si.results[(self.key, 1)], None)
    self.assertEqual(self.si.results[(self.key, 2)], None)
    self.assertEqual(self.si.results[(self.key, 3)], None)
    # it should grep the last line from the file as timing
    self.si.populate_result_dict()
    self.assertEqual(self.si.results[(self.key, 1)], (float(1), "thisissomeoutput\n"))
    self.assertEqual(self.si.results[(self.key, 2)], (float(2), "thisissomeoutput\n"))
    self.assertEqual(self.si.results[(self.key, 3)], (float(3), "thisissomeoutput\n"))
    for i in range(1, 3+1, 1):
      U.remove_file(f"{U.get_default_pira_dir()}//pira-slurm-err.{jobid}_{i}")





