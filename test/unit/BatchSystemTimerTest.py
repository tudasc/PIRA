"""
File: BatchSystemTimerTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Tests for the batch system timer module.
"""
import json
import os
import subprocess
import unittest
import lib.Utility as U


class BatchSystemTimerTest(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.key = "ABCDEFG"
    self.job_id = "123456"
    self.job_array_id = "0"
    self.export_path = "."
    self.command = "sleep 2"
    # comparison options
    self.elapsed = 2
    self.output = ""

  def setUp(self) -> None:
    self.cmd = ["python3", f"{U.get_pira_code_dir()}/lib/BatchSystemTimer.py", self.key, self.job_id,
                self.job_array_id, self.export_path, self.command]

  def tearDown(self) -> None:
    os.remove(f"{self.export_path}/pira-slurm-{self.job_id}-{self.key}-{self.job_array_id}.json")

  def test_result_file(self):
    subprocess.run(self.cmd)
    try:
      with open(f"{self.export_path}/pira-slurm-{self.job_id}-{self.key}-{self.job_array_id}.json", "r") as f:
        content = json.load(f)
        print(content["output"])
        self.assertTrue(self.elapsed - 1 < content["elapsed"] < self.elapsed + 1)
        newline = "\n"
        self.assertEqual(content['output'], f"{self.output}{newline if self.output != '' else ''}")
    except FileNotFoundError:
      assert False


class BatchSystemTimerTest2(BatchSystemTimerTest):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.command = "sleep 10"
    # comparison options
    self.elapsed = 10
    self.output = ""


class BatchSystemTimerTest3(BatchSystemTimerTest):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.command = "sleep 2; echo 'Hello World!'"
    # comparison options
    self.elapsed = 2
    self.output = "Hello World!"


