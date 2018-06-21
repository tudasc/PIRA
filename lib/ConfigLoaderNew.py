import lib.Utility as util
import lib.Logging as log
import json
import typing


class ConfigurationNew:
  """
    A configuration for the Runner.

    TODO: Rename.
          Test the actual internal data structure.
          Remove unnecessary functions from this interface.
    """

  def __init__(self) -> None:
    self.directories = []
    self.builds = {}
    self.items = {}
    self.prefix = []
    self.flavors = {}
    self.instrument_analysis = []
    self.builders = []
    self.args = []
    self.runner = []
    self.submitter = []
    self.global_flavors = []
    self.global_submitter = {}
    self.stop_iteration = {}
    self.is_first_iteration = {}

  def set_build_directories(self, dirs) -> None:
    self.directories = dirs

  def set_glob_flavors(self, glob_flavors) -> None:
    self.global_flavors = glob_flavors

  def set_glob_submitter(self, glob_submitter, glob_flavor) -> None:
    self.global_submitter.update({glob_flavor: glob_submitter})

  def set_prefix(self, prefix, dir) -> None:
    self.builds[dir].update({'prefix': prefix})

  def set_items(self, items, dir) -> None:
    self.builds[dir].update({'items': items})

  def set_flavours(self, flavours, dir) -> None:
    self.builds[dir].update({'flavours': flavours})

  def initialize_build_dict(self, dir) -> None:
    for dirs in dir:
      self.builds.update({dirs: {}})
      self.items.update({dirs: {}})
      self.flavors.update({dirs: {}})

  def initialize_item_dict(self, dir, items) -> None:
    for item in items:
      self.items[dir].update({item: {}})
      self.flavors[dir].update({item: {}})

  def set_item_instrument_analysis(self, inst_analysis, dir, item) -> None:
    self.items[dir][item].update({'instrument_analysis': inst_analysis})

  def set_item_builders(self, builders, dir, item) -> None:
    self.items[dir][item].update({'builders': builders})

  def set_item_args(self, args, dir, item) -> None:
    self.items[dir][item].update({'args': args})

  def set_item_runner(self, runner, dir, item) -> None:
    self.items[dir][item].update({'runner': runner})

  def set_item_submitter(self, submitter, dir, item) -> None:
    self.items[dir][item].update({'submitter': submitter})

  def set_item_batch_script(self, batch_script, dir, item) -> None:
    self.items[dir][item].update({'batch_script': batch_script})

  def set_item_flavor(self, flavors, dir, item) -> None:
    self.flavors[dir][item].update({'flavors': flavors})

  def get_builds(self) -> typing.List[str]:
    return self.builds.keys()

  def get_items(self, b: str) -> typing.List[str]:
    return self.items[b].keys()

  def get_flavors(self, b: str, it: str) -> typing.List[str]:
    return self.flavors[b][it]['flavors']

  def has_local_flavors(self, b: str, it: str) -> bool:
    return len(self.flavors[b][it]['flavors']) > 0

  def get_args(self, b: str, it: str) -> typing.List[str]:
    return self.items[b][it]['args']

  def get_cleaner_path(self, b: str, i: str) -> str:
    return self.items[b][i]['builders']

  def get_builder_path(self, b: str, i: str) -> str:
    return self.items[b][i]['builders']

  def get_analyzer_path(self, b: str, i: str) -> str:
    return self.items[b][i]['instrument_analysis'][0]

  def get_runner_path(self, b: str, i: str) -> str:
    return self.items[b][i]['runner']

  # FIXME Rename some more reasonable // get_builder_path
  def get_flavor_func(self, build: str, item: str) -> str:
    log.get_logger().log('Using a deprecated function: get_flavor_func', level='warn')
    return self.items[build][item]['builders']

  # TODO: We should lift all the accesses to these functor paths etc to the FunctorManagement
  #       entity.
  def get_runner_func(self, build: str, item: str) -> str:
    return self.items[build][item]['runner']

  def get_analyse_func(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][0]

  def get_analyser_exp_dir(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][1]

  def get_analyser_dir(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][2]

  def get_analyse_slurm_func(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][3]

  def is_submitter(self, build: str, item: str) -> bool:
    return self.items[build][item]['submitter'] != ''

  # XXX Apparrently not used
  def get_submitter_func(self, build, item) -> str:
    return self.items[build][item]['submitter']

  def get_batch_script_func(self, build, item) -> str:
    return self.items[build][item]['batch_script']

  def get_benchmark_name(self, benchmark) -> str:
    return benchmark.split('/')[-1:][0]

  def initialize_stopping_iterator(self) -> None:
    for build in self.builds:
      for item in self.builds[build]['items']:
        for flavor in self.builds[build]['flavours']:
          self.stop_iteration[build + item + flavor] = False

  def initialize_first_iteration(self) -> None:
    for build in self.builds:
      for item in self.builds[build]['items']:
        for flavor in self.builds[build]['flavours']:
          self.is_first_iteration[build + item + flavor] = False


class ConfigurationLoader:
  """
    Loads a provided configuration file. May be static in the future.

    """

  def __init__(self):
    self.config_cache = {}

  def load_conf(self, config_file: str) -> ConfigurationNew:
    if config_file in self.config_cache:
      return self.config_cache[config_file]

    file_content = util.read_file(config_file)
    json_tree = json.loads(file_content)
    configuration = self.construct_from_json(json_tree)
    self.config_cache[config_file] = configuration
    return configuration

  def construct_from_json(self, json_tree):
    conf = ConfigurationNew()
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
