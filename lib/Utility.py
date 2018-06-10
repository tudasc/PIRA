import sys
import os
import subprocess
import Logging as log
import filecmp
import Utility as util
from random import choice
from string import ascii_uppercase
from timeit import timeit
import shutil

queued_job_filename = './queued_job.tmp'


def read_file(file_name):
  f = file(file_name)
  content = f.read()
  f.close()
  return content


def check_provided_directory(path):
  if os.path.isdir(path):
    return True

  return False


def check_file(path):
  if os.path.exists(path):
    return True
  return False


def rename(old, new):
  os.rename(old, new)


def remove(path):
  for root, dirs, files in os.walk(path):
    for f in files:
      os.unlink(os.path.join(root, f))
    for d in dirs:
      shutil.rmtree(os.path.join(root, d))


def append_scorep_footer(filename):
  with open(filename, "a") as myfile:
    myfile.write("SCOREP_REGION_NAMES_END")


def append_scorep_header(filename):
  line = "SCOREP_REGION_NAMES_BEGIN\nEXCLUDE *\nINCLUDE"
  with open(filename, 'r+') as myfile:
    content = myfile.read()
    myfile.seek(0, 0)
    myfile.write(line.rstrip('\r\n') + '\n' + content)


def diff_inst_files(file1, file2):
  if (filecmp.cmp(file1, file2)):
    return True
  return False


def set_env(env_var, val):
  log.get_logger().log('Setting ' + env_var + ' to ' + str(val), level='debug')
  os.environ[env_var] = val


def get_absolute_path(path):
  return os.path.abspath(path)


def generate_random_string():
  return ''.join(choice(ascii_uppercase) for i in range(12))


def get_cwd():
  return os.getcwd()


def change_cwd(path):
  log.get_logger().log('cd\'ing to ' + path, level='debug')
  os.chdir(path)


def load_functor(directory, module):
  log.get_logger().log('Appending ' + directory + ' to system path.', level='debug')
  append_to_sys_path(directory)
  # Adding 'fromList' argument loads exactly the module.
  functor = __import__(module)
  remove_from_sys_path(directory)
  return functor


def unload_functo(functor, module):
  del functor
  sys.modules.pop(module)


def shell(command, silent=True, dry=False):
  if dry:
    log.get_logger().log('DRY RUN SHELL CALL: ' + command, level='debug')
    return ''

  try:
    t1 = os.times()  # start time
    out = subprocess.check_output(command, shell=True)
    t2 = os.times()  # end time
    cutime = t2[2] - t1[2]
    cstime = t2[3] - t1[3]
    runTime = cutime + cstime
    return runTime

  except subprocess.CalledProcessError as e:
    if e.returncode == 1:
      if command.find('grep '):
        return ''

    log.get_logger().log('Utility.shell: Caught Exception ' + e.output, level='error')
    raise Exception('Running command ' + command + ' did not succeed')


def shell_for_submitter(command, silent=True, dry=False):
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

    log.get_logger().log('Utility.shell: Caught Exception ' + e.message, level='error')
    raise Exception('Running command ' + command + ' did not succeed')


def append_to_sys_path(func_tuple):
  sys.path.append(func_tuple)


def remove_from_sys_path(func_tuple):
  sys.path.remove(func_tuple)


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


def remove_from_pgoe_out_dir(directory):
  util.remove(directory + "/" + "out")


def build_runner_functor_filename(IsForDB, benchmark_name, flavor):
  if IsForDB:
    return '/runner_' + benchmark_name + flavor
  else:
    return 'runner_' + benchmark_name + '_' + flavor


def build_builder_functor_filename(IsForDB, IsNoInstr, benchmark_name, flavor):
  if IsForDB:
    return '/' + benchmark_name + flavor
  else:
    if IsNoInstr:
      return 'no_instr_' + benchmark_name + '_' + flavor
    else:
      return benchmark_name + '_' + flavor


def build_clean_functor_filename(benchmark_name, flavor):
  return 'clean_' + benchmark_name + '_' + flavor


def build_analyse_functor_filename(IsForDB, benchmark_name, flavor):
  if IsForDB:
    return '/analyse_' + benchmark_name + flavor
  else:
    return 'analyse_' + benchmark_name + '_' + flavor


def build_instr_file_path(analyser_dir, flavor, benchmark_name):
  return analyser_dir + "/" + 'out/instrumented-' + flavor + '-' + benchmark_name + '.txt'


def build_previous_instr_file_path(analyser_dir, flavor, benchmark_name):
  return analyser_dir + "/" + 'out/instrumented-' + flavor + '-' + benchmark_name + 'previous.txt'


def run_analyser_command(command, analyser_dir, flavor, benchmark_name, exp_dir, iterationNumber):
  sh_cmd = command + ' ' + analyser_dir + "/" + flavor + '-' + benchmark_name + '.ipcg ' + exp_dir + '-' + flavor + '-' + str(
      iterationNumber) + '/' + flavor + '-' + benchmark_name + '.cubex'
  log.get_logger().log('  INSTR: Run cmd: ' + sh_cmd)
  util.shell(sh_cmd)


def run_analyser_command_noInstr(command, analyser_dir, flavor, benchmark_name):
  sh_cmd = command + ' ' + analyser_dir + "/" + flavor + '-' + benchmark_name + '.ipcg '
  log.get_logger().log('  NO INSTR: Run cmd: ' + sh_cmd)
  util.shell(sh_cmd)


def get_cube_file_path(experiment_dir, flavor, iter_nr, is_no_instr):
  if is_no_instr:
    return experiment_dir + '-' + flavor + '-' + str(iter_nr) + 'noInstrRun'

  return experiment_dir + '-' + flavor + '-' + str(iter_nr)


def build_cube_file_path_for_db(exp_dir, flavor, iterationNumber, isNoInstr):
  return get_cube_file_path(exp_dir, flavor, iterationNumber, isNoInstr)


def set_scorep_exp_dir(exp_dir, flavor, iterationNumber, isNoInstr):
  effective_dir = get_cube_file_path(exp_dir, flavor, iterationNumber, isNoInstr)
  util.set_env('SCOREP_EXPERIMENT_DIRECTORY', effective_dir)
  return


def set_overwrite_scorep_exp_dir():
  util.set_env('SCOREP_OVERWRITE_EXPERIMENT_DIRECTORY', 'True')


def set_scorep_profiling_basename(flavor, benchmark_name):
  util.set_env('SCOREP_PROFILING_BASE_NAME', flavor + '-' + benchmark_name)
