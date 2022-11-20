"""
File: ConfigurationLoader.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Module to read the PIRA configuration from file.
"""

import lib.Utility as U
import lib.Logging as L
from lib.BatchSystemBackends import BatchSystemInterface, BatchSystemBackendType, SlurmBackend, SlurmInterfaces, \
  BatchSystemTimingType
from lib.Configuration import PiraConfig, PiraConfigII, PiraItem, PiraConfigAdapter, PiraConfigErrorException, \
  InvocationConfig, SlurmConfig
from lib.ArgumentMapping import CmdlineCartesianProductArgumentMapper, CmdlineLinearArgumentMapper, ArgumentMapperFactory
from lib.Configuration import BatchSystemHardwareConfig

import os
import sys
import json
import typing
""" 
  These defines are the JSON field names for the configuration 
"""
_BUILDS = 'builds'
_DESC = 'description'
_DIRS = 'directories'
_ITEMS = 'items'
_FLAVORS = 'flavors'
_G_FLAVORS = 'glob-flavors'
_G_SUBMITTER = 'glob-submitter'
_PREFIX = 'prefix'
_BUILDERS = 'builders'
_RUN = 'run'
_ARGS = 'args'
_RUNNER = 'runner'
_SUBMITTER = 'submitter'
_BATCH_SCRIPT = 'batch_script'
_INSTRUMENT_ANALYSIS = 'instrument-analysis'


class ConfigurationLoader:
  """
    Loads a provided configuration file.
  """

  def __init__(self):
    self.config_cache = {}

  def load_conf(self) -> PiraConfig:
    config_file = InvocationConfig.get_instance().get_path_to_cfg()
    if config_file in self.config_cache:
      return self.config_cache[config_file]

    try:
      file_content = U.read_file(config_file)
      json_tree = json.loads(file_content)
      configuration = self.construct_from_json(json_tree)
      self.config_cache[config_file] = configuration
      return configuration

    except PiraConfigErrorException as e:
      L.get_logger().log(str(e), level='error')
      sys.exit()

    except Exception as e:
      print('Exception occured ' + str(e))

  def construct_from_json(self, json_tree) -> PiraConfig:
    conf = PiraConfig()
    # json_to_canonic can construct lists
    conf.set_build_directories(U.json_to_canonic(json_tree[_DESC][_DIRS]))
    conf.populate_build_dict(conf.directories)

    conf.set_global_flavors(U.json_to_canonic(json_tree[_DESC][_G_FLAVORS]))

    for glob_flav in conf.get_global_flavors():
      conf.set_glob_submitter(U.json_to_canonic(json_tree[_DESC][_G_SUBMITTER][glob_flav]),
                              glob_flav)

    for build_dir in conf.directories:
      conf.set_prefix(U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_PREFIX]), build_dir)
      conf.set_items(U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_ITEMS]), build_dir)
      conf.initialize_item_dict(build_dir, conf.builds[build_dir][_ITEMS])

      for item in conf.builds[build_dir][_ITEMS]:
        conf.set_item_instrument_analysis(
            U.json_to_canonic(
                json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_INSTRUMENT_ANALYSIS][item]),
            build_dir, item)
        conf.set_item_builders(
            U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_BUILDERS][item]),
            build_dir, item)
        conf.set_item_args(
            U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_ARGS]),
            build_dir, item)
        conf.set_item_runner(
            U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_RUNNER]),
            build_dir, item)
        conf.set_item_submitter(
            U.json_to_canonic(
                json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_SUBMITTER]), build_dir,
            item)
        conf.set_item_batch_script(
            U.json_to_canonic(
                json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_BATCH_SCRIPT]),
            build_dir, item)
        conf.set_flavours(U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][item]),
                          build_dir)
        conf.set_item_flavor(
            U.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][item]), build_dir,
            item)

    conf._empty = False

    return conf


