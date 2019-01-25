"""
File: Configuration.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module that provides to main data structures.
"""

import sys
sys.path.append('..')
import lib.Logging as log

import typing


class PiraConfiguration:
  """
    A configuration for PIRA

    TODO: Test the actual internal data structure.
          Remove unnecessary functions from this interface.
          Get rid of direct dependency on this data structure as much as possible.
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

  @staticmethod
  def get_benchmark_name(benchmark) -> str:
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


class TargetConfiguration:
  """  The TargetConfiguration encapsulates the relevant information for a specific target, i.e., its place and a given flavor. 
  Using TargetConfiguration all steps of building and executing are possible.  """

  def __init__(self, place: str, target: str, flavor: str, db_item_id: str):
    """  Initializes the TargetConfiguration with its necessary parameters.

    :place: str: TODO
    :target: str: TODO
    :flavor: str: TODO
    :db_item_id: str: The unique ID for this target

    """
    self._place: str = place
    self._target: str = target
    self._flavor: str = flavor
    self._db_item_id: str = db_item_id

  def get_build(self):
    """Return the place / build stored in this TargetConfiguration

    :lf: TODO
    :returns: The top-level items, i.e., "builds"

    """
    return self._place

  def get_target(self):
    """Return the target / item stored in this TargetConfiguration
    :returns: the targets / items (children of build)

    """
    return self._target

  def get_flavor(self):
    """Return the flavor stored in this TargetConfiguration
    :returns: TODO

    """
    return self._flavor

  def get_db_item_id(self):
    """Return the DB item id stored in this TargetConfiguration

    :f: TODO
    :returns: TODO

    """
    return self._db_item_id
