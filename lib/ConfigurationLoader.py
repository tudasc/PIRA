"""
File: ConfigurationLoader.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to read the PIRA configuration from file.
"""

import lib.Utility as util
import lib.Logging as log
from lib.Configuration import PiraConfiguration, PiraConfigurationII, PiraItem, PiraConfigurationAdapter, PiraConfigurationErrorException
from lib.ArgumentMapping import CmdlineCartesianProductArgumentMapper, CmdlineLinearArgumentMapper, ArgumentMapperFactory
import sys
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

  def load_conf(self, config_file: str) -> PiraConfiguration:
    if config_file in self.config_cache:
      return self.config_cache[config_file]

    try:
      file_content = util.read_file(config_file)
      json_tree = json.loads(file_content)
      configuration = self.construct_from_json(json_tree)
      #self.check_paths(configuration)
      self.config_cache[config_file] = configuration
      return configuration

    except PiraConfigurationErrorException as e:
      log.get_logger().log(str(e), level='error')
      sys.exit()

    except Exception as e:
      print('Exception occured ' + str(e))

  def construct_from_json(self, json_tree) -> PiraConfiguration:
    conf = PiraConfiguration()
    # json_to_canonic can construct lists
    conf.set_build_directories(util.json_to_canonic(json_tree[_DESC][_DIRS]))
    conf.populate_build_dict(conf.directories)

    conf.set_global_flavors(util.json_to_canonic(json_tree[_DESC][_G_FLAVORS]))

    for glob_flav in conf.get_global_flavors():
      conf.set_glob_submitter(util.json_to_canonic(json_tree[_DESC][_G_SUBMITTER][glob_flav]), glob_flav)

    for build_dir in conf.directories:
      conf.set_prefix(util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_PREFIX]), build_dir)
      conf.set_items(util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_ITEMS]), build_dir)
      conf.initialize_item_dict(build_dir, conf.builds[build_dir][_ITEMS])

      for item in conf.builds[build_dir][_ITEMS]:
        conf.set_item_instrument_analysis(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_INSTRUMENT_ANALYSIS][item]), build_dir,
            item)
        conf.set_item_builders(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_BUILDERS][item]), build_dir, item)
        conf.set_item_args(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_ARGS]), build_dir, item)
        conf.set_item_runner(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_RUNNER]), build_dir, item)
        conf.set_item_submitter(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_SUBMITTER]), build_dir,
            item)
        conf.set_item_batch_script(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][_RUN][item][_BATCH_SCRIPT]), build_dir,
            item)
        conf.set_flavours(util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][item]), build_dir)
        conf.set_item_flavor(
            util.json_to_canonic(json_tree[_DESC][_BUILDS][build_dir][_FLAVORS][item]), build_dir, item)

    return conf

  def check_paths(self, conf):
    error_message ="Error in configuration-file:\n\n"
    exception_occured = False
    for build_dir in conf.directories:
      if not(util.check_provided_directory(build_dir)):
        error_message += "Build-directory " +build_dir+ " does not exist.\n\n"
        exception_occured = True
      for item in conf.builds[build_dir][_ITEMS]:
        for inst_ana in conf.items[build_dir][item]["instrument_analysis"]:
          if not(util.check_provided_directory(inst_ana)):
            error_message += "Instrument-analysis directory " + inst_ana + " does not exist.\n"
            exception_occured = True
        if not(util.check_provided_directory(conf.items[build_dir][item]["builders"])):
          error_message += "Builders-directory " + conf.items[build_dir][item]["builders"] + " does not exist.\n"
          exception_occured = True
        for arg in conf.items[build_dir][item]["args"]:
          if not(util.check_provided_directory(arg)):
            error_message += "args" + arg + "does not exist.\n"
            exception_occured = True
          if not(util.check_provided_directory(conf.items[build_dir][item]["runner"])):
            error_message += "runner" + conf.items[build_dir][item]["runner"] + "does not exist.\n"
            exception_occured = True
      if exception_occured:
        raise PiraConfigurationErrorException(error_message)