class SimplifiedConfigurationLoader:

  def __init__(self):
    self._config = PiraConfigII()
    self.base_mapper = None

  def load_conf(self) -> PiraConfig:
    config_file = InvocationConfig.get_instance().get_path_to_cfg()
    if not U.is_file(config_file):
      raise RuntimeError(
          'SimplifiedConfigurationLoader::load_conf: Invalid config file location "' + config_file +
          '" [no such file].')

    config_abs = U.get_absolute_path(config_file)
    config_abs_path = config_abs[:config_abs.rfind('/')]
    self._config.set_absolute_base_path(config_abs_path)

    try:
      file_content = U.read_file(config_file)
      json_tree = json.loads(file_content)
      self.parse_from_json(json_tree)

    except Exception as e:
      L.get_logger().log('SimplifiedConfigurationLoader::load_conf: Caught exception "' + str(e))

    return PiraConfigAdapter(self._config)

  def is_escaped(self, string: str) -> bool:
    return string.startswith('%')

  def get_parameter(self, item_tree, item_key):
    run_opts = {}
    run_opts['mapper'] = U.json_to_canonic(item_tree[item_key]['argmap']['mapper'])

    params = {}

    param_tree = item_tree[item_key]['argmap']
    file_mapper = False

    if 'pira-file' in param_tree:
      run_opts['pira-file'] = []
      run_opts['pira-file'] = U.json_to_canonic(param_tree['pira-file']['names'])
      param_tree = param_tree['pira-file']
      file_mapper = True

    for param in param_tree:
      parameter = U.json_to_canonic(param)

      if param == 'mapper':
        continue
      if file_mapper and param == 'names':
        continue

      try:
        params[parameter]
      except:
        params[parameter] = []

      params[parameter] = U.json_to_canonic(param_tree[param])

      # For slurm integration U.json_to_canonic was updated to respect types int and None
      # But config hold argmap parameters as ints, which PIRA expected to be parsed to string,
      # which is not the case anymore. To correct for this, there are tests for
      # params of type int here, and they are changed to string.
      if isinstance(params[parameter], int):
        params[parameter] = str(params[parameter])
      elif isinstance(params[parameter], list):
        new_params = []
        for p in params[parameter]:
          if isinstance(p, int):
            new_params.append(str(p))
          else:
            new_params.append(p)
        params[parameter] = new_params
        del new_params

    run_opts['argmap'] = params

    return run_opts

  def create_item_from_json(self, item_key: str, item_tree):
    pira_item = PiraItem(item_key)

    analyzer_dir = item_tree[item_key]['analyzer']
    if analyzer_dir == '':
      analyzer_dir = U.get_base_dir(__file__) + '/../extern/install/pgis/bin'
      L.get_logger().log('Analyzer: using analyzer default: ' + analyzer_dir, level='debug')

    cubes_dir = item_tree[item_key]['cubes']
    flavors = item_tree[item_key]['flavors']
    functors_base_path = item_tree[item_key]['functors']
    mode = item_tree[item_key]['mode']

    run_opts = self.get_parameter(item_tree, item_key)

    run_options = ArgumentMapperFactory.get_mapper(run_opts)

    # expand environment variables in directory attributes
    analyzer_dir = os.path.expandvars(analyzer_dir)
    cubes_dir = os.path.expandvars(cubes_dir)
    functors_base_path = os.path.expandvars(functors_base_path)

    pira_item.set_analyzer_dir(analyzer_dir)
    pira_item.set_cubes_dir(cubes_dir)
    pira_item.set_flavors(flavors)
    pira_item.set_functors_base_path(functors_base_path)
    pira_item.set_mode(mode)
    pira_item.set_run_options(run_options)

    return pira_item

  def parse_from_json(self, json_tree) -> None:
    # Top-level key elements // theoretically not required
    try:
      directories = U.json_to_canonic(json_tree[_DIRS])

    except Exception as e:
      L.get_logger().log('SimplifiedConfigurationLoader::parse_from_json: ' + str(e))
      directories = {}

    for tld_build in json_tree[_BUILDS]:
      # These are the elements, i.e., %astar and alike
      directory_for_item = U.json_to_canonic(tld_build)
      if self.is_escaped(directory_for_item):
        directory_for_item = directories[directory_for_item[1:]]

      # expand environment variables in directory value
      directory_for_item = os.path.expandvars(directory_for_item)

      item_tree = U.json_to_canonic(json_tree[_BUILDS][tld_build][_ITEMS])
      for item_key in item_tree:
        L.get_logger().log('SimplifiedConfigurationLoader::parse_from_json: ' + str(item_key))
        pira_item = self.create_item_from_json(item_key, item_tree)
        self._config.add_item(directory_for_item, pira_item)
        self._config._empty = False


