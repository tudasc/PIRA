"""
File: Configuration.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Module that provides to main data structures.
"""

import sys

# from lib.BatchSystemGenerator import MailType

sys.path.append('..')
import lib.Logging as L
import lib.Exception as E
import lib.Utility as U
import typing
from argparse import Namespace


class PiraConfigErrorException(E.PiraException):

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

  def set_base_path(self, path: str) -> None:
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


class PiraConfigII:

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


class PiraConfigAdapter:

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


class PiraConfig:
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
    return [x for x in self.builds.keys()]

  def get_place(self, dir):
    return dir

  def get_items(self, b: str) -> typing.List[str]:
    return [x for x in self.items[b].keys()]

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


class TargetConfig:
  """  The TargetConfiguration encapsulates the relevant information for a specific target, i.e., its place and a given flavor. 
  Using TargetConfiguration all steps of building and executing are possible.  """

  def __init__(self, place: str, build: str, target: str, flavor: str, db_item_id: str):
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
      L.get_logger().log('TargetConfiguration::get_args_for_invocation: args are None.',
                         level='warn')

    return self._args_for_invocation

  def set_args_for_invocation(self, args) -> None:
    self._args_for_invocation = args

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


class ExtrapConfig:

  def __init__(self, dir: str, prefix: str, postfix: str):
    self._dir = dir
    self._prefix = prefix
    self._postfix = postfix

  def get_dir(self) -> str:
    return self._dir

  def get_prefix(self) -> str:
    return self._prefix


class InvocationConfig:

  __instance = None

  @staticmethod
  def get_instance():
    if InvocationConfig.__instance == None:
      L.get_logger().log('InvocationConfig::get_instance: InvocationConfig not initialized.',
                         level='error')
      raise Exception('InvocationConfiguration not initialized!')
    return InvocationConfig.__instance

  def __init__(self, cmdline_args: Namespace):

    if InvocationConfig.__instance != None:
      L.get_logger().log('InvocationConfig::__init__: InvocationConfig already initialized!',
                         level='error')
      raise Exception('re-initializing Singleton')

    else:
      InvocationConfig.__instance = self
      self._pira_dir = cmdline_args.pira_dir
      self._slurm_config_path = cmdline_args.slurm_config
      self._config_version = cmdline_args.config_version
      self._config_path = cmdline_args.config
      self._compile_time_filtering = not (cmdline_args.runtime_filter or
                                          (cmdline_args.hybrid_filter_iters != 0))
      self._pira_iters = cmdline_args.iterations
      self._repetitions = cmdline_args.repetitions
      self._hybrid_filter_iters = cmdline_args.hybrid_filter_iters
      self._export = cmdline_args.export
      self._export_runtime_only = cmdline_args.export_runtime_only
      self._use_call_site_instrumentation = cmdline_args.call_site_instrumentation
      self._lide = cmdline_args.lide
      self._analysis_parameters_path = cmdline_args.analysis_parameters

  def __str__(self) -> str:
    cf_str = 'runtime filtering'
    if self.is_hybrid_filtering():
      cf_str = 'hybrid filtering: rebuilding every ' + str(
          self.get_hybrid_filter_iters()) + ' iterations'
    if self.is_compile_time_filtering():
      cf_str = 'compiletime filtering'
    return 'Running PIRA in ' + cf_str + ' with configuration\n ' + str(self.get_path_to_cfg())

  @staticmethod
  def reset_to_default() -> None:
    if InvocationConfig.__instance == None:
      L.get_logger().log(
          'InvocationConfig::reset_to_default: InvocationConfig not initialized, creating a new instance',
          level='warn')
      cmdline_args = Namespace(pira_dir=U.get_default_pira_dir(),
                               slurm_config=None,
                               config_version=2,
                               config=U.get_default_config_file(),
                               runtime_filter=False,
                               hybrid_filter_iters=0,
                               iterations=4,
                               repetitions=5,
                               export=False,
                               export_runtime_only=False,
                               lide=False,
                               analysis_parameters=U.get_default_analysis_parameters_config_file(),
                               call_site_instrumentation=False)
      InvocationConfig(cmdline_args)

    else:
      instance = InvocationConfig.__instance

      instance._pira_dir = U.get_default_pira_dir()
      instance._slurm_config_path = None
      instance._config_version = 2
      instance._config_path = U.get_default_config_file()
      instance._compile_time_filtering = True
      instance._pira_iters = 4
      instance._repetitions = 3
      instance._hybrid_filter_iters = 0
      instance._export = False
      instance._export_runtime_only = False
      instance._lide = False
      instance._use_call_site_instrumentation = False
      instance._analysis_parameters_path = U.get_default_analysis_parameters_config_file()

  @staticmethod
  def create_from_kwargs(args: dict) -> None:

    required_args = [
        'runtime_filter', 'iterations', 'repetitions', 'hybrid_filter_iters', 'export',
        'export_runtime_only', 'config_version'
    ]
    for arg in required_args:
      if args.get(arg) == None or InvocationConfig.__instance == None:
        InvocationConfig.reset_to_default()
        L.get_logger().log(
            "Invocation-Config not fully initialized. Assuming one or more default values",
            level='warn')
        break

    instance = InvocationConfig.__instance

    if args.get('config') != None:
      instance._config_path = args['config']

    if args.get('pira_dir') != None:
      instance._pira_dir = args['pira_dir']

    if args.get('slurm-config') != None:
      instance._slurm_config_path = args['slurm-config']
    else:
      # set it None, if flag was not given
      # (will decide the local vs. slurm branch)
      instance._slurm_config_path = None

    if args.get('config_version') != None:
      instance._config_version = args['config_version']

    if args.get('hybrid_filter_iters') != None and args.get('runtime_filter') != None:
      instance._compile_time_filtering = not (args['runtime_filter'] or
                                              (args['hybrid_filter_iters'] != 0))

    if args.get('iterations') != None:
      instance._pira_iters = args['iterations']

    if args.get('repetitions') != None:
      instance._repetitions = args['repetitions']

    if args.get('hybrid_filter_iters') != None:
      instance._hybrid_filter_iters = args['hybrid_filter_iters']

    if args.get('export') != None:
      instance._export = args['export']

    if args.get('export_runtime_only') != None:
      instance._export_runtime_only = args['export_runtime_only']

    if args.get('use_cs_instrumentation') != None:
      instance._use_call_site_instrumentation = args['use_cs_instrumentation']

  def get_pira_dir(self) -> str:
    return self._pira_dir

  def get_slurm_config_path(self) -> str:
    return self._slurm_config_path

  def get_config_version(self) -> str:
    return self._config_version

  def is_compile_time_filtering(self) -> bool:
    return self._compile_time_filtering

  def get_path_to_cfg(self) -> str:
    return self._config_path

  def get_hybrid_filter_iters(self) -> int:
    return self._hybrid_filter_iters

  def is_hybrid_filtering(self) -> bool:
    return not self.get_hybrid_filter_iters() == 0

  def get_pira_iters(self) -> int:
    return self._pira_iters

  def get_num_repetitions(self) -> int:
    return self._repetitions

  def is_export(self) -> bool:
    return self._export

  def is_export_runtime_only(self) -> bool:
    return self._export_runtime_only

  def is_lide_enabled(self) -> bool:
    return self._lide

  def get_analysis_parameters_path(self) -> str:
    return self._analysis_parameters_path

  def use_cs_instrumentation(self) -> bool:
    return self._use_call_site_instrumentation


