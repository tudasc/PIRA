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
    if(os.path.exists(path)):
        return True
    return False

def rename(old,new):
    os.rename(old,new)

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

def diff_inst_files(file1,file2):
    if(filecmp.cmp(file1,file2)):
        return True
    return False

def set_env(env_var,val):
    os.environ[env_var] = val

def get_absolute_path(path):
    return os.path.abspath(path)

def generate_random_string():
    return ''.join(choice(ascii_uppercase) for i in range(12))

def get_cwd():
    return os.getcwd()


def change_cwd(path):
    log.get_logger().log('cd\'ing to ' + path)
    os.chdir(path)


def load_functor(dir, module):
    append_to_sys_path(dir)
    # Adding 'fromList' argument loads exactly the module.
    functor = __import__(module, fromlist=[''])
    return functor


def shell(command, silent=True, dry=False):
    if dry:
        log.get_logger().log('SHELL CALL: ' + command, level='debug')
        return ''

    try:

        t1 = os.times() # start time
        #out = timeit(stmt = "subprocess.check_output("+command+", shell=True)", number = 1)
        out = subprocess.check_output(command, shell=True)
        t2 = os.times() # end time
        cutime = t2[2]-t1[2]
        cstime = t2[3]-t1[3]
        runTime = cutime+cstime
        print runTime
        return runTime

    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            if command.find('grep '):
                return ''

        log.get_logger().log('Utility.shell: Caught Exception ' + e.message, level='error')
        raise Exception('Running command ' + command + ' did not succeed')


def append_to_sys_path(func_tuple):
    sys.path.append(func_tuple)


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
