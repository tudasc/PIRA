"""
File: BatchSystemGeneratorTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Tests for the batch system generator module.
"""

import unittest

from lib.BatchSystemGenerator import *
from lib.BatchSystemGenerator import _Module


class ModuleTests(unittest.TestCase):
  """
  Testcases for the Module class of slurm configuration module.
  """

  def setUp(self) -> None:
    self.m1 = _Module(name="gcc", version="10.2")
    self.m2 = _Module(name="make", version="10.2")
    self.m3 = _Module(name="cmake", version="10.2")
    self.m4 = _Module(name="llvm", version="10.2")
    self.m5 = _Module(name="cuda", version="10.2", depends_on=["gcc/10.2"])
    self.m6 = _Module(name="openmpi", version="10.2")
    self.slurm_config = SlurmConfig(uses_module_system=True)
    self.gen = SlurmGenerator(self.slurm_config)

  def tearDown(self) -> None:
    del self.m1
    del self.m2
    del self.m3
    del self.m4
    del self.m5
    del self.m6
    del self.slurm_config
    del self.gen

  def test_module_dependency1(self):
    self.gen.add_module("gcc", depends_on=["cuda"])
    with self.assertRaises(RuntimeError):
      with self.assertRaises(ModuleDependencyConflict):
        # should assert because there is a circular dependency (cuda <-> gcc)
        self.gen.add_module("cuda", depends_on=["gcc"])

  def test_module_dependency2(self):
    self.gen.add_module("gcc", version="10.2", depends_on=["cuda/11.2"])
    with self.assertRaises(RuntimeError):
      with self.assertRaises(ModuleDependencyConflict):
        # should assert because there is a circular dependency (cuda <-> gcc <-> cmake)
        self.gen.add_module("cuda", version="11.2", depends_on=["gcc/10.2"])

  def test_module_order1(self):
    self.gen.add_module("cuda", depends_on=["gcc"])
    self.gen.add_module("gcc")
    res = self.gen.sbatch(active=False, load_modules=True)
    self.assertIn("module load gcc; module load cuda", res)

  def test_module_order2(self):
    self.gen.add_module("cuda", version="10.2", depends_on=["gcc/11.2"])
    self.gen.add_module("gcc", version="11.2")
    res = self.gen.sbatch(active=False, load_modules=True)
    self.assertIn("module load gcc/11.2; module load cuda/10.2", res)

  def test_module_order3(self):
    # this unlike the dependency can check for circular imports of more than two modules.
    # It tries to sort the modules in a way that they do not conflict each other, if this cannot be done,
    # it is likely that there is a circular import
    self.gen.add_module("cuda", depends_on=["gcc"])
    self.gen.add_module("gcc", depends_on=["cmake"])
    self.gen.add_module("cmake", depends_on=["cuda"])
    with self.assertRaises(ModuleDependencyConflict):
      self.gen.sbatch(active=False, load_modules=True)


