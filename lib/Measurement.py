import lib.Utility as u
import lib.Logging as log
import lib.ConfigLoaderNew as cln

import typing


class MeasurementSystemException(Exception):
  def __init__(self, message):
    super().__init__(message)


class RunResult:
  """Holds the result of a measurement execution with potentially multiple iterations."""

  def __init__(self, accumulated_runtime, nr_of_iterations, average):
    """Initializes the class

    :accumulated_runtime: TODO
    :nr_of_iterations: TODO
    :average: TODO

    """
    super().__init__(self)

    self._accumulated_runtime = accumulated_runtime
    self._nr_of_iterations = nr_of_iterations
    self._average = average


class RunConfiguration:

  """This class holds information required for one specific experiment run"""

  def __init__(self, iteration, is_instr_run, db_item_id) -> None:
    """TODO: Implement

    :iteration: The number of the iteration of this invocation
    :is_instr_run: Whether this iteration does instrumentation

    """
    self._iteration = iteration
    self._is_instr_run = is_instr_run
    self._db_item_id = db_item_id


  def get_iteration(self):
    """Returns the current iteration saved in this instance

    :f: TODO
    :returns: TODO
    """
    return self._iteration


  def get_db_item_id(self):
    """Returns the db item id associated with this instance

    :f: TODO
    :returns: TODO

    """
    return self._db_item_id


  def is_instr(self):
    """Returns true iff this instance is meant for instrumentation
    :returns: TODO
    """
    return self._is_instr_run


class ScorepSystemHelper:

  def __init__(self, config: cln.PiraConfiguration) -> None:
    self.known_files = ['.cubex']
    self.config = config
    self.data = {}
    self.cur_mem_size = ''
    self.cur_exp_directory = ''
    self.cur_overwrite_exp_dir = 'False'
    self.cur_base_name = ''
    self.cur_filter_file = ''

  def get_data_elem(self, key: str):
    try:
      if key in self.data.keys():
        return self.data[key]

    except KeyError as ke:
      pass

    log.get_logger().log('Key ' + key + ' was not found in ScorepSystemHelper')
    return ''

  def set_up(self, build, item, flavor, it_nr, is_instr_run) -> None:
    log.get_logger().log('ScorepSystemHelper.set_up: is_instr_run: ' + str(is_instr_run), level='debug')
    if not is_instr_run:
      return

    exp_dir = self.config.get_analyser_exp_dir(build, item)
    log.get_logger().log('Retrieved analyser experiment directory: ' + exp_dir, level='debug')
    effective_dir = u.get_cube_file_path(exp_dir, flavor, it_nr)
    if not u.check_provided_directory(effective_dir):
      log.get_logger().log('Experiment directory does not exist. Creating', level='debug')
      u.create_directory(effective_dir)

    db_exp_dir = u.build_cube_file_path_for_db(exp_dir, flavor, it_nr)
    self.data['cube_dir'] = db_exp_dir
    self.set_scorep_exp_dir(exp_dir, flavor, it_nr)
    self.set_scorep_memory_size('500M')
    self.set_overwrite_scorep_exp_dir()
    self.set_scorep_profiling_basename(flavor, build, item)

  def set_scorep_memory_size(self, mem_str: str) -> None:
    self.cur_mem_size = mem_str
    u.set_env('SCOREP_TOTAL_MEMORY', self.cur_mem_size)

  def set_scorep_profiling_basename(self, flavor: str, base: str, item: str) -> None:
    self.cur_base_name = flavor + '-' + item
    u.set_env('SCOREP_PROFILING_BASE_NAME', self.cur_base_name)

  def set_scorep_exp_dir(self, exp_dir: str, flavor: str, iterationNumber: int) -> None:
    effective_dir = u.get_cube_file_path(exp_dir, flavor, iterationNumber)
    if not u.is_valid_file(effective_dir):
      raise MeasurementSystemException('Score-p experiment directory invalid.')

    self.cur_exp_directory = effective_dir
    u.set_env('SCOREP_EXPERIMENT_DIRECTORY', self.cur_exp_directory)
    return

  def set_overwrite_scorep_exp_dir(self) -> None:
    self.cur_overwrite_exp_dir = 'True'
    u.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY', self.cur_overwrite_exp_dir)

  def set_filter_file(self, file_name:str) -> None:
    if not u.is_valid_file(file_name):
      raise MeasurementSystemException('Score-P filter file not valid.')

    self.cur_filter_file = file_name
    u.set_env('SCOREP_FILTERING_FILE', self.cur_filter_file)
