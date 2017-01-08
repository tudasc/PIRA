import sys


def read_file(file_name):
    f = file(file_name)
    content = f.read()
    f.close()
    return content


def check_provided_directory(path):
    # TODO Implement me
    pass


def change_cwd(path):
    # TODO Implement me
    pass


def load_functor(func_tuple):
    append_to_sys_path(func_tuple)
    # Adding fromList argument loads exactly the module.
    functor = __import__(func_tuple[1], fromlist=[''])
    return functor


def append_to_sys_path(func_tuple):
    sys.path.append(func_tuple[0])
