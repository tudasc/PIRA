"""
File: ProfileSink.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module hosts different profile sinks. These can process resulting profile files outside of regular PIRA iteration.
"""

import sys
sys.path.append('../')

import lib.Logging as L
import lib.Utility as U
from lib.Configuration import TargetConfig, InstrumentConfig, InvocationConfig
from lib.Exception import PiraException

import json


class FolderRenamer:

  class __FolderRenamerImpl:
    def __init__(self) -> None:
      self.currentStr = U.generate_random_string()

    def get_renamed_folder(self, old_folder: str) -> str:
      return old_folder + '_' + self.currentStr

  instance = None

  def __init__(self):
    if not FolderRenamer.instance:
      FolderRenamer.instance = FolderRenamer.__FolderRenamerImpl()

  def __getattr__(self, name):
    return getattr(self.instance, name)


class ProfileSinkException(PiraException):

  def __init__(self, msg):
    super().__init__(msg)


class ProfileSinkBase:

  def __init__(self):
    self._sink_target = ''

  def process(self, exp_dir: str, target_config: TargetConfig, instr_config: InstrumentConfig):
    L.get_logger().log('ProfileSinkBase::process. ABSTRACT not implemented. Aborting')
    raise RuntimeError('ProfileSinkBase::process. ABSTRACT not implemented. Aborting')

  def get_target(self):
    return self._sink_target

  def has_config_output(self):
    return False


class NopSink(ProfileSinkBase):
  '''
  NopSink: To be used whenever a sink is required as an argument, but not needed for functionality
  '''
  def __init__(self):
    super().__init__()

  def process(self, exp_dir, target_conf, instr_config):
    self._sink_target = exp_dir

  def has_config_output(self):
    return False


class PiraOneProfileSink(ProfileSinkBase):
  '''
  PiraOneProfileSink: To be used in PIRA version 1 mode.
  '''
  def __init__(self):
    super().__init__()

  def process(self, exp_dir, target_conf, instr_config):
    self._sink_target = exp_dir

  def output_config(self, benchmark, analyzer_dir):
    return None

  def has_config_output(self):
    return False


class ExtrapProfileSink(ProfileSinkBase):

  def __init__(self, dir: str, params, prefix: str, postfix: str, filename: str):
    super().__init__()
    self._base_dir = dir
    self._params = params
    self._prefix = prefix
    self._postfix = postfix
    self._filename = filename
    self._iteration = -1
    self._repetition = 0
    self._total_reps = InvocationConfig.get_instance().get_num_repetitions()
    self._VALUE = ()

  def has_config_output(self):
    return True

  def output_config(self, benchmark, output_dir):
    L.get_logger().log('ExtrapProfileSink::output_config:\ndir: ' + self._base_dir + '\nprefix: ' +
                         self._prefix + '\npostfix: ' + self._postfix + '\nreps: ' + str(self._total_reps) +
                         '\nNiter: ' + str(self._iteration + 1))
    s = ''
    for p in self._params:
      s += p + ', '
    L.get_logger().log('params: ' + s)

    json_str = json.dumps({
        'dir': self._base_dir,
        'prefix': self._prefix,
        'postfix': self._postfix,
        'reps': int(self._total_reps),
        'iter': int(self._iteration + 1),
        'params': self._params
    })

    out_file_final = output_dir + '/pgis_cfg_' + benchmark + '.json'
    U.write_file(out_file_final, json_str)
    return out_file_final

  def get_target(self):
    return self._sink_target

  def get_param_mapping(self, target_config: TargetConfig) -> str:
    if not target_config.has_args_for_invocation():
      return '.'

    args = target_config.get_args_for_invocation()
    param_str = ''
    # TODO FIX ME!
    if isinstance(args, list):
      L.get_logger().log('ExtrapProfileSink::get_param_mapping: isinstance of list')
      param_str = str(args[1]) + str(args[2]) + '.' + str(args[4]) + str(args[0])

    elif not isinstance(args, tuple):
      L.get_logger().log('ExtrapProfileSink::get_param_mapping: not isinstance of tuple')
      param_str = str(args)  # PiraArgument knows how to unparse to string

    else:
      for v in args:
        param_str += v

    L.get_logger().log('ExtrapProfileSink::get_param_mapping: ' + param_str)
    return param_str

  def get_extrap_dir_name(self, target_config: TargetConfig, instr_iteration: int) -> str:
    dir_name = self._base_dir + '/' + 'i' + str(instr_iteration) + '/' + self._prefix + '.'
    dir_name += self.get_param_mapping(target_config)
    dir_name += '.' + self._postfix + '.r' + str(self._repetition + 1)
    return dir_name

  def check_and_prepare(self, experiment_dir: str, target_config: TargetConfig,
                        instr_config: InstrumentConfig) -> str:
    cur_ep_dir = self.get_extrap_dir_name(target_config, instr_config.get_instrumentation_iteration())
    if not U.is_valid_file_name(cur_ep_dir):
      L.get_logger().log(
          'ExtrapProfileSink::check_and_prepare: Generated directory name no good. Abort\n' + cur_ep_dir, level='error')
    else:
      if U.check_provided_directory(cur_ep_dir):
        renamer = FolderRenamer()
        #new_dir_name = cur_ep_dir + '_' + U.generate_random_string()
        new_dir_name = renamer.get_renamed_folder(cur_ep_dir)
        L.get_logger().log('ExtrapProfileSink::check_and_prepare: Moving old experiment directory (' + cur_ep_dir + ') to: ' + new_dir_name, level='info')
        U.rename(cur_ep_dir, new_dir_name)

      U.create_directory(cur_ep_dir)
      cubex_name = U.get_cubex_file(experiment_dir, target_config.get_target(), target_config.get_flavor())      
      L.get_logger().log(cubex_name)

      if not U.is_file(cubex_name):
        L.get_logger().log('ExtrapProfileSink::check_and_prepare: Returned experiment cube name is no file: ' +
                             cubex_name)
      else:
        return cubex_name

    raise ProfileSinkException('ExtrapProfileSink: Could not create target directory or Cube dir bad.')

  def do_copy(self, src_cube_name: str, dest_dir: str) -> None:
    L.get_logger().log('ExtrapProfileSink::do_copy: ' + src_cube_name + ' => ' + dest_dir + '/' + self._filename)
    # return  # TODO make this actually work
    U.copy_file(src_cube_name, dest_dir + '/' + self._filename)

  def process(self, exp_dir: str, target_config: TargetConfig, instr_config: InstrumentConfig) -> None:
    L.get_logger().log('ExtrapProfileSink::process: ' + str(instr_config.get_instrumentation_iteration()))
    if instr_config.get_instrumentation_iteration() > self._iteration or target_config.get_args_for_invocation(
    ) is not self._VALUE:
      self._iteration = instr_config.get_instrumentation_iteration()
      self._repetition = -1
      self._VALUE = ()

    self._repetition += 1
    self._VALUE = target_config.get_args_for_invocation()
    src_cube_name = self.check_and_prepare(exp_dir, target_config, instr_config)
    self._sink_target = self.get_extrap_dir_name(target_config, self._iteration)

    self.do_copy(src_cube_name, self._sink_target)