class BatchSystemGeneratorTests(unittest.TestCase):
  """
  Testcases for the slurm configuration class of the slurm configuration module.
  """

  def __init__(
          self,
          *args,
          **kwargs
  ):
    self.test_file = "test.sh"
    self.slurm_script_file = "exampleslurmscript.sh"
    self.job_name = "examplejobname"
    self.std_out_path = "./examplejoboutput/out"
    self.std_err_path = "./examplejoboutput/err"
    self.time_str = "00:10:00"
    self.in_minutes = 10
    self.mem_per_cpu = 3800
    self.number_of_tasks = 1
    self.number_of_cores_per_task = 1
    self.cpu_frequency_str = "High-High"
    self.partition = "pira"
    self.reservation = "pira"
    self.account = "pira"
    self.job_array_start = 1
    self.job_array_end = 5
    self.job_array_step = 1
    self.exclusive = True
    self.wait = False
    self.dependencies = None
    self.mail_types = [MailType.FAIL, MailType.BEGIN]
    self.mail_address = "test@test.com"
    self.uses_module_system = True
    self.shell = "/bin/bash"
    self.purge_modules_at_start = True
    self.force_sequential = False

    # should be a dict of {"name": name, "version": "10.0", "dependencies": "name[/version]"}
    # (version, dependencies are optional)
    self.modules = []
    # list of strings
    self.commands = []
    # expected module sorting order
    self.expected_module_order = []
    # whether it is expected this raises a "ModuleDependencyConflict: Modules could not be sorted in a way
    # they do not conflict each other"
    self.expected_module_error = False

    super().__init__(*args, **kwargs)

  def setUp(self) -> None:
    self.slurm_config = SlurmConfig(
      slurm_script_file=self.slurm_script_file,
      job_name=self.job_name,
      std_out_path=self.std_out_path,
      std_err_path=self.std_err_path,
      time_str=self.time_str,
      mem_per_cpu=self.mem_per_cpu,
      number_of_tasks=self.number_of_tasks,
      number_of_cores_per_task=self.number_of_cores_per_task,
      cpu_frequency_str=self.cpu_frequency_str,
      partition=self.partition,
      reservation=self.reservation,
      account=self.account,
      job_array_start=self.job_array_start,
      job_array_end=self.job_array_end,
      job_array_step=self.job_array_step,
      exclusive=self.exclusive,
      wait=self.wait,
      dependencies=self.dependencies,
      mail_types=self.mail_types,
      mail_address=self.mail_address,
      uses_module_system=self.uses_module_system,
      shell=self.shell,
      purge_modules_at_start=self.purge_modules_at_start,
      modules=self.modules,
      force_sequential=self.force_sequential
    )
    self.gen = SlurmGenerator(self.slurm_config)

    # adding modules
    for m in self.modules:
      version = None
      if "version" in m:
        version = m["version"]
      dependencies = None
      if "depends_on" in m:
        dependencies = []
        for d in m["depends_on"]:
          dep = d["name"]
          if "version" in d:
            dep = dep + "/" + d["version"]
          dependencies.append(dep)
      self.gen.add_module(m["name"], version, dependencies)
    # adding commands
    for c in self.commands:
      self.gen.add_command(c)

  def tearDown(self) -> None:
    del self.slurm_config
    del self.gen
    # remove test script again
    U.remove_file("test.sh")

  def test_write_slurm_script(self):
    # test target - produces file
    self.gen.write_slurm_script(self.test_file, load_modules=True)
    # asserts
    with open(self.test_file, "r") as f:
      content = f.readlines()
      self.assertIn(f"#SBATCH --job-name={self.job_name}\n", content)
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"#SBATCH --output={self.std_out_path}.%A_%a\n", content)
        self.assertIn(f"#SBATCH --error={self.std_err_path}.%A_%a\n", content)
      else:
        self.assertIn(f"#SBATCH --output={self.std_out_path}.%j\n", content)
        self.assertIn(f"#SBATCH --error={self.std_err_path}.%j\n", content)
      self.assertIn(f"#SBATCH --time={self.time_str}\n", content)
      self.assertIn(f"#SBATCH --mem-per-cpu={self.mem_per_cpu}\n", content)
      self.assertIn(f"#SBATCH --ntasks={self.number_of_tasks}\n", content)
      self.assertIn(f"#SBATCH --cpus-per-task={self.number_of_cores_per_task}\n", content)
      self.assertIn(f"#SBATCH --cpu-freq={self.cpu_frequency_str}\n", content)
      self.assertIn(f"#SBATCH --partition={self.partition}\n", content)
      self.assertIn(f"#SBATCH --reservation={self.reservation}\n", content)
      self.assertIn(f"#SBATCH --account={self.account}\n", content)
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"#SBATCH --array={self.job_array_start}-{self.job_array_end}:{self.job_array_step}"
                      f"{'%1' if self.force_sequential else ''}\n", content)
      if self.exclusive:
        self.assertIn(f"#SBATCH --exclusive\n", content)
      else:
        self.assertNotIn(f"#SBATCH --exclusive\n", content)
      if not self.dependencies:
        self.assertNotIn(f"#SBATCH --dependency={self.dependencies}\n", content)
      else:
        self.assertIn(f"#SBATCH --dependency={self.dependencies}\n", content)
      mts = ",".join(self.mail_types)
      self.assertIn(f"#SBATCH --mail-type={mts}\n", content)
      self.assertIn(f"#SBATCH --mail-user={self.mail_address}\n", content)
      self.assertIn(f"#!{self.shell}\n", content)
      if self.uses_module_system and self.purge_modules_at_start:
        self.assertIn(f"module purge\n", content)
      # modules
      for m in self.modules:
        mod = m["name"]
        if "version" in m:
          mod = mod + "/" + m["version"]
        self.assertIn(f"module load {mod}\n", content)
      # commands
      for c in self.commands:
        self.assertIn(f"{c}\n", content)

  def test_sbatch_passive_no_script(self):
    # test target
    result = self.gen.sbatch(active=False, load_modules=True)
    # asserts
    self.assertIn("sbatch", result)
    self.assertIn(f"--job-name={self.job_name}", result)
    if self.job_array_start is not None and self.job_array_end is not None:
      self.assertIn(f"--output={self.std_out_path}.%A_%a", result)
      self.assertIn(f"--error={self.std_err_path}.%A_%a", result)
    else:
      self.assertIn(f"--output={self.std_out_path}.%j", result)
      self.assertIn(f"--error={self.std_err_path}.%j", result)
    self.assertIn(f"--time={self.time_str}", result)
    self.assertIn(f"--mem-per-cpu={self.mem_per_cpu}", result)
    self.assertIn(f"--ntasks={self.number_of_tasks}", result)
    self.assertIn(f"--cpus-per-task={self.number_of_cores_per_task}", result)
    self.assertIn(f"--cpu-freq={self.cpu_frequency_str}", result)
    self.assertIn(f"--partition={self.partition}", result)
    self.assertIn(f"--reservation={self.reservation}", result)
    self.assertIn(f"--account={self.account}", result)
    if self.job_array_start is not None and self.job_array_end is not None:
      self.assertIn(f"--array={self.job_array_start}-{self.job_array_end}:{self.job_array_step}"
                    f"{'%1' if self.force_sequential else ''}",
                    result)
    if self.exclusive:
      self.assertIn(f"--exclusive", result)
    else:
      self.assertNotIn(f"--exclusive", result)
    if not self.dependencies:
      self.assertNotIn(f"--dependency={self.dependencies}", result)
    else:
      self.assertIn(f"--dependency={self.dependencies}", result)
    mts = ",".join(self.mail_types)
    self.assertIn(f"--mail-type={mts}", result)
    self.assertIn(f"--mail-user={self.mail_address}", result)
    if self.uses_module_system and self.purge_modules_at_start:
      self.assertIn(f"module purge", result)
    # modules
    for m in self.modules:
      mod = m["name"]
      if "version" in m:
        mod = mod + "/" + m["version"]
      self.assertIn(f"module load {mod};", result)
    # commands
    for c in self.commands:
      if c == self.commands[-1]:
        # for last command: without semicolon
        self.assertIn(f"{c}", result)
      else:
        self.assertIn(f"{c};", result)

  def test_sbatch_passive_script(self):
    # test target
    result = self.gen.sbatch(script_path=self.test_file, active=False, load_modules=True)
    # asserts
    self.assertEqual(f"sbatch {self.test_file}", result)
    with open(self.test_file, "r") as f:
      content = f.readlines()
      self.assertIn(f"#SBATCH --job-name={self.job_name}\n", content)
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"#SBATCH --output={self.std_out_path}.%A_%a\n", content)
        self.assertIn(f"#SBATCH --error={self.std_err_path}.%A_%a\n", content)
      else:
        self.assertIn(f"#SBATCH --output={self.std_out_path}.%j\n", content)
        self.assertIn(f"#SBATCH --error={self.std_err_path}.%j\n", content)
      self.assertIn(f"#SBATCH --time={self.time_str}\n", content)
      self.assertIn(f"#SBATCH --mem-per-cpu={self.mem_per_cpu}\n", content)
      self.assertIn(f"#SBATCH --ntasks={self.number_of_tasks}\n", content)
      self.assertIn(f"#SBATCH --cpus-per-task={self.number_of_cores_per_task}\n", content)
      self.assertIn(f"#SBATCH --cpu-freq={self.cpu_frequency_str}\n", content)
      self.assertIn(f"#SBATCH --partition={self.partition}\n", content)
      self.assertIn(f"#SBATCH --reservation={self.reservation}\n", content)
      self.assertIn(f"#SBATCH --account={self.account}\n", content)
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"#SBATCH --array={self.job_array_start}-{self.job_array_end}:{self.job_array_step}"
                      f"{'%1' if self.force_sequential else ''}\n", content)
      if self.exclusive:
        self.assertIn(f"#SBATCH --exclusive\n", content)
      else:
        self.assertNotIn(f"#SBATCH --exclusive\n", content)
      if not self.dependencies:
        self.assertNotIn(f"#SBATCH --dependency={self.dependencies}\n", content)
      else:
        self.assertIn(f"#SBATCH --dependency={self.dependencies}\n", content)
      mts = ",".join(self.mail_types)
      self.assertIn(f"#SBATCH --mail-type={mts}\n", content)
      self.assertIn(f"#SBATCH --mail-user={self.mail_address}\n", content)
      self.assertIn(f"#!{self.shell}\n", content)
      if self.uses_module_system and self.purge_modules_at_start:
        self.assertIn(f"module purge\n", content)
      # modules
      for m in self.modules:
        mod = m["name"]
        if "version" in m:
          mod = mod + "/" + m["version"]
        self.assertIn(f"module load {mod}\n", content)
      # commands
      for c in self.commands:
        self.assertIn(f"{c}\n", content)
    os.remove(self.test_file)

  def test_module_order_slurm_script(self):
    # target
    self.gen.write_slurm_script(self.test_file, load_modules=True)
    # asserts
    with open(self.test_file, "r") as f:
      module_lines = [line for line in f.readlines() if "module" in line]
      if self.uses_module_system:
        if self.purge_modules_at_start:
          self.assertEqual("module purge\n", module_lines[0])
          module_lines = module_lines[1:]
        for i in range(len(module_lines)):
          self.assertEqual(f"module load {self.expected_module_order[i]}\n", module_lines[i])
      else:
        self.assertEqual(module_lines, [])

  def test_module_order_sbatch_passive_script(self):
    if self.expected_module_error:
      with self.assertRaises(ModuleDependencyConflict):
        self.gen.sbatch(script_path=self.test_file, active=False, load_modules=True)
    else:
      result = self.gen.sbatch(script_path=self.test_file, active=False, load_modules=True)
      # assert
      self.assertEqual(f"sbatch {self.test_file}", result)
      with open(self.test_file, "r") as f:
        module_lines = [line for line in f.readlines() if "module" in line]
        if self.uses_module_system:
          if self.purge_modules_at_start:
            self.assertEqual("module purge\n", module_lines[0])
            module_lines = module_lines[1:]
          for i in range(len(module_lines)):
            self.assertEqual(f"module load {self.expected_module_order[i]}\n", module_lines[i])
        else:
          self.assertEqual(module_lines, [])

  def test_module_order_sbatch_passive_no_script(self):
    if self.expected_module_error:
      with self.assertRaises(ModuleDependencyConflict):
        self.gen.sbatch(active=False, load_modules=True)
    else:
      result = self.gen.sbatch(active=False, load_modules=True)
      # asserts
      self.assertIn("sbatch", result)
      module_lines = [m.strip() for m in result.split(";") if "module" in m]
      if self.uses_module_system:
        module_lines[0] = "module" + module_lines[0].split("module")[1].rstrip()
        if self.purge_modules_at_start:
          self.assertEqual("module purge", module_lines[0])
          module_lines = module_lines[1:]
        for i in range(len(module_lines)):
          self.assertEqual(f"module load {self.expected_module_order[i]}", module_lines[i])
      else:
        self.assertEqual(module_lines, [])

  def test_add_modules(self):
    """
    set_up uses add_module. Tests "add_modules" wrapper here.
    """
    self.gen.clear_modules()
    self.gen.add_modules()
    for mod_is, mod_exp in zip(self.gen.modules, self.modules):
      self.assertEqual(mod_is.name, mod_exp["name"])
      if "version" in mod_exp:
        self.assertEqual(mod_is.version, mod_exp["version"])
      if "depends_on" in mod_exp:
        for dep_is, dep_exp in zip(mod_is.depends_on, mod_exp["depends_on"]):
          if "version" in dep_exp:
            self.assertEqual(dep_is, f"{dep_exp['name']}/{dep_exp['version']}")
          else:
            self.assertEqual(dep_is, dep_exp['name'])

  def test_clear_modules(self):
    self.gen.clear_modules()
    self.assertListEqual(self.gen.modules, [])

  def test_clear_commands(self):
    self.gen.clear_commands()
    self.assertListEqual(self.gen.commands, [])

  def test_to_slurm_args(self):
    self.gen.to_slurm_options()
    if self.account:
      self.assertEqual(self.account, self.gen.slurm_options["--account"])
    if self.reservation:
      self.assertEqual(self.reservation, self.gen.slurm_options["--reservation"])
    if self.partition:
      self.assertEqual(self.partition, self.gen.slurm_options["--partition"])
    if self.job_name:
      self.assertEqual(self.job_name, self.gen.slurm_options["--job-name"])
    if self.std_out_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertEqual(self.gen.slurm_options["--output"], f"{self.std_out_path}.%A_%a")
      else:
        self.assertEqual(self.gen.slurm_options["--output"], f"{self.std_out_path}.%j")
    if self.std_err_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertEqual(self.gen.slurm_options["--error"], f"{self.std_err_path}.%A_%a")
      else:
        self.assertEqual(self.gen.slurm_options["--error"], f"{self.std_err_path}.%j")
    if self.time_str:
      self.assertEqual(self.gen.slurm_options["--time"], self.time_str)
    if self.mem_per_cpu:
      self.assertEqual(self.gen.slurm_options["--mem-per-cpu"], self.mem_per_cpu)
    if self.number_of_tasks:
      self.assertEqual(self.gen.slurm_options["--ntasks"], self.number_of_tasks)
    if self.number_of_cores_per_task:
      self.assertEqual(self.gen.slurm_options["--cpus-per-task"], self.number_of_cores_per_task)
    if self.exclusive:
      self.assertEqual(self.gen.slurm_options["--exclusive"], None)
    if self.wait:
      self.assertEqual(self.gen.slurm_options["--wait"], None)
    if self.job_array_start is not None and self.job_array_end is not None:
      self.assertEqual(self.gen.slurm_options["--array"], f"{self.job_array_start}-{self.job_array_end}:"
                                                          f"{self.job_array_step}"
                                                          f"{'%1' if self.force_sequential else ''}")
    if self.cpu_frequency_str:
      self.assertEqual(self.gen.slurm_options["--cpu-freq"], self.cpu_frequency_str)
    if self.dependencies:
      self.assertEqual(self.gen.slurm_options["--dependency"], self.dependencies)
    if self.mail_address:
      self.assertEqual(self.gen.slurm_options["--mail-user"], self.mail_address)
    if self.mail_types:
      self.assertEqual(self.gen.slurm_options["--mail-type"], ",".join(self.mail_types))

  def test_to_arg_strings(self):
    res = self.gen.to_arg_strings()
    if self.account:
      self.assertIn(f"--account={self.account}", res)
    if self.reservation:
      self.assertIn(f"--reservation={self.reservation}", res)
    if self.partition:
      self.assertIn(f"--partition={self.partition}", res)
    if self.job_name:
      self.assertIn(f"--job-name={self.job_name}", res)
    if self.std_out_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"--output={self.std_out_path}.%A_%a", res)
      else:
        self.assertIn(f"--output={self.std_out_path}.%j", res)
    if self.std_err_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"--error={self.std_err_path}.%A_%a", res)
      else:
        self.assertIn(f"--error={self.std_err_path}.%j", res)
    if self.time_str:
      self.assertIn(f"--time={self.time_str}", res)
    if self.mem_per_cpu:
      self.assertIn(f"--mem-per-cpu={self.mem_per_cpu}", res)
    if self.number_of_tasks:
      self.assertIn(f"--ntasks={self.number_of_tasks}", res)
    if self.number_of_cores_per_task:
      self.assertIn(f"--cpus-per-task={self.number_of_cores_per_task}", res)
    if self.exclusive:
      self.assertIn(f"--exclusive", res)
    if self.wait:
      self.assertIn(f"--wait", res)
    if self.job_array_start is not None and self.job_array_end is not None:
      self.assertIn(f"--array={self.job_array_start}-{self.job_array_end}:{self.job_array_step}"
                    f"{'%1' if self.force_sequential else ''}", res)
    if self.cpu_frequency_str:
      self.assertIn(f"--cpu-freq={self.cpu_frequency_str}", res)
    if self.dependencies:
      self.assertIn(f"--dependency={self.dependencies}", res)
    if self.mail_address:
      self.assertIn(f"--mail-user={self.mail_address}", res)
    if self.mail_types:
      self.assertIn(f"--mail-type={','.join(self.mail_types)}", res)

  def test_get_pyslurm_args(self):
    """
    Test for get_pyslurm_args.
    """
    res = self.gen.get_pyslurm_args()
    if self.account:
      # "|" is the union operator: So we add account to res
      # which will change nothing if it is already there.
      # So this test will pass, if the account is in res,
      # fail otherwise (cause it will add account and res will
      # be more then the res dict and not equal)
      self.assertEqual(res, res | {"account": self.account})
    if self.reservation:
      self.assertEqual(res, res | {"reservation": self.reservation})
    if self.partition:
      self.assertEqual(res, res | {"partition": self.partition})
    if self.job_name:
      self.assertEqual(res, res | {"job_name": self.job_name})
    if self.std_out_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertEqual(res, res | {"output": f"{self.std_out_path}.%A_%a"})
      else:
        self.assertEqual(res, res | {"output": f"{self.std_out_path}.%j"})
    if self.std_err_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertEqual(res, res | {"error": f"{self.std_err_path}.%A_%a"})
      else:
        self.assertEqual(res, res | {"error": f"{self.std_err_path}.%j"})
    if self.time_str:
      # first real pyslurm difference: time -> time limit
      self.assertEqual(res, res | {"time_limit": self.in_minutes})
    if self.mem_per_cpu:
      self.assertEqual(res, res | {"mem_per_cpu": self.mem_per_cpu})
    if self.number_of_tasks:
      self.assertEqual(res, res | {"ntasks": self.number_of_tasks})
    if self.number_of_cores_per_task:
      self.assertEqual(res, res | {"cpus_per_task": self.number_of_cores_per_task})
    if self.exclusive:
      # exclusive should not be in it
      self.assertNotEqual(res, res | {"exclusive": None})
    if self.wait:
      # wait should not be in pyslurm args
      self.assertNotEqual(res, res | {"wait": True})
    if self.job_array_start is not None and self.job_array_end is not None:
      # second difference: array -> array_inx
      inx = []
      for i in range(int(self.job_array_start), int(self.job_array_end)+1, int(self.job_array_step)):
        inx.append(str(i))
      inx = ",".join(inx)
      self.assertEqual(res, res | {"array_inx": inx})
    if self.cpu_frequency_str:
      self.assertEqual(res, res | {"cpu_freq_min": self.cpu_frequency_str.split("-")[0]})
      self.assertEqual(res, res | {"cpu_freq_max": self.cpu_frequency_str.split("-")[1]})
    if self.dependencies:
      self.assertEqual(res, res | {"dependency": self.dependencies})
    if self.mail_address:
      self.assertEqual(res, res | {"mail-user": self.mail_address})
    if self.mail_types:
      self.assertEqual(res, res | {"mail-type": ','.join(self.mail_types)})
    if self.commands:
      self.assertEqual(res, res | {"wrap": ";".join(self.commands)})

  def test_get_slurm_cmd_line_args(self):
    """
    Test for get_slurm_cmd_line_args. The same as test_to_arg_strings,
    but the assertIN tests for in string, not in list.
    """
    res = self.gen.get_slurm_cmd_line_args()
    if self.account:
      self.assertIn(f"--account={self.account}", res)
    if self.reservation:
      self.assertIn(f"--reservation={self.reservation}", res)
    if self.partition:
      self.assertIn(f"--partition={self.partition}", res)
    if self.job_name:
      self.assertIn(f"--job-name={self.job_name}", res)
    if self.std_out_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"--output={self.std_out_path}.%A_%a", res)
      else:
        self.assertIn(f"--output={self.std_out_path}.%j", res)
    if self.std_err_path:
      if self.job_array_start is not None and self.job_array_end is not None:
        self.assertIn(f"--error={self.std_err_path}.%A_%a", res)
      else:
        self.assertIn(f"--error={self.std_err_path}.%j", res)
    if self.time_str:
      self.assertIn(f"--time={self.time_str}", res)
    if self.mem_per_cpu:
      self.assertIn(f"--mem-per-cpu={self.mem_per_cpu}", res)
    if self.number_of_tasks:
      self.assertIn(f"--ntasks={self.number_of_tasks}", res)
    if self.number_of_cores_per_task:
      self.assertIn(f"--cpus-per-task={self.number_of_cores_per_task}", res)
    if self.exclusive:
      self.assertIn(f"--exclusive", res)
    if self.wait:
      self.assertIn(f"--wait", res)
    if self.job_array_start is not None and self.job_array_end is not None:
      self.assertIn(f"--array={self.job_array_start}-{self.job_array_end}:{self.job_array_step}"
                    f"{'%1' if self.force_sequential else ''}", res)
    if self.cpu_frequency_str:
      self.assertIn(f"--cpu-freq={self.cpu_frequency_str}", res)
    if self.dependencies:
      self.assertIn(f"--dependency={self.dependencies}", res)
    if self.mail_address:
      self.assertIn(f"--mail-user={self.mail_address}", res)
    if self.mail_types:
      self.assertIn(f"--mail-type={','.join(self.mail_types)}", res)


