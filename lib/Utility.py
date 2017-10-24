import sys
import os
import subprocess
import Logging as log
import Utility as util


def read_file(file_name):
    f = file(file_name)
    content = f.read()
    f.close()
    return content


def check_provided_directory(path):
    if os.path.isdir(path):
        return True

    return False


def get_absolute_path(path):
    return os.path.abspath(path)


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
