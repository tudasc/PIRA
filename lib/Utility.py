"""
File: Utility.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to support other tasks.
"""

import sys
sys.path.append('..')
from lib.Exception import PiraException
import os
import subprocess
import lib.Logging as log
import filecmp
from random import choice
from string import ascii_uppercase
from timeit import timeit
import shutil

import typing

queued_job_filename = './queued_job.tmp'
home_directory = ''


def set_home_dir(home_dir: str) -> None:
  global home_directory
  home_directory = home_dir


def get_home_dir() -> str:
  if home_directory == '':
    raise PiraException('Utility::get_home_dir: No Home Directory Set!')

  return home_directory


def read_file(file_name: str) -> str:
  with open(file_name) as f:
    content = f.read()

  return content


def copy_file(source_file: str, target_file: str) -> None:
  log.get_logger().log('Utility::copy_file: ' + source_file + ' -to- ' + target_file)
  shutil.copyfile(source_file, target_file)


def lines_in_file(file_name: str) -> int:
  if check_file(file_name):
    content = read_file(file_name)
    lines = len(content.split('\n'))
    return lines

  log.get_logger().log('Utility::lines_in_file: No file ' + file_name + ' to read. Return 0 lines', level='debug')
  return 0


def check_provided_directory(path: str) -> bool:
  if os.path.isdir(path):
    return True

  return False


def create_directory(path: str) -> None:
  os.makedirs(path)


def write_file(file_path: str, file_content: str) -> str:
  log.get_logger().log('Utility::write_file: file_path to write: ' + file_path)
  with open(file_path, 'w+') as out_file:
    out_file.write(file_content)


def get_base_dir(file_path: str) -> str:
  return os.path.dirname(file_path)


def check_file(path: str) -> bool:
  if os.path.exists(path):
    return True
  return False


def is_valid_file_name(file_name: str) -> bool:
  import re
  search = re.compile(r'[^a-zA-z0-9/\._-]').search
  return not bool(search(file_name))


def rename(old: str, new: str) -> None:
  os.rename(old, new)


def remove(path: str) -> None:
  for root, dirs, files in os.walk(path):
    for f in files:
      os.unlink(os.path.join(root, f))
    for d in dirs:
      shutil.rmtree(os.path.join(root, d))


def remove_file(path: str) -> bool:
  if check_file(path):
    os.remove(path)
    return True
  return False


def diff_inst_files(file1: str, file2: str) -> bool:
  if (filecmp.cmp(file1, file2)):
    return True
  return False


def set_env(env_var: str, val) -> None:
  log.get_logger().log('Utility::set_env: Setting ' + env_var + ' to ' + str(val), level='debug')
  os.environ[env_var] = val


def get_absolute_path(path: str) -> str:
  return os.path.abspath(path)


def generate_random_string() -> str:
  return ''.join(choice(ascii_uppercase) for i in range(12))


def get_cwd() -> str:
  return os.getcwd()


def change_cwd(path: str) -> None:
  log.get_logger().log('Utility::change_cwd: to ' + path, level='debug')
  os.chdir(path)


def load_functor(directory: str, module: str):
  if not check_provided_directory(directory):
    log.get_logger().log('Utility::load_functor: Functor directory invalid', level='warn')
  if not is_valid_file_name(directory + '/' + module):
    log.get_logger().log('Utility::load_functor: Functor filename invalid', level='warn')

  # TODO: Add error if functor path does not exist!!!
  log.get_logger().log('Utility::load_functor: Appending ' + directory + ' to system path.', level='debug')
  append_to_sys_path(directory)
  # Adding 'fromList' argument loads exactly the module.
  functor = __import__(module)
  remove_from_sys_path(directory)
  log.get_logger().log('Utility::load_functor: Returning from load_functor', level='debug')
  return functor


