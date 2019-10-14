"""
File: DefaultFlags.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module holds a selection of default flags.
"""
import typing


class BackendDefaults:
  """
  Meant to hold different defaults for, e.g., flags.
  """

  class _BackendDefaultsImpl:

    def __init__(self):
      self._c_compiler = 'clang'
      self._cpp_compiler = 'clang++'
      self._compiler_instr_flag = '-finstrument-functions'
      self._compiler_instr_wl_flag = '-finstrument-functions-whitelist-inputfile'
      self._num_compile_procs = 8
      self._pira_exe_name = 'pira.built.exe'

    def get_default_c_compiler_name(self) -> str:
      return self._c_compiler

    def get_default_cpp_compiler_name(self) -> str:
      return self._cpp_compiler

    def get_default_instrumentation_flag(self) -> str:
      return self._compiler_instr_flag

    def get_default_instrumentation_selection_flag(self) -> str:
      return self._compiler_instr_wl_flag

    def get_default_number_of_processes(self) -> int:
      return self._num_compile_procs

    def get_default_exe_name(self) -> str:
      return self._pira_exe_name

    def get_default_kwargs(self) -> dict:
      kwargs = {
          'CC': self.get_default_c_compiler_name(),
          'CXX': self.get_default_cpp_compiler_name(),
          'PIRANAME': self.get_default_exe_name(),
          'NUMPROCS': self._num_compile_procs
      }
      return kwargs

  instance = None

  def __init__(self):
    if not BackendDefaults.instance:
      BackendDefaults.instance = BackendDefaults._BackendDefaultsImpl()

  def __getattr__(self, name):
    return getattr(self.instance, name)