class SimplifiedConfigurationLoader:

  def __init__(self):
    self._config = PiraConfigurationII()
    self.base_mapper = None

  def load_conf(self, config_file: str) -> PiraConfiguration:
    if not util.is_file(config_file):
      raise RuntimeError('SimplifiedConfigurationLoader::load_conf: Invalid config file location "' + config_file + '" [no such file].')

    config_abs = util.get_absolute_path(config_file)
    config_abs_path = config_abs[:config_abs.rfind('/')]
    self._config.set_absolute_base_path(config_abs_path)

    try:
      file_content = util.read_file(config_file)
      json_tree = json.loads(file_content)
      self.parse_from_json(json_tree)

    except Exception as e:
     log.get_logger().log('SimplifiedConfigurationLoader::load_conf: Caught exception "' + str(e))


    return PiraConfigurationAdapter(self._config)

  def is_escaped(self, string: str) -> bool:
    return string.startswith('%')

  def get_parameter(self, item_tree, item_key):
    run_opts = {}
    run_opts['mapper'] = util.json_to_canonic(item_tree[item_key]['argmap']['mapper'])
    params = {}

    param_tree = item_tree[item_key]['argmap']
    file_mapper = False

    if 'pira-file' in param_tree:
      run_opts['pira-file'] = []
      run_opts['pira-file'] = util.json_to_canonic(param_tree['pira-file']['names'])
      param_tree = param_tree['pira-file']
      file_mapper = True

    for param in param_tree:
      parameter = util.json_to_canonic(param)

      if param == 'mapper':
        continue
      if file_mapper and param == 'names':
        continue

      try:
        params[parameter]
      except:
        params[parameter] = []

      params[parameter] = util.json_to_canonic(param_tree[param])

    run_opts['argmap'] = params

    return run_opts

  def create_item_from_json(self, item_key, item_tree):
    pira_item = PiraItem(item_key)

    analyzer_dir = item_tree[item_key]['analyzer']
    cubes_dir = item_tree[item_key]['cubes']
    flavors = item_tree[item_key]['flavors']
    functors_base_path = item_tree[item_key]['functors']
    mode = item_tree[item_key]['mode']

    run_opts = self.get_parameter(item_tree, item_key)

    run_options = ArgumentMapperFactory.get_mapper(run_opts)

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
      directories = util.json_to_canonic(json_tree[_DIRS])

    except Exception as e:
      log.get_logger().log('SimplifiedConfigurationLoader::parse_from_json: ' + str(e))
      directories = {}

    for tld_build in json_tree[_BUILDS]:
      # These are the elements, i.e., %astar and alike
      directory_for_item = util.json_to_canonic(tld_build)
      if self.is_escaped(directory_for_item):
        directory_for_item = directories[directory_for_item[1:]]

      item_tree = util.json_to_canonic(json_tree[_BUILDS][tld_build][_ITEMS])
      for item_key in item_tree:
        pira_item = self.create_item_from_json(item_key, item_tree)

        self._config.add_item(directory_for_item, pira_item)

  def check_paths(self,config) :
    error_message = "Error in configuration-file:\n\n"
    exception_occured = False

    for dir in config.get_directories():
      if not(util.check_provided_directory(dir)):
        error_message += "Directory " + dir + " does not exist.\n"
        exception_occured = True
      for item in config.get_items(dir):
        if not(util.check_provided_directory(item.get_analyzer_dir())):
          error_message += "Analyzer-Directory " + item.get_analyzer_dir() + " does not exist\n"
          exception_occured = True
        if not(util.check_provided_directory(item.get_analyzer_dir())):
          error_message += "Cubes-Directory " + item.get_cubes_dir() + " does not exist\n"
          exception_occured = True
        if not(util.check_provided_directory(item.get_functor_base_path())):
          error_message += "Functors-Base-Directory " + item.get_functor_base_path() + " does not exist\n"
          exception_occured = True
        for flavor in item.get_flavors():
          if not(util.is_file(item.get_functor_base_path() + "/analyse_" + item._name + "_" + flavor + ".py")):
            error_message += "analyse-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True
          if not(util.is_file(item.get_functor_base_path() + "/clean_" + item._name + "_" + flavor + ".py")):
            error_message += "clean-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True
          if not(util.is_file(item.get_functor_base_path() + "/no_instr_" + item._name + "_" + flavor + ".py")):
            error_message += "no_instr-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True
          if not(util.is_file(item.get_functor_base_path() + "/runner_" + item._name + "_" + flavor + ".py")):
            error_message += "runner-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True
          if not(util.is_file(item.get_functor_base_path() + "/" + item._name + "_" + flavor + ".py")):
            error_message += "plain-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True

    if exception_occured:
      raise PiraConfigurationErrorException(error_message)