class CSVConfig:

  def __init__(self, csv_dir: str, csv_dialect: str):
    self._csv_dir = csv_dir
    self._csv_dialect = csv_dialect

  def should_export(self) -> bool:
    return self._csv_dir != ''

  def get_csv_dir(self) -> str:
    return self._csv_dir

  def get_csv_dialect(self) -> str:
    return self._csv_dialect


class BatchSystemHardwareConfig:
  """
  Base class for Hardware config. Holding all hardware data.
  """

  def __init__(self,
               mem_per_cpu: int,
               number_of_tasks: int,
               number_of_cores_per_task: int,
               cpu_frequency_str: typing.Optional[str] = None,
               shell: str = "/bin/bash"):
    """
    Constructor.
    :param mem_per_cpu: Memory per thread, the --mem-per-cpu setting.
    :param number_of_tasks: Number of cores/individual processing units you want, the -n or --ntasks setting.
    E.g. important for MPI.
    :param number_of_cores_per_task: Number of threads per process you want, the --cpus-per-task or -c setting.
    :param cpu_frequency_str: Set this to ensure the processors run on equal speeds
    (disables all fancy overclocking, hyperboots, ... features), the --cpu-freq setting.
    Do not specify if you do not want a fixed cpu speed. Default: None.
    :param shell: The shell/shebang for the system. Default: "/bin/bash".
    """
    self.mem_per_cpu = mem_per_cpu
    self.number_of_tasks = number_of_tasks
    self.number_of_cores_per_task = number_of_cores_per_task
    self.cpu_frequency_str = cpu_frequency_str
    self.shell = shell


