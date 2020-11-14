"""
File: DefaultFlags.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module holds a selection of default flags.
"""
import typing
import os

from lib.Configuration import InvocationConfiguration


class BackendDefaults:
  """
  Meant to hold different defaults for, e.g., flags.
  """

  class _BackendDefaultsImpl:

    def __init__(self, invoc_config: InvocationConfiguration):
      self._c_compiler = 'clang'
      self._cpp_compiler = 'clang++'
      self._compiler_instr_flag = '-finstrument-functions'
      self._compiler_instr_wl_flag = '-finstrument-functions-whitelist-inputfile'
      self._num_compile_procs = 8
      self._pira_exe_name = 'pira.built.exe'
      if invoc_config is None: # this check is redundant if we always instantiate BackendDefaults with an InvocationConfiguration
        self.pira = os.path.join(os.path.expanduser('~'), '.pira')
      else:
        self.pira_dir = invoc_config.get_pira_dir()

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
          'CC': '\"' + self.get_default_c_compiler_name() + '\"',
          'CXX': '\"' + self.get_default_cpp_compiler_name() + '\"',
          'PIRANAME': self.get_default_exe_name(),
          'NUMPROCS': self._num_compile_procs
      }
      return kwargs

    def get_pira_dir(self) -> str:
      return self.pira_dir

    def get_wrap_w_file(self) -> str:
      return os.path.join(self.pira_dir, 'pira-mpi-filter.w')

    def get_wrap_c_file(self) -> str:
      return os.path.join(self.pira_dir, 'pira-mpi-filter.c')

    def get_wrap_so_file(self) -> str:
      return os.path.join(self.pira_dir, 'PIRA_MPI_Filter.so')

    def get_MPI_wrap_LD_PRELOAD(self) -> str:
      return 'LD_PRELOAD=' + self.get_wrap_so_file()


  instance = None

  def __init__(self, invoc_config: InvocationConfiguration = None):
    if not BackendDefaults.instance:
      BackendDefaults.instance = BackendDefaults._BackendDefaultsImpl(invoc_config)

  def __getattr__(self, name):
    return getattr(self.instance, name)
