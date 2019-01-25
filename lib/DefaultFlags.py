"""
File: DefaultFlags.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module holds a selection of default flags.
"""
import typing


def get_default_c_compiler_name() -> str:
    return 'clang'

def get_default_cpp_compiler_name() -> str:
    return 'clang++'

def get_default_instrumentation_flag() -> str:
    return '-finstrument-functions'

def get_default_instrumentation_selection_flag() -> str:
    return '-finstrument-functions-whitelist-inputile'

def get_default_number_of_processes() -> int:
    return 8