class SlurmConfig(BatchSystemHardwareConfig):
  """
  Holds config for SLURM run. This info can than be used to sbatch it as SLURM job via a job script, or srun it.
  """

  def __init__(self,
               slurm_script_file: str = f"{U.get_default_pira_dir()}/pira-slurm-job.sh",
               job_name: str = "pira-slurm-job",
               std_out_path: str = f"{U.get_default_pira_dir()}/pira-slurm-out",
               std_err_path: str = f"{U.get_default_pira_dir()}/pira-slurm-err",
               mem_per_cpu: int = 1000,
               number_of_tasks: int = 1,
               number_of_cores_per_task: int = 1,
               time_str: str = "00:10:00",
               cpu_frequency_str: typing.Optional[str] = None,
               shell: str = "/bin/bash",
               partition: typing.Optional[str] = None,
               reservation: typing.Optional[str] = None,
               account: typing.Optional[str] = None,
               job_array_start: typing.Optional[int] = None,
               job_array_end: typing.Optional[int] = None,
               job_array_step: int = 1,
               exclusive: bool = False,
               wait: bool = False,
               dependencies: typing.Optional[typing.List[str]] = None,
               mail_types=None,
               mail_address: typing.Optional[str] = None,
               uses_module_system: bool = False,
               purge_modules_at_start: bool = True,
               check_interval_in_seconds: int = 5,
               modules: typing.List[typing.Dict[str,
                                                typing.Union[str,
                                                             typing.List[typing.Dict[str,
                                                                                     str]]]]] = {},
               force_sequential: bool = False) -> None:
    """
    Constructor. Check here for defaults of the config. If not given by the loader, these defaults will be in place
    in the resulting config.

    :param slurm_script_file: The file to save the SLURM script.
    :param job_name: Job name, -J or --job-name setting.
    :param std_out_path: Path to put the stdout of the job, -o or --out setting. Give the absolute file path.
    The job id will be added at the back automatically.
    :param std_err_path: Path to put the stderr of the job, -e or --err setting. Give the absolute file path.
    The job id will be added at the back automatically.
    :param mem_per_cpu: Memory per thread, the --mem-per-cpu setting.
    :param number_of_tasks: Number of cores/individual processing units you want, the -n or --ntasks setting.
    E.g. important for MPI.
    :param number_of_cores_per_task: Number of threads per process you want, the --cpus-per-task or -c setting.
    :param time_str: Time limit for the job, --time or -t setting.
    :param cpu_frequency_str: Set this to ensure the processors run on equal speeds, the --cpu-freq setting.
    Do not specify if you do not want a fixed cpu speed.
    :param shell: The shell/shebang for the system.
    :param partition: Partition for the job, -p or --partition setting.
    :param reservation: Reservation for the job, the --reservation setting.
    :param account: Allocation for the job, the -A option.
    :param job_array_start: Start id for job array, part of the -a setting.
    If you do not want a job array, do not specify job_array_start and job_array_end.
    :param job_array_end: End id for job array, part of the -a setting.
    If you do not want a job array, do not specify job_array_start and job_array_end.
    :param job_array_step: Step for the job array, part of the -a setting.
    :param wait: Whether the sbatch command should block until the job is finished.
    :param dependencies: List of dependency stings.
    :param mail_types: Mail types, the --mail-type setting.
    If not specified, --mail-type=NONE will be set automatically.
    :param mail_address: Mail address, the --mail-user setting.
    :param uses_module_system: Whether the system uses a module system, with "module load/purge" commands.
    :param purge_modules_at_start: If modules should be purged bevor module load commands.
    Has no effect if "uses_module_system" is not True.
    :param check_interval: Check interval in seconds for wait method.
    :param force_sequential: Whether to force all executions to be sequential on slurm runs.
    """
    super().__init__(mem_per_cpu, number_of_tasks, number_of_cores_per_task, cpu_frequency_str,
                     shell)
    self.slurm_script_file = slurm_script_file
    self.job_name = job_name
    self.std_out_path = std_out_path
    self.std_err_path = std_err_path
    self.time_str = time_str
    self.partition = partition
    self.reservation = reservation
    self.account = account
    self.job_array_start = job_array_start
    self.job_array_end = job_array_end
    self.job_array_step = job_array_step
    self.wait = wait
    self.exclusive = exclusive
    self.dependencies = dependencies
    self.mail_types = mail_types
    self.mail_address = mail_address
    self.uses_module_system = uses_module_system
    self.purge_modules_at_start = purge_modules_at_start
    self.check_interval = check_interval_in_seconds
    self.modules = modules
    self.force_sequential = force_sequential
