"""
File: Measurement.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module hosts measurement support infrastructure.
"""

import lib.Utility as u
import lib.Logging as log
import lib.DefaultFlags as defaults
from lib.Configuration import PiraConfiguration, TargetConfiguration, InstrumentConfig
from lib.Exception import PiraException

import typing


class MeasurementSystemException(PiraException):
  """  This exception is thrown if problems in the runtime occur.  """

  def __init__(self, message):
    super().__init__(message)


class RunResult:
  """  Holds the result of a measurement execution with potentially multiple iterations.  """

  def __init__(self, accumulated_runtime: float = None, nr_of_iterations: int = None, rt_trace=None):
    """Initializes the class

    :accumulated_runtime: TODO
    :nr_of_iterations: TODO
    :average: TODO

    """
    if accumulated_runtime is not None:
      self._accumulated_runtime = [accumulated_runtime]
    else:
      self._accumulated_runtime = []
    if nr_of_iterations is not None:
      self._nr_of_iterations = [nr_of_iterations]
    else:
      self._nr_of_iterations = []
    if rt_trace is not None:
      self._rt_trace = [rt_trace]
    else:
      self._rt_trace = []

  def is_multi_value(self):
    return len(self._accumulated_runtime) > 1

  def add_values(self, accu_rt: float, nr_iter: int) -> None:
    self._accumulated_runtime.append(accu_rt)
    self._nr_of_iterations.append(nr_iter)
    self._rt_trace.append(None)

  def add_from(self, other) -> None:
    for (accu, iters) in zip(other._accumulated_runtime, other._nr_of_iterations):
      self._accumulated_runtime.append(accu)
      self._nr_of_iterations.append(iters)

  def get_average(self, pos: int = 0) -> float:
    if self._nr_of_iterations == 0 or self._nr_of_iterations == []:
      log.get_logger().log('Calculating average based on 0 repetitions - assuming 1', level='warn')
      raise RuntimeError('Calculating average based on 0 repetitions impossible.')
      self._nr_of_iterations = 1
    return self._accumulated_runtime[pos] / self._nr_of_iterations[pos]

  def compute_overhead(self, base_line, pos: int = 0) -> float:
    base_line_avg = base_line.get_average(pos)
    if base_line_avg == 0:
      base_line_avg = 1
    result = self.get_average(pos) / base_line_avg
    return result

  def get_all_averages(self) -> typing.List[float]:
    avgs = []
    for (rt, ni) in zip(self._accumulated_runtime, self._nr_of_iterations):
      avgs.append(rt / ni)

    return avgs

  def compute_all_overheads(self, base_line: typing.List) -> typing.List[float]:
    ovhds = []
    for (thisAvg, otherAvg) in zip(self.get_all_averages(), base_line.get_all_averages()):
      ovhds.append(thisAvg / otherAvg)

    return ovhds


