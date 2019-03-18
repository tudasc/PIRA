"""
File: ProfileSink.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module hosts different profile sinks. These can process resulting profile files outside of regular PIRA iteration.
"""

import sys
sys.path.append('../')
import lib.Logging as log
import lib.Utility as u
from lib.Configuration import TargetConfiguration, InstrumentConfig
from lib.Exception import PiraException



class ArgumentMapper:
  """
  The first approach towards the implementation of the general mapping problem would be that.
  """
  pass

class SimpleCmdlineArgumentMapper(ArgumentMapper):
  """
  Maps a single parameter from param to commandline argument.
  """
  pass

class SimpleInputFileArgumentMapper(ArgumentMapper):
  """
  Maps a single parameter to a series of input files.
  """
  pass

class CartesianProductCmdlineArgumentMapper(SimpleCmdlineArgumentMapper):
  """
  Does a cartesian product of all the given cmdline arguments.
  Param names and values are given in config file. 
  """
  pass

class UserArgumentMapper(ArgumentMapper):
  """
  Used for complex mappings of arguments to inputs / files.
  
  TODO: How should this be implemented? Ideas:
  1) Loads another functor that does the final mapping.
  2) Config has explicit mapping that is loaded.
  """
  pass


class ProfileSinkException(PiraException):

  def __init__(self, msg):
    super().__init__(msg)


class ProfileSinkBase:

  def __init__(self):
    pass

  def process(self, exp_dir: str, target_config: TargetConfiguration, instr_config: InstrumentConfig):
    log.get_logger().log('ProfileSinkBase::process. ABSTRACT not implemented. Aborting')
    assert (False)


class NopSink(ProfileSinkBase):

  def __init__(self):
    pass

  def process(self, exp_dir, target_conf, instr_config):
    pass


class ExtrapProfileSink(ProfileSinkBase):

  def __init__(self, dir: str, paramname: str, prefix: str, postfix: str, filename: str):
    super().__init__()
    self._base_dir = dir
    self._paramname = paramname
    self._prefix = prefix
    self._postfix = postfix
    self._filename = filename
    self._iteration = -1
    self._repetition = 0
    self._VALUE = 1  # FIXME Implement how to get this data

  def get_extrap_dir_name(self, instr_config: InstrumentConfig) -> str:
    dir_name = self._base_dir + '/' + self._prefix + '.'
    dir_name += self._paramname + str(self._VALUE)
    dir_name += '.' + self._postfix + '.r' + str(self._repetition)
    return dir_name

  def check_and_prepare(self, experiment_dir: str, target_config: TargetConfiguration,
                        instr_config: InstrumentConfig) -> str:
    cur_ep_dir = self.get_extrap_dir_name(instr_config)
    if not u.is_valid_file_name(cur_ep_dir):
      log.get_logger().log(
          'ExtrapProfileSink::check_and_prepare: Generated directory name no good. Abort', level='error')
    else:
      u.create_directory(cur_ep_dir)
      cubex_name = experiment_dir + '/' + target_config.get_flavor() + '-' + target_config.get_target() + '.cubex'
      log.get_logger().log(cubex_name)

      if not u.check_file(cubex_name):
        log.get_logger().log('ExtrapProfileSink::check_and_prepare: Returned experiment cube name is no file [' +
                             cubex_name)
      else:
        return cubex_name

    raise ProfileSinkException('Could not create target directory')

  def do_copy(self, src_cube_name: str, dest_dir: str) -> None:
    log.get_logger().log('ExtrapProfileSink::do_copy: ' + src_cube_name + ' => ' + dest_dir + '/' + self._filename)
    # return  # TODO make this actually work
    u.copy_file(src_cube_name, dest_dir + '/' + self._filename)

  def process(self, exp_dir: str, target_config: TargetConfiguration, instr_config: InstrumentConfig) -> None:
    log.get_logger().log('ExtrapProfileSink::process.')
    if instr_config.get_instrumentation_iteration() > self._iteration:
      self._iteration = instr_config.get_instrumentation_iteration()
      self._repetition = -1
      self._VALUE = 0

    self._repetition += 1
    self._VALUE += 1
    src_cube_name = self.check_and_prepare(exp_dir, target_config, instr_config)

    self.do_copy(src_cube_name, self.get_extrap_dir_name(instr_config))
