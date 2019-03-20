"""
File: ConfigLoaderNew.py
Author: Sachin Manawadi
Email: ?
Github: https://github.com/jplehr
Description: Module to read the PIRA configuration from file.
"""

import lib.Utility as util
import lib.Logging as log
from lib.Configuration import PiraConfiguration, PiraConfigurationII, PiraItem, PiraConfigurationAdapter
from lib.ArgumentMapping import CmdlineCartesianProductArgumentMapper, CmdlineLinearArgumentMapper, ArgumentMapperFactory

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
      self.config_cache[config_file] = configuration
      return configuration

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


class SimplifiedConfigurationLoader:

  def __init__(self):
    self._config = PiraConfigurationII()

  def load_conf(self, confilg_file: str) -> PiraConfiguration:
    if not util.check_file(confilg_file):
      raise RuntimeError('SimplifiedConfigurationLoader::load_conf: Invalid config file.')

    try:
      file_content = util.read_file(confilg_file)
      json_tree = json.loads(file_content)
      self.parse_from_json(json_tree)

    except Exception as e:
      log.get_logger().log('SimplifiedConfigurationLoader::load_conf: Caught exception "' + str(e))

    return PiraConfigurationAdapter(self._config)

  def is_escaped(self, string: str) -> bool:
    return string.startswith('%')

  def create_item_from_json(self, item_key, item_tree):
    pira_item = PiraItem(item_key)

    analyzer_dir = item_tree[item_key]['analyzer']
    cubes_dir = item_tree[item_key]['cubes']
    flavors = item_tree[item_key]['flavors']
    functors_base_path = item_tree[item_key]['functors']
    mode = item_tree[item_key]['mode']

    run_opts = {}
    run_opts['mapper'] = util.json_to_canonic(item_tree[item_key]['argmap']['mapper'])
    params = {}
    for param in item_tree[item_key]['argmap']:
      parameter = util.json_to_canonic(param)
      if param == 'mapper':
        continue
      try:
        params[parameter]
      except:
        params[parameter] = []
      params[parameter] = util.json_to_canonic(item_tree[item_key]['argmap'][param])
    run_opts['argmap'] = params

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
