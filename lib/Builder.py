import lib.Utility as util
import lib.Logging as log
import lib.FunctorManagement as fm

import typing


class Builder:
  """
    Class which builds a benchmark and the run configuration.
    """

  def __init__(self, dir_key, configuration, no_instrumentation=False)->None:
    self.directory = dir_key
    self.config = configuration
    self.old_cwd = ''
    self.build_no_instr = no_instrumentation
    self.error = None

  def build(self, config, build, benchmark, flavor):
    try:
      self.set_up()
      self.build_detail(build, benchmark, flavor)
      self.tear_down()

    except Exception as e:
      log.get_logger().log('Caught exception ' + e.message, level='info')
      if self.error:
        raise Exception('Severe Problem in Builder.build')

  def set_up(self):
    directory_good = util.check_provided_directory(self.directory)
    if directory_good:
      self.old_cwd = util.get_cwd()
      util.change_cwd(self.directory)
    else:
      self.error = True
      raise Exception('Could not change to directory')

  def tear_down(self):
    util.change_cwd(self.old_cwd)

  def build_detail(self, build, benchmark, flavor):
    kwargs = {'compiler': 'clang++'}
    self.build_flavours(flavor, build, benchmark, kwargs)

  def build_flavours(self, flavor:str, build:str, benchmark:str, kwargs)->None:
    # benchmark == item
    benchmark_name = self.config.get_benchmark_name(benchmark)
    f_man = fm.FunctorManager(self.config)
    clean_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'clean')

    if self.build_no_instr:
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'basebuild')
    else:
      build_functor = f_man.get_or_load_functor(build, benchmark, flavor, 'build')
    log.get_logger().log('The retrieved build functor: ' + str(build_functor), level='debug')

    if build_functor.get_method()['active']:
      build_functor.active(benchmark, **kwargs)

    else:
      try:
        util.change_cwd(build)
        
        build_command = build_functor.passive(benchmark, **kwargs)
        clean_command = clean_functor.passive(benchmark, **kwargs)
        log.get_logger().log('Making clean in ' + benchmark, level='debug')
        util.shell(clean_command)
        log.get_logger().log('Building with command: ' + build_command, level='debug')
        util.shell(build_command)

      except Exception as e:
        log.get_logger().log(str(e), level='warn')

  def generate_run_configurations(self):
    """
        Generates scripts which are to be submitted to the batch system.
        These are stored in the format ((Benchmark, Flavor), Script_File_Name).
        :return: List of script files
    """
    run_configs = []
    kwargs = {'util': util}
    for flavor in self.config.get_flavors():
      for benchmark in self.config.get_benchmarks():
        run_generator = util.load_functor(self.config.get_flavor_run_generator(flavor))
        # This is always active mode. We need to generate scripts and return the filename.
        rc = run_generator.generate(benchmark, **kwargs)
        run_configs.append(((benchmark, flavor), rc))
    return run_configs