class ScorepSystemHelper:
  """  Takes care of setting necessary environment variables appropriately.  """

  def __init__(self, config: PiraConfiguration) -> None:
    self.known_files = ['.cubex']
    self.config = config
    self.data = {}
    self.cur_mem_size = ''
    self.cur_exp_directory = ''
    self.cur_overwrite_exp_dir = 'False'
    self.cur_base_name = ''
    self.cur_filter_file = ''
    self._enable_unwinding = 'False'
    self._MPI_filter_so_path = ''

  def get_data_elem(self, key: str):
    try:
      if key in self.data.keys():
        return self.data[key]

    except KeyError:
      pass

    log.get_logger().log('Key ' + key + ' was not found in ScorepSystemHelper')
    return ''

  def set_up(self, target_config: TargetConfiguration, instrumentation_config: InstrumentConfig,
             compile_time_filter: bool) -> None:
    if not target_config.is_compile_time_filtering():
      scorep_filter_file = self.prepare_scorep_filter_file(target_config.get_instr_file())
      self.set_filter_file(scorep_filter_file)

    self._set_up(target_config.get_build(), target_config.get_target(), target_config.get_flavor(),
                 instrumentation_config.get_instrumentation_iteration(),
                 instrumentation_config.is_instrumentation_run())

  def prepare_scorep_filter_file(self, filter_file: str) -> None:
    ''' 
        Prepares the file that Score-P uses to include or exclude. 
        NOTE: The filter_file is a positive list! We want to include these functions!
    '''
    file_dir = u.get_base_dir(filter_file)
    file_content = u.read_file(filter_file)
    scorep_filter_file_content = self.append_scorep_footer(self.prepend_scorep_header(file_content))
    scorep_filter_file_name = file_dir + '/scorep_filter_file.txt'
    u.write_file(scorep_filter_file_name, scorep_filter_file_content)
    return scorep_filter_file_name

  def _set_up(self, build, item, flavor, it_nr, is_instr_run) -> None:
    log.get_logger().log('ScorepSystemHelper::_set_up: is_instr_run: ' + str(is_instr_run), level='debug')
    if not is_instr_run:
      return

    exp_dir = self.config.get_analyser_exp_dir(build, item)
    log.get_logger().log(
        'ScorepSystemHelper::_set_up: Retrieved analyser experiment directory: ' + exp_dir, level='debug')
    effective_dir = u.get_cube_file_path(exp_dir, flavor, it_nr)
    if not u.check_provided_directory(effective_dir):
      log.get_logger().log(
          'ScorepSystemHelper::_set_up: Experiment directory does not exist.  \nCreating path: ' + effective_dir,
          level='debug')
      u.create_directory(effective_dir)

    db_exp_dir = u.build_cube_file_path_for_db(exp_dir, flavor, it_nr)
    self.data['cube_dir'] = db_exp_dir
    self.set_exp_dir(exp_dir, flavor, it_nr)
    self.set_memory_size('500M')
    self.set_overwrite_exp_dir()
    self.set_profiling_basename(flavor, build, item)
    # TODO WHEN FIXED: FOR NOW LET'S ENABLE UNWINDING
    # self.set_enable_unwinding(self)


  def set_memory_size(self, mem_str: str) -> None:
    self.cur_mem_size = mem_str
    u.set_env('SCOREP_TOTAL_MEMORY', self.cur_mem_size)

  def set_profiling_basename(self, flavor: str, base: str, item: str) -> None:
    self.cur_base_name = flavor + '-' + item
    u.set_env('SCOREP_PROFILING_BASE_NAME', self.cur_base_name)

  def set_exp_dir(self, exp_dir: str, flavor: str, iterationNumber: int) -> None:
    effective_dir = u.get_cube_file_path(exp_dir, flavor, iterationNumber)
    if not u.is_valid_file_name(effective_dir):
      raise MeasurementSystemException('Score-p experiment directory invalid.')

    self.cur_exp_directory = effective_dir
    u.set_env('SCOREP_EXPERIMENT_DIRECTORY', self.cur_exp_directory)
    return

  def get_exp_dir(self) -> str:
    assert (self.cur_exp_directory is not '')
    return self.cur_exp_directory

  def set_overwrite_exp_dir(self) -> None:
    self.cur_overwrite_exp_dir = 'True'
    u.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY', self.cur_overwrite_exp_dir)

  def set_enable_unwinding(self) -> None:
    self._enable_unwinding = 'True'
    u.set_env('SCOREP_ENABLE_UNWINDING', self._enable_unwinding)

  def set_filter_file(self, file_name: str) -> None:
    log.get_logger().log('ScorepMeasurementSystem::set_filter_file: File for runtime filtering = ' + file_name)
    if not u.is_valid_file_name(file_name):
      raise MeasurementSystemException('Score-P filter file not valid.')

    self.cur_filter_file = file_name
    u.set_env('SCOREP_FILTERING_FILE', self.cur_filter_file)

  def append_scorep_footer(self, input_str: str) -> str:
    return input_str + '\nSCOREP_REGION_NAMES_END\n'

  def prepend_scorep_header(self, input_str: str) -> str:
    line = 'SCOREP_REGION_NAMES_BEGIN\nEXCLUDE *\nINCLUDE MANGLED '
    return line + input_str

  @classmethod
  def get_config_libs(cls) -> str:
    return '`scorep-config --nomemory --libs`'

  @classmethod
  def get_config_ldflags(cls) -> str:
    return '`scorep-config --nomemory --ldflags`'

  @classmethod
  def get_additional_libs(cls) -> str:
    return '-lscorep_adapter_memory_mgmt -lscorep_alloc_metric'

  @classmethod
  def get_instrumentation_flags(cls, instr_file: str, compile_time_filter: bool) -> str:
    default_provider = defaults.BackendDefaults()
    flags = default_provider.get_default_instrumentation_flag() + ' '
    if compile_time_filter:
      flags += default_provider.get_default_instrumentation_selection_flag() + '=' + instr_file
    return flags

  @classmethod
  def get_scorep_compliant_CC_command(cls, instr_file: str, compile_time_filter: bool = True) -> str:
    """ Returns instrumentation flags for the C compiler.

    :instr_file: str: The file name to use for filtering
    :compile_time_filter: bool: Should compile-time filtering be used (default)
    """
    default_provider = defaults.BackendDefaults()
    log.get_logger().log('ScorepSystemHelper::get_scorep_compliant_CC_command: ', level='debug')
    cc_str = default_provider.get_default_c_compiler_name() + ' ' + cls.get_instrumentation_flags(
        instr_file, compile_time_filter)
    return '\"' + cc_str + '\"'

  @classmethod
  def get_scorep_compliant_CXX_command(cls, instr_file: str, compile_time_filter: bool = True) -> str:
    """ Returns instrumentation flags for the C++ compiler.

    :instr_file: str: The file name to use for filtering
    :compile_time_filter: bool: Should compile-time filtering be used (default)
    """
    default_provider = defaults.BackendDefaults()
    cxx_str = default_provider.get_default_cpp_compiler_name() + ' ' + cls.get_instrumentation_flags(
        instr_file, compile_time_filter)
    return '\"' + cxx_str + '\"'

  @classmethod
  def get_scorep_needed_libs_c(cls) -> str:
    return '\" scorep.init.o ' + cls.get_config_libs() + ' ' + cls.get_config_ldflags() + ' ' + cls.get_additional_libs(
    ) + '\"'

  @classmethod
  def get_scorep_needed_libs_cxx(cls) -> str:
    return '\" scorep.init.o ' + cls.get_config_libs() + ' ' + cls.get_config_ldflags(
    ) + ' -lscorep_adapter_memory_event_cxx_L64 ' + cls.get_additional_libs() + '\"'

  @classmethod
  def check_build_prerequisites(cls) -> None:
    scorep_init_file_name = 'scorep.init.c'
    log.get_logger().log('ScorepMeasurementSystem::check_build_prerequisites: global home dir: ' + u.get_home_dir())
    pira_scorep_resource = u.get_home_dir() + '/resources/scorep.init.c'
    if not u.check_file(scorep_init_file_name):
      u.copy_file(pira_scorep_resource, u.get_cwd() + '/' + scorep_init_file_name)

    # In case something goes wrong with copying
    if u.check_file(scorep_init_file_name):
      u.shell('gcc -c ' + scorep_init_file_name)
    else:
      raise MeasurementSystemException('ScorepMeasurementSystem::check_build_prerequisites: Missing ' +
                                       scorep_init_file_name)

  @classmethod
  def prepare_MPI_filtering(cls, filter_file: str) -> None:
    # Find which MPI functions to filter
    # Get all MPI functions (our filter_file is a WHITELIST)
    mpi_funcs_dump = '/tmp/mpi_funcs.dump'
    u.shell('wrap.py -d > ' + mpi_funcs_dump)
    all_MPI_functions_decls = u.read_file(mpi_funcs_dump).split('\n')
    all_MPI_functions = []
    for fd in all_MPI_functions_decls:
      name = fd[fd.find(' '):fd.find('(')]
      all_MPI_functions.append(name.strip())

    MPI_functions_to_filter = []
    file_content = u.read_file(filter_file).split('\n')
    # We always want to measure MPI_Init and MPI_Finalize
    file_content.append('MPI_Init')
    file_content.append('MPI_Finalize')
    for l in file_content:
      if l.find('MPI_') > -1:
        log.get_logger().log('ScorepSystemHelper::prepare_MPI_filtering: Remove ' + l)
        all_MPI_functions.remove(l)

    # Generate the .c file using the mpi wrap.py script
    log.get_logger().log('ScorepSystemHelper::prepare_MPI_filtering: About to filter ' + str(len(all_MPI_functions)) + ' MPI functions')
    wrap_script = '{{fn PIRA_Filter'
    for mpi_func in all_MPI_functions:
      wrap_script += ' ' + mpi_func

    wrap_script += '}}\n{{callfn}}\n{{endfn}}'
    default_provider = defaults.BackendDefaults()
    wrap_file = default_provider.get_wrap_w_file()
    if u.check_file(wrap_file):
      u.remove_file(wrap_file)
    u.write_file(wrap_file, wrap_script)

    wrap_c_path = default_provider.get_wrap_c_file()
    wrap_command = 'wrap.py -o ' + wrap_c_path + ' ' + wrap_file
    u.shell(wrap_command)
    # Compile it to .so file
    compile_mpi_wrapper_command = 'mpicc -shared -fPIC -o ' + default_provider.get_wrap_so_file() + ' ' + wrap_c_path
    u.shell(compile_mpi_wrapper_command)