class BatchSystemConfigurationLoader:
  """
  Loader for the BatchSystemConfiguration.
  """

  def __init__(self, invoc_cfg: InvocationConfig):
    """
    Constructor.
    """
    self.config_file = invoc_cfg.get_slurm_config_path()
    self.invoc_cfg = invoc_cfg
    self.backend = None
    self.interface = None
    self.timings = None
    self.modules = None

  def get_config(self) -> BatchSystemHardwareConfig:
    """
    Read and return the batch system configuration from the config file.
    """
    if not U.is_file(self.config_file):
      raise RuntimeError('BatchSystemConfigLoader::get_config: Invalid config file location "' +
                         self.config_file + '" [no such file].')
    self.config_file = U.get_absolute_path(self.config_file)
    try:
      file_content = U.read_file(self.config_file)
      json_tree = json.loads(file_content)
      return self.load_from_json(json_tree)
    except Exception as e:
      L.get_logger().log('BatchSystemConfigLoader::get_config: Caught exception "' + str(e))
      raise RuntimeError(e)

  def load_from_json(self, json_tree: dict) -> typing.Union[BatchSystemHardwareConfig, SlurmConfig]:
    """
    Loads config values form the json file contents.
    """
    general = None
    if "general" in json_tree:
      general = U.json_to_canonic(json_tree["general"])
    mod_loads = None
    if "module-loads" in json_tree:
      mod_loads = U.json_to_canonic(json_tree["module-loads"])
    if "batch-settings" in json_tree:
      batch_settings = U.json_to_canonic(json_tree["batch-settings"])
    else:
      L.get_logger().log(
          "BatchSystemConfigLoader::load_from_json: 'batch-settings' section not found in config "
          "file.",
          level="error")
      raise RuntimeError("'batch-settings' section not found in config file.")
    force_sequential = False
    if not general:
      # defaults for general section
      self.backend = BatchSystemBackendType.SLURM
      self.interface = SlurmInterfaces.PYSLURM
      self.timings = BatchSystemTimingType.SUBPROCESS
    else:
      if "backend" in general:
        if general["backend"] == "slurm":
          self.backend = BatchSystemBackendType.SLURM
      else:
        # use default
        self.backend = BatchSystemBackendType.SLURM
      if "interface" in general:
        if general["interface"] == "pyslurm":
          self.interface = SlurmInterfaces.PYSLURM
        elif general["interface"] == "sbatch-wait":
          self.interface = SlurmInterfaces.SBATCH_WAIT
        elif general["interface"] == "os":
          self.interface = SlurmInterfaces.OS
        else:
          L.get_logger().log(
              "BatchSystemConfigLoader::load_from_json: 'general/interface' holds an illegal value: "
              "" + str(general["backend"]) + ". Choices are: 'pyslurm', 'sbatch-wait' or 'os'.",
              level="error")
          raise RuntimeError("'general/interface' holds an illegal value: " +
                             str(general["backend"]) + ". Choices are: "
                             "'pyslurm', 'sbatch-wait' or 'os'.")
      else:
        # use default
        self.interface = SlurmInterfaces.PYSLURM
      if "timings" in general:
        if general["timings"] == "subprocess":
          self.timings = BatchSystemTimingType.SUBPROCESS
        elif general["timings"] == "os":
          self.timings = BatchSystemTimingType.OS_TIME
        else:
          L.get_logger().log(
              "BatchSystemConfigLoader::load_from_json: 'general/timings' holds an illegal value:"
              " " + str(general["timings"]) + ". Choices are: 'subprocess' or 'os'.",
              level="error")
          raise RuntimeError("'general/timings' holds an illegal value: " +
                             str(general["timings"]) + ". "
                             "Choices are: 'subprocess' or 'os'.")
      else:
        # use default
        self.timings = self.timings = BatchSystemTimingType.SUBPROCESS
      if "force-sequential" in general:
        force_sequential = general["force-sequential"]
    modules = None
    if mod_loads:
      if mod_loads is not None:
        modules = []
        for module in mod_loads:
          mod = {}
          if "name" in module:
            mod["name"] = module["name"]
          else:
            L.get_logger().log(
                "BatchSystemConfigLoader::load_from_json: 'module-loads': Every module have to "
                "have a name.",
                level="error")
            raise RuntimeError("'module-loads': Every module have to have a name.")
          if "version" in module:
            if module["version"] is not None:
              mod["version"] = module["version"]
          if "depends-on" in module:
            if module["depends-on"] is not None:
              mod["depends-on"] = []
              for dep_module, index in zip(module["depends-on"], range(len(module["depends-on"]))):
                dep_mod = {}
                if "name" in dep_module:
                  dep_mod["name"] = module["depends-on"][index]["name"]
                else:
                  L.get_logger().log(
                      "BatchSystemConfigLoader::load_from_json: 'module-loads': Every module dependency "
                      "have to have a name.",
                      level="error")
                  raise RuntimeError(f"module-loads': Every module dependency have to have a "
                                     f"name (in module {mod['name']}).")
                if "version" in dep_module:
                  dep_mod["version"] = module["depends-on"][index]["version"]
                mod["depends-on"].append(dep_mod)
          modules.append(mod)
    if not batch_settings:
      L.get_logger().log(
          "BatchSystemConfigLoader::load_from_json: 'batch-settings': 'batch-settings' section not found but mandatory.",
          level="error")
      raise RuntimeError(
          "'general/batch-settings': 'batch-settings' section not found but mandatory.")
    else:
      if "time" in batch_settings:
        time_str = batch_settings["time"]
      else:
        L.get_logger().log(
            "BatchSystemConfigLoader::load_from_json: 'batch-settings/time' option not found but mandatory.",
            level="error")
        raise RuntimeError("'batch-settings/time' option not found but mandatory.")
      if "mem-per-cpu" in batch_settings:
        memcpu = batch_settings["mem-per-cpu"]
      else:
        L.get_logger().log(
            "BatchSystemConfigLoader::load_from_json: 'batch-settings/mem-per-cpu' option not found but mandatory.",
            level="error")
        raise RuntimeError("'batch-settings/mem-per-cpu' option not found but mandatory.")
      if "ntasks" in batch_settings:
        ntasks = batch_settings["ntasks"]
      else:
        L.get_logger().log(
            "BatchSystemConfigLoader::load_from_json: 'batch-settings/ntasks' option not found but mandatory.",
            level="error")
        raise RuntimeError("'batch-settings/ntasks' option not found but mandatory.")
      partition = None
      if "partition" in batch_settings:
        partition = batch_settings["partition"]
      reservation = None
      if "reservation" in batch_settings:
        reservation = batch_settings["reservation"]
      account = None
      if "account" in batch_settings:
        account = batch_settings["account"]
      cpupertask = 1
      if "cpus-per-task" in batch_settings:
        cpupertask = batch_settings["cpus-per-task"]
      exclusive = True
      if "exclusive" in batch_settings:
        exclusive = batch_settings["exclusive"]
      cpufreqstr = None
      if "cpu-freq" in batch_settings:
        cpufreqstr = batch_settings["cpu-freq"]

      return SlurmConfig(mem_per_cpu=memcpu,
                         number_of_tasks=ntasks,
                         number_of_cores_per_task=cpupertask,
                         time_str=time_str,
                         cpu_frequency_str=cpufreqstr,
                         partition=partition,
                         reservation=reservation,
                         account=account,
                         job_array_start=0,
                         job_array_end=self.invoc_cfg.get_num_repetitions() - 1,
                         job_array_step=1,
                         exclusive=exclusive,
                         uses_module_system=True if modules else False,
                         purge_modules_at_start=True,
                         modules=modules,
                         force_sequential=force_sequential)

  def get_batch_interface(self) -> BatchSystemInterface:
    """
    Get the correct BatchInterface subclass upon the parameters.
    """

    batch_interface = None
    if self.backend == BatchSystemBackendType.SLURM:
      batch_interface = SlurmBackend(backend_type=BatchSystemBackendType.SLURM,
                                     interface_type=self.interface,
                                     timing_type=self.timings)
    return batch_interface
