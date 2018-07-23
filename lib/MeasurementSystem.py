import lib.Utility as u
import lib.Logging as log
import lib.ConfigLoaderNew as cln

import typing


class ScorepSystemHelper:

  def __init__(self, config: cln.ConfigurationNew) -> None:
    self.known_files = ['.cubex']
    self.config = config
    self.data = {}

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
    self.set_overwrite_scorep_exp_dir()
    if is_instr_run:
      self.set_scorep_profiling_basename(flavor, build, item)

  def set_scorep_profiling_basename(self, flavor: str, base: str, item: str) -> None:
    u.set_env('SCOREP_PROFILING_BASE_NAME', flavor + '-' + item)

  def set_scorep_exp_dir(self, exp_dir: str, flavor: str, iterationNumber: int) -> None:
    effective_dir = u.get_cube_file_path(exp_dir, flavor, iterationNumber)
    if not u.is_valid_file(effective_dir):
      raise Exception('Score-p experiment directory invalid.')

    u.set_env('SCOREP_EXPERIMENT_DIRECTORY', effective_dir)
    return

  def set_overwrite_scorep_exp_dir(self) -> None:
    u.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY', 'True')

  def set_filter_file(self, file_name:str) -> None:
    if not u.is_valid_file(file_name):
      raise RuntimeError('Score-P filter file not valid.')

    u.set_env('SCOREP_FILTERING_FILE', file_name)