def timed_invocation(command: str, stderr_fd) -> typing.Tuple[str, float]:
  t1 = os.times()  # start time
  out = subprocess.check_output(command, stderr=stderr_fd, shell=True)
  t2 = os.times()  # end time
  cutime = t2[2] - t1[2]
  cstime = t2[3] - t1[3]
  elapsed = t2[4] - t1[4]
  # FIXME: How to actually compute this? Make it configurable?
  # Problem is: util.shell('sleep 4s') returns cutime + cstime == 0
  runtime = cutime + cstime
  runtime = elapsed
  return out, runtime


def shell(command: str, silent: bool = True, dry: bool = False, time_invoc: bool = False) -> typing.Tuple[str, float]:
  if dry:
    log.get_logger().log('Utility::shell: DRY RUN SHELL CALL: ' + command, level='debug')
    return '', 1.0

  stderr_fn = '/tmp/stderr-bp-' + generate_random_string()
  stderr_fd = open(stderr_fn, 'w+')
  try:
    log.get_logger().log('Utility::shell: util executing: ' + str(command), level='debug')

    if time_invoc:
      out, rt = timed_invocation(command, stderr_fd)
      log.get_logger().log('Util::shell: timed_invocation took: ' + str(rt), level='debug')
      return str(out.decode('utf-8')), rt

    else:
      out = subprocess.check_output(command, stderr=stderr_fd, shell=True)
      return str(out.decode('utf-8')), -1.0

  except subprocess.CalledProcessError as e:
    if e.returncode == 1:
      if command.find('grep '):
        return '', .0

    err_out = ''
    log.get_logger().log('Utility::shell: Attempt to write stderr file', level='debug')
    err_out += stderr_fd.read()

    log.get_logger().log('Utility::shell: Error output: ' + str(err_out), level='debug')
    log.get_logger().log('Utility::shell: Caught Exception ' + str(e), level='error')
    raise Exception('Utility::shell: Running command ' + command + ' did not succeed')

  finally:
    stderr_fd.close()
    remove_file(stderr_fn)
    log.get_logger().log('Utility::shell Cleaning up temp files for subprocess communication.', level='debug')


def shell_for_submitter(command: str, silent: bool = True, dry: bool = False):
  if dry:
    log.get_logger().log('Utility::shell_for_submitter: SHELL CALL: ' + command, level='debug')
    return ''

  try:
    out = subprocess.check_output(command, shell=True)
    return out

  except subprocess.CalledProcessError as e:
    if e.returncode == 1:
      if command.find('grep '):
        return ''

    log.get_logger().log('Utility.shell: Caught Exception ' + str(e), level='error')
    raise Exception('Utility::shell_for_submitter: Running command ' + command + ' did not succeed')


def append_to_sys_path(path: str) -> None:
  sys.path.append(path)


def remove_from_sys_path(path: str) -> None:
  sys.path.remove(path)


def json_to_canonic(json_elem):
  if isinstance(json_elem, list):
    new_list = []
    for entry in json_elem:
      new_list.append(json_to_canonic(entry))
    return new_list

  elif isinstance(json_elem, str):
    new_str = str(json_elem)
    return new_str

  elif isinstance(json_elem, dict):
    new_dict = {}
    for k in json_elem:
      key_v = json_to_canonic(k)
      new_dict[key_v] = json_to_canonic(json_elem[key_v])
    return new_dict

  else:
    return str(json_elem)


def remove_from_pgoe_out_dir(directory: str) -> None:
  remove(directory + "/" + "out")


def concat_a_b_with_sep(a: str, b: str, sep: str) -> str:
  return a + sep + b


def build_runner_functor_filename(IsForDB: bool, benchmark_name: str, flavor: str) -> str:
  if IsForDB:
    return '/runner_' + concat_a_b_with_sep(benchmark_name, flavor, '')
  else:
    return 'runner_' + concat_a_b_with_sep(benchmark_name, flavor, '_')


def build_builder_functor_filename(IsForDB: bool, IsNoInstr: bool, benchmark_name: str, flavor: str) -> str:
  if IsForDB:
    return '/' + concat_a_b_with_sep(benchmark_name, flavor, '')
  else:
    if IsNoInstr:
      return 'no_instr_' + concat_a_b_with_sep(benchmark_name, flavor, '_')
    else:
      return concat_a_b_with_sep(benchmark_name, flavor, '_')