# Derives the class above for multiple versions of SLURM configs to ran on all tests
class BatchSystemGeneratorTestsMinimal(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # no module system
    self.uses_module_system = False
    self.purge_modules_at_start = False
    self.modules = []
    self.expected_module_order = []
    self.expected_module_error = False
    # no jobarray
    self.job_array_start = None
    self.job_array_end = None
    self.job_array_step = None
    # no commands
    self.commands = []


class BatchSystemGeneratorTestsMaximal(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # another shell
    self.shell = "/bin/fish"
    # other user detail (with some special chars)
    self.partition = "!§$%&/()="
    self.reservation = "VJTZg mg fjt&/"
    self.account = "234567890"
    self.wait = True
    # other mail details
    self.mail_address = "complicatedtest§$%&/()@mail/(/(&&%%%.de"
    self.mail_types = [MailType.BEGIN, MailType.END, MailType.ALL, MailType.FAIL, MailType.NONE]
    # other hardware settings
    self.number_of_tasks = 96
    self.number_of_cores_per_task = 96
    self.mem_per_cpu = 4321
    self.cpu_frequency_str = "Medium-Medium"
    self.time_str = "00:59:00"
    self.in_minutes = 59
    self.exclusive = True
    self.dependencies = "afterok:123434"
    # other out and err paths
    self.std_out_path = "/home/piratest/piratest/a/b12/78-98/test.out"
    self.std_err_path = "/home/piratest/piratest/t/c21/98-12/test.err"
    # module system
    self.uses_module_system = True
    self.purge_modules_at_start = True
    self.use_set_u = True
    self.modules = [
      {"name": "gcc"},
      {"name": "make", "version": "9.7", "depends_on": [{"name": "cuda", "version": "10.2"}]},
      {"name": "cmake"},
      {"name": "cuda", "version": "10.2", "depends_on": [{"name": "gcc"}]},
    ]
    self.expected_module_order = ["gcc", "cmake", "cuda/10.2", "make/9.7"]
    self.expected_module_error = False
    # commands
    self.commands = [
      "a", "b", "c", "aslkdjalkdj", "12334576876", "§$%&/()(/&", "/usr/bin/time"
    ]
    self.job_array_start = 1
    self.job_array_end = 5
    self.job_array_step = 1
    self.force_sequential = True


class BatchSystemGeneratorTestsModuleOrder1(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # module system
    self.uses_module_system = False
    self.purge_modules_at_start = True
    self.modules = []
    self.expected_module_order = []
    self.expected_module_error = False
    # everything other: minimal
    self.job_array_start = None
    self.job_array_end = None
    self.job_array_step = None
    self.commands = []


class BatchSystemGeneratorTestsModuleOrder2(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # module system
    self.uses_module_system = True
    self.purge_modules_at_start = True
    self.modules = []
    self.expected_module_order = []
    self.expected_module_error = False
    # everything other: minimal
    self.job_array_start = None
    self.job_array_end = None
    self.job_array_step = None
    self.commands = []


class BatchSystemGeneratorTestsModuleOrder3(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # module system
    self.uses_module_system = True
    self.purge_modules_at_start = False
    self.modules = [
      {"name": "gcc"},
      {"name": "cuda", "version": "10.2", "depends_on": [{"name": "gcc"}]},
      {"name": "cmake"},
      {"name": "make", "version": "9.7", "depends_on": [{"name": "cuda"}]}
    ]
    self.expected_module_order = ["gcc", "cmake", "cuda/10.2", "make/9.7"]
    self.expected_module_error = False
    # everything other: minimal
    self.job_array_start = None
    self.job_array_end = None
    self.job_array_step = None
    self.commands = []


class BatchSystemGeneratorTestsJobarray(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # module system: minimal
    self.uses_module_system = False
    self.purge_modules_at_start = False
    self.modules = []
    self.expected_module_order = []
    self.expected_module_error = False
    # job array:
    self.job_array_start = 0
    self.job_array_end = 10
    self.job_array_step = 1
    # commands minimal
    self.commands = []


class BatchSystemGeneratorTestsJobarray2(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # module system: minimal
    self.uses_module_system = False
    self.purge_modules_at_start = False
    self.modules = []
    self.expected_module_order = []
    self.expected_module_error = False
    # job array:
    self.job_array_start = 0
    self.job_array_end = 10
    self.job_array_step = 2
    # commands minimal
    self.commands = []


class BatchSystemGeneratorTestsPySlurmArgs(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set time and in_minutes to test the get_pyslurm_args time conversion
    self.time_str = "42"
    self.in_minutes = 42


class BatchSystemGeneratorTestsPySlurmArgs2(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set time and in_minutes to test the get_pyslurm_args time conversion
    self.time_str = "42:42"
    self.in_minutes = 43


class BatchSystemGeneratorTestsPySlurmArgs3(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set time and in_minutes to test the get_pyslurm_args time conversion
    self.time_str = "42:12:42"
    self.in_minutes = 2533


class BatchSystemGeneratorTestsPySlurmArgs4(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set time and in_minutes to test the get_pyslurm_args time conversion
    self.time_str = "2-12"
    self.in_minutes = 3600


class BatchSystemGeneratorTestsPySlurmArgs5(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set time and in_minutes to test the get_pyslurm_args time conversion
    self.time_str = "1-09:07"
    self.in_minutes = 1987


class BatchSystemGeneratorTestsPySlurmArgs6(BatchSystemGeneratorTests):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set time and in_minutes to test the get_pyslurm_args time conversion
    self.time_str = "1-9:7:51"
    self.in_minutes = 1988
