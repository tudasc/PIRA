"""
File: Checker.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Checks if files and paths in config-file are valid.
"""
import lib.Utility as U
import lib.Configuration as C
import lib.Logging as L

class Checker:

  def check_configfile_v1(configuration):

    error_message ="Error in configuration-file:\n\n"
    exception_occured = False

    for build_dir in configuration.directories:
      if not(U.check_provided_directory(build_dir)):
        error_message += "Build-directory " +build_dir+ " does not exist.\n\n"
        exception_occured = True


      for item in configuration.builds[build_dir]['items']:
        analysis_functor_dir = configuration.items[build_dir][item]['instrument_analysis'][0]
        if not (U.check_provided_directory(analysis_functor_dir)):
          error_message += "Analysis-functor dir " + analysis_functor_dir  + " does not exist.\n"
          exception_occured = True

        analysis_binary_dir = configuration.items[build_dir][item]['instrument_analysis'][2]
        if not (U.check_provided_directory(analysis_binary_dir)):
          error_message += "Analysis-binary dir " + analysis_binary_dir  + " does not exist.\n"
          exception_occured = True

        # Instead of prompting an error, we just create a log if the cubes-directory does not exist.
        # This is due to that the directory is created in ProfileSink
        cubes_dir = configuration.items[build_dir][item]['instrument_analysis'][1]
        if not(U.check_provided_directory(cubes_dir)):
          L.get_logger().log("Creating Cubes-Directory" + cubes_dir , level='info')

        if not(U.check_provided_directory(configuration.items[build_dir][item]["builders"])):
          error_message += "Builders-directory " + configuration.items[build_dir][item]["builders"] + " does not exist.\n"
          exception_occured = True

        for arg in configuration.items[build_dir][item]["args"]:
          if not(U.check_provided_directory(arg)):
            error_message += "args" + arg + "does not exist.\n"
            exception_occured = True

          if not(U.check_provided_directory(configuration.items[build_dir][item]["runner"])):
            error_message += "runner" + configuration.items[build_dir][item]["runner"] + "does not exist.\n"
            exception_occured = True

      if exception_occured:
        raise C.PiraConfigurationErrorException(error_message)

  def check_configfile_v2(configuration):
    if isinstance(configuration, C.PiraConfigurationAdapter):
      configuration = configuration.get_adapted()

    error_message = "Error in configuration-file:\n\n"
    exception_occured = False

    # check if directories exist
    for dir in configuration.get_directories():
      if not U.check_provided_directory(configuration.get_place(dir)):
        error_message += "Directory " + dir + " does not exist.\n"
        exception_occured = True

      for item in configuration.get_items(dir):
        if not U.check_provided_directory(item.get_analyzer_dir()):
          error_message += "Analyzer-Directory " + item.get_analyzer_dir() + " does not exist\n"
          exception_occured = True

        # instead of throwing an error, only an info is logged. This is due to that the directory is created in ProfileSink
        if not U.check_provided_directory(item.get_cubes_dir()):
          L.get_logger().log("Creating Cubes-Directory" + item.get_cubes_dir(), level='info')

        if not U.check_provided_directory(item.get_functor_base_path()):
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
          functors = ['analyze_', 'clean_', 'no_instr_', 'runner_', '']

          for functor in functors:
            path_to_check = item.get_functor_base_path() + '/'+ functor + item._name + underscore + flavor + '.py'
            L.get_logger().log('Checker::check_v2: ' + path_to_check)

            if not (U.is_file(path_to_check)):
              error_message += functor + "-functor of flavor " + flavor + " does not exist" + ".\n"
              exception_occured = True


    if exception_occured:
      raise C.PiraConfigurationErrorException(error_message)
