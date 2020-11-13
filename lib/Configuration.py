"""
File: Configuration.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module that provides to main data structures.
"""

import sys
sys.path.append('..')
import lib.Logging as L
import lib.Exception as E
import lib.Utility as U


import typing


class PiraConfigurationErrorException(E.PiraException):
  def __init__(self, m):
    super().__init__(m)

class PiraItem:

  def __init__(self, name):
    self._name = name
    self._base_path = None
    self._analyzer_dir = None
    self._cubes_dir = None
    self._flavors = None
    self._functor_base_path = None
    self._mode = None
    self._run_options = None

  def __str__(self):
    return '[PiraItem] ' + self._name

  def get_name(self):
    return self._name

  def get_analyzer_dir(self):
    if U.is_absolute_path(self._analyzer_dir):
      return self._analyzer_dir

    return self._base_path + '/' + self._analyzer_dir

  def get_cubes_dir(self):
    if U.is_absolute_path(self._cubes_dir):
      return self._cubes_dir

    return self._base_path + '/' + self._cubes_dir

  def get_flavors(self):
    return self._flavors

  def get_functor_base_path(self):
    if U.is_absolute_path(self._functor_base_path):
      return self._functor_base_path

    return self._base_path + '/' + self._functor_base_path

  def get_mode(self):
    return self._mode

  def get_run_options(self):
    return self._run_options

  def set_base_path(self, path : str) -> None:
    self._base_path = path

  def set_analyzer_dir(self, directory) -> None:
    self._analyzer_dir = directory

  def set_cubes_dir(self, directory) -> None:
    self._cubes_dir = directory

  def set_flavors(self, flavors) -> None:
    self._flavors = flavors

  def set_functors_base_path(self, path) -> None:
    self._functor_base_path = path

  def set_mode(self, mode) -> None:
    self._mode = mode

  def set_run_options(self, run_opts) -> None:
    self._run_options = run_opts


class PiraConfigurationII:

  def __init__(self):
    self._directories = {}
    self._abs_base_path = None
    self._empty = True

  def add_item(self, name, item) -> None:
    try:
      self._directories[name]
    except:
      self._directories[name] = []

    item.set_base_path(self._abs_base_path)

    self._directories[name].append(item)

  def get_directories(self):
    return self._directories.keys()

  def get_place(self, build):
    place = build
    for k in self._directories.keys():
      if place == k:
        if not U.is_absolute_path(k):
          place = self._abs_base_path + '/' + str(k)
    return place

  def get_items(self, directory):
    return self._directories[directory]

  def set_absolute_base_path(self, path):
    self._abs_base_path = path

  def get_absolute_base_path(self):
    return self._abs_base_path

  def is_empty(self) -> bool:
    return self._empty


