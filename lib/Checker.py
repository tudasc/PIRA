"""
File: Checker.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Checks if files and paths in config-file are vaild.
"""
import lib.Utility as util
import lib.Configuration as config
import lib.Logging as log

class Checker:

  def check_configfile_v1(configuration):

    error_message ="Error in configuration-file:\n\n"
    exception_occured = False

    for build_dir in configuration.directories:
      if not(util.check_provided_directory(build_dir)):
        error_message += "Build-directory " +build_dir+ " does not exist.\n\n"
        exception_occured = True

      for item in configuration.builds[build_dir]['items']:
        analysis_functor_dir = configuration.items[build_dir][item]['instrument_analysis'][0]

        if not (util.check_provided_directory(analysis_functor_dir)):
          error_message += "Analysis-functor dir " + analysis_functor_dir  + " does not exist.\n"
          exception_occured = True

        analysis_binary_dir = configuration.items[build_dir][item]['instrument_analysis'][2]
        if not (util.check_provided_directory(analysis_binary_dir)):
          error_message += "Analysis-functor dir " + analysis_binary_dir  + " does not exist.\n"
          exception_occured = True

        cubes_dir = configuration.items[build_dir][item]['instrument_analysis'][1]
        if not(util.check_provided_directory(cubes_dir)):
          log.get_logger().log("Creating Cubes-Directory" + cubes_dir , level='info')

        if not(util.check_provided_directory(configuration.items[build_dir][item]["builders"])):
          error_message += "Builders-directory " + configuration.items[build_dir][item]["builders"] + " does not exist.\n"
          exception_occured = True

        for arg in configuration.items[build_dir][item]["args"]:
          if not(util.check_provided_directory(arg)):
            error_message += "args" + arg + "does not exist.\n"
            exception_occured = True

          if not(util.check_provided_directory(configuration.items[build_dir][item]["runner"])):
            error_message += "runner" + configuration.items[build_dir][item]["runner"] + "does not exist.\n"
            exception_occured = True

      if exception_occured:
        raise config.PiraConfigurationErrorException(error_message)

  def check_configfile_v2(configuration):

    if isinstance(configuration, config.PiraConfigurationAdapter):
      configuration = configuration.get_adapted()

    error_message = "Error in configuration-file:\n\n"
    exception_occured = False

    for dir in configuration.get_directories():
      if not (util.check_provided_directory(configuration.get_place(dir))):
        error_message += "Directory " + dir + " does not exist.\n"
        exception_occured = True

      # check if directories exist
      for item in configuration.get_items(dir):
        if not (util.check_provided_directory(item.get_analyzer_dir())):
          error_message += "Analyzer-Directory " + item.get_analyzer_dir() + " does not exist\n"
          exception_occured = True

        # instead of throwing an error, only an info is logged. This is due to that the directory is created in ProfileSink
        if not (util.check_provided_directory(item.get_cubes_dir())):
          log.get_logger().log("Creating Cubes-Directory" + item.get_cubes_dir(), level='info')

        if not (util.check_provided_directory(item.get_functor_base_path())):
          error_message += "Functors-Base-Directory " + item.get_functor_base_path() + " does not exist\n"
          exception_occured = True

        # if there is no flavor,the flavors-array is filled with an empty entry and the underscore in the filename is removed
        if len(item.get_flavors()) == 0 :
          flavors = ['']
          underscore = ''

        else:
          flavors = item.get_flavors()
          underscore = "_"

        # check if functor-files exist
        for flavor in flavors:
          if not (util.is_file(item.get_functor_base_path() + "/analyse_" + item._name + underscore + flavor + ".py")):
            error_message += "analyse-functor of flavor " + flavor + " does not exist" + ".\n"
            exception_occured = True

          if not (util.is_file(item.get_functor_base_path() + "/clean_" + item._name + underscore + flavor + ".py")):
            error_message += "clean-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True

          if not (util.is_file(item.get_functor_base_path() + "/no_instr_" + item._name + underscore + flavor + ".py")):
            error_message += "no_instr-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True

          if not (util.is_file(item.get_functor_base_path() + "/runner_" + item._name + underscore + flavor + ".py")):
            error_message += "runner-functor of flavor " + flavor + " does not exist.\n"
            exception_occured = True

          if not (util.is_file(item.get_functor_base_path() + "/" + item._name + underscore + flavor + ".py")):
            error_message += "plain-functor of flavor " + flavor + " in item " + item._name + " does not exist.\n"
            exception_occured = True


    if exception_occured:
      raise config.PiraConfigurationErrorException(error_message)
