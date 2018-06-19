import sys
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


def read_file(file_name: str) -> str:
  with open(file_name) as f:
    content = f.read()

  return content


def check_provided_directory(path: str) -> bool:
  if os.path.isdir(path):
    return True

  return False


def check_file(path: str) -> bool:
  if os.path.exists(path):
    return True
  return False


def is_valid_file(file_name: str) -> bool:
  import re
  search = re.compile(r'[^a-zA-z0-9/_-]').search
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


def append_scorep_footer(filename: str) -> None:
  with open(filename, "a") as myfile:
    myfile.write("SCOREP_REGION_NAMES_END")


def append_scorep_header(filename: str) -> None:
  line = "SCOREP_REGION_NAMES_BEGIN\nEXCLUDE *\nINCLUDE"
  with open(filename, 'r+') as myfile:
    content = myfile.read()
    myfile.seek(0, 0)
    myfile.write(line.rstrip('\r\n') + '\n' + content)


def diff_inst_files(file1: str, file2: str) -> bool:
  if (filecmp.cmp(file1, file2)):
    return True
  return False


def set_env(env_var: str, val) -> None:
  log.get_logger().log('Setting ' + env_var + ' to ' + str(val), level='debug')
  os.environ[env_var] = val


def get_absolute_path(path: str) -> str:
  return os.path.abspath(path)


def generate_random_string() -> str:
  return ''.join(choice(ascii_uppercase) for i in range(12))


def get_cwd() -> str:
  return os.getcwd()


def change_cwd(path: str) -> None:
  log.get_logger().log('util.change_cwd to ' + path, level='debug')
  os.chdir(path)


def load_functor(directory: str, module: str):
  if not check_provided_directory(directory):
    log.get_logger().log('Functor directory invalid', level='warn')
  if not check_file(directory + '/' + module):
    log.get_logger().log('Functor filename invalid', level='warn')

  # TODO: Add error if functor path does not exist!!!
  log.get_logger().log('Appending ' + directory + ' to system path.', level='debug')
  append_to_sys_path(directory)
  # Adding 'fromList' argument loads exactly the module.
  functor = __import__(module)
  remove_from_sys_path(directory)
  log.get_logger().log('Returning from load_functor', level='debug')
  return functor


def timed_invocation(command: str, stderr_fd) -> typing.Tuple[str, float]:
  t1 = os.times()  # start time
  out = subprocess.check_output(command, stderr=stderr_fd, shell=True)
  t2 = os.times()  # end time
  cutime = t2[2] - t1[2]
  cstime = t2[3] - t1[3]
  runtime = cutime + cstime
  return out, runtime


def shell(command: str, silent: bool = True, dry: bool = False,
          time_invoc: bool = False) -> typing.Tuple[str, float]:
  if dry:
    log.get_logger().log('DRY RUN SHELL CALL: ' + command, level='debug')
    return '', -1.0

  try:
    stderr_fn = '/tmp/stderr-bp-' + generate_random_string()
    stderr_fd = open(stderr_fn, 'w')
    log.get_logger().log('util executing: ' + str(command), level='debug')

    if time_invoc:
      out, rt = timed_invocation(command, stderr_fd)
      return str(out.decode('utf-8')), rt

    else:
      out = subprocess.check_output(command, stderr=stderr_fd, shell=True)
      return str(out.decode('utf-8')), -1.0

  except subprocess.CalledProcessError as e:
    if e.returncode == 1:
      if command.find('grep '):
        return '', .0

    log.get_logger().log('Utility.shell: Caught Exception ' + str(e), level='error')
    raise Exception('Running command ' + command + ' did not succeed')

  finally:
    stderr_fd.close()
    remove_file(stderr_fn)
    log.get_logger().log('Cleaning up temp files for subprocess communication.', level='debug')


def shell_for_submitter(command: str, silent: bool = True, dry: bool = False):
  if dry:
    log.get_logger().log('SHELL CALL: ' + command, level='debug')
    return ''

  try:
    out = subprocess.check_output(command, shell=True)
    return out

  except subprocess.CalledProcessError as e:
    if e.returncode == 1:
      if command.find('grep '):
        return ''

    log.get_logger().log('Utility.shell: Caught Exception ' + str(e), level='error')
    raise Exception('Running command ' + command + ' did not succeed')


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

  if isinstance(json_elem, str):
    new_str = str(json_elem)
    return new_str

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
                         iterationNumber: int) -> None:
  ipcg_file = get_ipcg_file_name(analyser_dir, benchmark_name, flavor)
  cubex_dir = get_cube_file_path(exp_dir, flavor, iterationNumber)
  cubex_file = cubex_dir + '/' + flavor + '-' + benchmark_name + '.cubex'

  sh_cmd = command + ' ' + ipcg_file + ' ' + cubex_file
  log.get_logger().log('  INSTR: Run cmd: ' + sh_cmd)
  shell(sh_cmd)


def run_analyser_command_noInstr(command: str, analyser_dir: str, flavor: str, benchmark_name: str) -> None:
  ipcg_file = get_ipcg_file_name(analyser_dir, benchmark_name, flavor)
  sh_cmd = command + ' ' + ipcg_file
  log.get_logger().log('  NO INSTR: Run cmd: ' + sh_cmd)
  shell(sh_cmd)


def get_cube_file_path(experiment_dir: str, flavor: str, iter_nr: int) -> str:
  return experiment_dir + '-' + flavor + '-' + str(iter_nr)


def build_cube_file_path_for_db(exp_dir: str, flavor: str, iterationNumber: int) -> str:
  fp = get_cube_file_path(exp_dir, flavor, iterationNumber)
  if is_valid_file(fp):
    return fp

  raise Exception('Built file path to Cube not valid. fp: ' + fp)