class PiraConfigurationAdapter:

  def __init__(self, pc2):
    self._pcii = pc2

  def get_adapted(self):
    return self._pcii

  def get_builds(self):
    return self._pcii.get_directories()

  def get_place(self, build):
    return self._pcii.get_place(build)

  def get_items(self, build):
    return [item.get_name() for item in self._pcii.get_items(build)]

  def has_local_flavors(self, build, item):
    return True

  def get_item_w_name(self, build, item):
    items = self._pcii.get_items(build)
    for item_obj in items:
      if item_obj.get_name() == item:
        return item_obj

    raise RuntimeError('Flavors not found for item ' + item)

  def get_flavors(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_flavors()

  def get_analyzer_path(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_functor_base_path()

  def get_analyzer_dir(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_analyzer_dir()

  def get_benchmark_name(self, item):
    return item

  def get_builder_path(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_functor_base_path()

  def get_runner_path(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_functor_base_path()

  def get_runner_func(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_functor_base_path()

  def get_cleaner_path(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_functor_base_path()

  def get_analyzer_exp_dir(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_cubes_dir()

  def get_args(self, build, item):
    io = self.get_item_w_name(build, item)
    return io.get_run_options().as_list()

  def is_empty(self) -> bool:
    return self._pcii.is_empty()


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
    self.base_mapper = None
    self._empty = True

  def is_empty(self) -> bool:
    return self._empty

  def set_build_directories(self, dirs) -> None:
    self.directories = dirs

  def set_global_flavors(self, glob_flavors) -> None:
    self.global_flavors = glob_flavors

  def get_global_flavors(self):
    return self.global_flavors

  def set_glob_submitter(self, glob_submitter, glob_flavor) -> None:
    self.global_submitter.update({glob_flavor: glob_submitter})

  def set_prefix(self, prefix, dir) -> None:
    self.builds[dir].update({'prefix': prefix})

  def set_items(self, items, dir) -> None:
    self.builds[dir].update({'items': items})

  def set_flavours(self, flavours, dir) -> None:
    self.builds[dir].update({'flavours': flavours})

  def populate_build_dict(self, dir) -> None:
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
    return [ x for x in self.builds.keys() ]

  def get_place(self, dir):
    return dir

  def get_items(self, b: str) -> typing.List[str]:
    return [ x for x in self.items[b].keys() ]

  def get_flavors(self, b: str, it: str) -> typing.List[str]:
    return self.flavors[b][it]['flavors']

  def has_local_flavors(self, b: str, it: str) -> bool:
    return len(self.flavors[b][it]['flavors']) > 0

  def get_args(self, b: str, it: str) -> typing.List[typing.List[str]]:
    return [self.items[b][it]['args']]

  def get_cleaner_path(self, b: str, i: str) -> str:
    return self.items[b][i]['builders']

  def get_builder_path(self, b: str, i: str) -> str:
    L.get_logger().log('Old: get_builder_path: ' + self.items[b][i]['builders'], level='debug')
    return self.items[b][i]['builders']

  def get_analyzer_path(self, b: str, i: str) -> str:
    return self.items[b][i]['instrument_analysis'][0]

  def get_runner_path(self, b: str, i: str) -> str:
    return self.items[b][i]['runner']

  # FIXME Rename some more reasonable // get_builder_path
  def get_flavor_func(self, build: str, item: str) -> str:
    L.get_logger().log('Using a deprecated function: get_flavor_func', level='warn')
    return self.items[build][item]['builders']

  # TODO: We should lift all the accesses to these functor paths etc to the FunctorManagement
  #       entity.
  def get_runner_func(self, build: str, item: str) -> str:
    return self.items[build][item]['runner']

  def get_analyze_func(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][0]

  def get_analyzer_exp_dir(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][1]

  def get_analyzer_dir(self, build, item) -> str:
    return self.items[build][item]['instrument_analysis'][2]

  def get_analyze_slurm_func(self, build, item) -> str:
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

  def __init__(self, place: str, build: str, target: str, flavor: str, db_item_id: str, compile_time_filter: bool = True, hybrid_filter_iters: int = 0):
    """  Initializes the TargetConfiguration with its necessary parameters.

    :place: str: TODO
    :target: str: TODO
    :flavor: str: TODO
    :db_item_id: str: The unique ID for this target

    """
    self._place: str = place
    self._build: str = build
    self._target: str = target
    self._flavor: str = flavor
    self._db_item_id: str = db_item_id
    self._compile_time_filtering = compile_time_filter
    self._hybrid_filter_iters = hybrid_filter_iters
    self._instr_file = ''
    self._args_for_invocation = None

  def get_place(self) -> str:
    """Return the place stored in this TargetConfiguration

    :lf: TODO
    :returns: The top-level items, i.e., "builds"

    """
    return self._place

  def get_build(self) -> str:
    """Return the build stored in this TargetConfiguration

    :lf: TODO
    :returns: The top-level items, i.e., "builds"

    """
    return self._build

  def get_target(self) -> str:
    """Return the target / item stored in this TargetConfiguration
    :returns: the targets / items (children of build)

    """
    return self._target

  def get_flavor(self) -> str:
    """Return the flavor stored in this TargetConfiguration
    :returns: TODO

    """
    return self._flavor

  def get_db_item_id(self) -> str:
    """Return the DB item id stored in this TargetConfiguration

    :f: TODO
    :returns: TODO

    """
    return self._db_item_id

  def has_args_for_invocation(self) -> bool:
    return self._args_for_invocation is not None

  def get_args_for_invocation(self) -> str:
    if self._args_for_invocation is None:
      L.get_logger().log('TargetConfiguration::get_args_for_invocation: args are None.', level='warn')

    return self._args_for_invocation

  def set_args_for_invocation(self, args) -> None:
    self._args_for_invocation = args

  def is_compile_time_filtering(self) -> bool:
    """ Returns whether this PIRA instance uses compile-time filtering"""
    return self._compile_time_filtering

  def get_hybrid_filter_iters(self) -> str:
    return self._hybrid_filter_iters

  def is_hybrid_filtering(self) -> bool:
    return not self.get_hybrid_filter_iters() == 0

  def set_instr_file(self, instr_file: str) -> None:
    self._instr_file = instr_file

  def get_instr_file(self) -> str:
    """
    Only valid IFF is_compile_time_filtering returns False!
    :returns: Iff this run is a runtime-filter run, returns the instrumentation file.
    """
    return self._instr_file


class InstrumentConfig:
  """  Holds information how instrumentation is handled in the different run phases.  """

  def __init__(self, is_instrumentation_run=False, instrumentation_iteration=None):
    self._is_instrumentation_run = is_instrumentation_run
    self._instrumentation_iteration = instrumentation_iteration

  def get_instrumentation_iteration(self) -> int:
    return self._instrumentation_iteration

  def is_instrumentation_run(self) -> bool:
    return self._is_instrumentation_run


class ExtrapConfiguration:

  def __init__(self, dir: str, prefix: str, postfix: str):
    self._dir = dir
    self._prefix = prefix
    self._postfix = postfix

  def get_dir(self) -> str:
    return self._dir

  def get_prefix(self) -> str:
    return self._prefix


class InvocationConfiguration:

  def __init__(self, path_to_config: str, pira_dir: str,compile_time_filter: bool, pira_iters: int, num_reps: int, hybrid_filter_iters: int = 0):
    self._path_to_cfg = path_to_config
    self._pira_dir = pira_dir
    self._compile_time_filtering = compile_time_filter
    self._pira_iters = pira_iters
    self._num_repetitions = num_reps
    self._hybrid_filter_iters = hybrid_filter_iters

  def get_path_to_cfg(self) -> str:
    return self._path_to_cfg

  def get_pira_dir(self) -> str:
    return self._pira_dir

  def is_compile_time_filtering(self) -> bool:
    return self._compile_time_filtering

  def get_hybrid_filter_iters(self) -> int:
    return self._hybrid_filter_iters

  def is_hybrid_filtering(self) -> bool:
    return not self.get_hybrid_filter_iters() == 0

  def get_pira_iters(self) -> int:
    return self._pira_iters

  def get_num_repetitions(self) -> int:
    return self._num_repetitions

class CSVConfiguration:

  def __init__(self, csv_dir: str, csv_dialect: str):
    self._csv_dir = csv_dir
    self._csv_dialect = csv_dialect

  def should_export(self) -> bool:
    return self._csv_dir != ''

  def get_csv_dir(self) -> str:
    return self._csv_dir

  def get_csv_dialect(self) -> str:
    return self._csv_dialect