def build_clean_functor_filename(benchmark_name: str, flavor: str) -> str:
  return 'clean_' + concat_a_b_with_sep(benchmark_name, flavor, '_')


def build_analyse_functor_filename(IsForDB: bool, benchmark_name: str, flavor: str) -> str:
  if IsForDB:
    return '/analyse_' + concat_a_b_with_sep(benchmark_name, flavor, '')
  else:
    return 'analyse_' + concat_a_b_with_sep(benchmark_name, flavor, '_')


def build_instr_file_path(analyser_dir: str, flavor: str, benchmark_name: str) -> str:
  return analyser_dir + "/" + 'out/instrumented-' + flavor + '-' + benchmark_name + '.txt'


def build_previous_instr_file_path(analyser_dir: str, flavor: str, benchmark_name: str) -> str:
  return analyser_dir + "/" + 'out/instrumented-' + flavor + '-' + benchmark_name + 'previous.txt'


def get_ipcg_file_name(base_dir: str, b_name: str, flavor: str) -> str:
  return base_dir + "/" + flavor + '-' + b_name + '.ipcg'


def run_analyser_command(command: str, analyser_dir: str, flavor: str, benchmark_name: str, exp_dir: str,
                         iterationNumber: int, pgis_cfg_file: str) -> None:
  ipcg_file = get_ipcg_file_name(analyser_dir, benchmark_name, flavor)
  cubex_dir = get_cube_file_path(exp_dir, flavor, iterationNumber - 1)
  cubex_file = cubex_dir + '/' + flavor + '-' + benchmark_name + '.cubex'

  #sh_cmd = command + ' ' + ipcg_file + ' ' + cubex_file
  #log.get_logger().log('Utility::run_analyser_command: INSTR: Run cmd: ' + sh_cmd)
  #log.get_logger().log(
  #    '\nTHIS IS THE OLD VERSION OF PIRA/PGIS!!! WE NEED TO PASS -c IN FRONT OF CUBE FILE!!!!\n', level='warn')
  #out, _ = shell(sh_cmd)
  #log.get_logger().log('Utility::run_analyser_command: Output of analyzer:\n' + out, level='debug')

  extrap_cfg_file = pgis_cfg_file
  # extrap_file_path = analyser_dir + '/' + extrap_cfg_file
  # sh_cmd = command + ' --model-filter -e ' + extrap_file_path + ' ' + ipcg_file
  sh_cmd = command + ' -e ' + pgis_cfg_file + ' ' + ipcg_file
  log.get_logger().log('Utility::run_analyser_command: INSTR: Run cmd: ' + sh_cmd)
  out, _ = shell(sh_cmd)
  log.get_logger().log('Utility::run_analyser_command: Output of analyzer:\n' + out, level='debug')



def run_analyser_command_noInstr(command: str, analyser_dir: str, flavor: str, benchmark_name: str) -> None:
  ipcg_file = get_ipcg_file_name(analyser_dir, benchmark_name, flavor)
  sh_cmd = command + ' --static ' + ipcg_file
  log.get_logger().log('Utility::run_analyser_command_noInstr: NO INSTR: Run cmd: ' + sh_cmd)
  out, _ = shell(sh_cmd)
  log.get_logger().log('Utility::run_analyser_command_noInstr: Output of analyzer:\n' + out, level='debug')


def get_cube_file_path(experiment_dir: str, flavor: str, iter_nr: int) -> str:
  log.get_logger().log('Utility::get_cube_file_path: ' + experiment_dir + '-' + flavor + '-' + str(iter_nr))
  return experiment_dir + '-' + flavor + '-' + str(iter_nr)


def build_cube_file_path_for_db(exp_dir: str, flavor: str, iterationNumber: int) -> str:
  fp = get_cube_file_path(exp_dir, flavor, iterationNumber)
  if is_valid_file_name(fp):
    return fp

  raise Exception('Utility::build_cube_file_path_for_db: Built file path to Cube not valid. fp: ' + fp)
