import lib.Utility as util
import lib.Logging as log
import lib.Configuration as C
import json
import typing



class ConfigurationLoader:
  """
    Loads a provided configuration file. May be static in the future.

    """

  def __init__(self):
    self.config_cache = {}

  def load_conf(self, config_file: str) -> C.PiraConfiguration:
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

  def construct_from_json(self, json_tree):
    conf = C.PiraConfiguration()
    conf.set_build_directories(util.json_to_canonic(json_tree['description']['directories']))
    conf.initialize_build_dict(conf.directories)
    conf.set_glob_flavors(util.json_to_canonic(json_tree['description']['glob-flavors']))
    for glob_flav in conf.global_flavors:
      conf.set_glob_submitter(
          util.json_to_canonic(json_tree['description']['glob-submitter'][glob_flav]), glob_flav)
    for build_dirs in conf.directories:
      conf.set_prefix(
          util.json_to_canonic(json_tree['description']['builds'][build_dirs]['prefix']), build_dirs)
      conf.set_items(
          util.json_to_canonic(json_tree['description']['builds'][build_dirs]['items']), build_dirs)
      conf.initialize_item_dict(build_dirs, conf.builds[build_dirs]['items'])
      for items in conf.builds[build_dirs]['items']:
        conf.set_item_instrument_analysis(
            util.json_to_canonic(
                json_tree['description']['builds'][build_dirs]['flavors']['instrument-analysis'][items]),
            build_dirs, items)
        conf.set_item_builders(
            util.json_to_canonic(
                json_tree['description']['builds'][build_dirs]['flavors']['builders'][items]), build_dirs,
            items)
        conf.set_item_args(
            util.json_to_canonic(
                json_tree['description']['builds'][build_dirs]['flavors']['run'][items]['args']), build_dirs,
            items)
        conf.set_item_runner(
            util.json_to_canonic(
                json_tree['description']['builds'][build_dirs]['flavors']['run'][items]['runner']),
            build_dirs, items)
        conf.set_item_submitter(
            util.json_to_canonic(
                json_tree['description']['builds'][build_dirs]['flavors']['run'][items]['submitter']),
            build_dirs, items)
        conf.set_item_batch_script(
            util.json_to_canonic(
                json_tree['description']['builds'][build_dirs]['flavors']['run'][items]['batch_script']),
            build_dirs, items)
        conf.set_flavours(
            util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors'][items]),
            build_dirs)
        conf.set_item_flavor(
            util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors'][items]),
            build_dirs, items)

    return conf
