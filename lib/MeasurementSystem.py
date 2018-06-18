import lib.Utility as u
import lib.Logging as log
import lib.ConfigLoaderNew as cln

import typing



class ScorepSystemHelper:
  def __init__(self, config: cln.ConfigurationNew) -> None:
    self.known_files = ['.cubex']
    self.config = config
    self.data = {}

  def get_data_elem(self, key:str):
    if key in self.data:
      return self.data[key]

    log.get_logger().log('Key ' + key + ' was not found in ScorepSystemHelper')
    raise KeyError()

  def set_up(self, build, item, flavor, it_nr, is_instr_run) -> None:
    exp_dir = self.config.get_analyser_exp_dir(build, item)
    log.get_logger().log('Retrieved analyser experiment directory: ' + exp_dir, level='debug')
    
    db_exp_dir = u.build_cube_file_path_for_db(exp_dir, flavor, it_nr)
    self.data['cube_dir'] = db_exp_dir
    u.set_scorep_exp_dir(exp_dir, flavor, it_nr)
    u.set_overwrite_scorep_exp_dir()
    if is_instr_run:
      u.set_scorep_profiling_basename(flavor, self.config.get_benchmark_name(build))

