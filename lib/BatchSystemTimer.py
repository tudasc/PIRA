"""
File: BatchSystemTimer.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Wrapper for timings in PIRA Slurm jobs, utilizes subprocess and os.times(). This way it is the
same as in PIRA, with in the U.shell call.
"""


import json
import os
import subprocess
import sys


class BatchSystemTimer:
  """
  A timer class for batch systems.
  This is not meant to be used in pira itself.
  It is a class that is used in the job script,
  as a python wrapper to obtain the timing results
  like it is done in PIRA local, with os.times().
  The times will be written to a json file, which will
  be read by PIRA later.
  For this to work, you have to give four arguments to this script:
  - key: The timings key from within PIRA.
  - job_id: The job id of the slurm job.
  - job_array_id: The index of the Slurm array job.
  - export_path: The path where the json results should go.
  - command: The command to run/to time.
  """
  def __init__(self, key: str, job_id: str, job_array_id: int, export_path: str, command: str):
    """
    Constructor.
    """
    self.key = key
    self.job_id = job_id
    self.job_array_id = job_array_id
    self.export_path = export_path
    self.command = command
    self.results = {}

  def run(self):
    """
    Run and time the command.
    Start the exporting.
    """
    t1 = os.times()  # start time
    out = subprocess.check_output(command, shell=True)
    t2 = os.times()  # end time
    cutime = t2[2] - t1[2]
    cstime = t2[3] - t1[3]
    elapsed = t2[4] - t1[4]
    runtime = elapsed
    out = str(out.decode('utf-8'))
    res = {
      "cutime": cutime,
      "cstime": cstime,
      "elapsed": runtime,
      "output": str(out)
    }
    self.export_results(res)

  def export_results(self, res):
    """
    Export results to the json file.
    """
    filename = f"{self.export_path}/pira-slurm-{self.job_id}-{self.key}-{self.job_array_id}.json"
    with open(filename, "w") as f:
      json.dump(res, f, indent=4)


if __name__ == "__main__":
  args = sys.argv[1:]
  key = args[0]
  job_id = args[1]
  job_array_id = int(args[2])
  export_path = args[3]
  command = args[4]
  BatchSystemTimer(key, job_id, job_array_id, export_path, command).run()
