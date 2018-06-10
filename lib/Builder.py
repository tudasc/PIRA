import Utility as util
import Logging as logging


class Builder:
  """
    Class which builds a benchmark and the run configuration.
    """

  def __init__(self, dir_key, configuration):
    self.directory = dir_key
    self.config = configuration
    self.old_cwd = ''
    self.build_no_instr = False
    self.error = None

  def build(self, config, build, benchmark, flavor):
    try:
      self.set_up()
      self.build_detail(build, benchmark, flavor)
      self.tear_down()

    except Exception as e:
      logging.get_logger().log('Caught exception ' + e.message, level='info')
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

  def build_flavours(self, flavor, build, benchmark, kwargs):
    benchmark_name = self.config.get_benchmark_name(benchmark)
    if self.build_no_instr:
      clean_functor = util.load_functor(
          self.config.get_flavor_func(build, benchmark),
          util.build_clean_functor_filename(benchmark_name[0], flavor))
      build_functor = util.load_functor(
          self.config.get_flavor_func(build, benchmark),
          util.build_builder_functor_filename(False, True, benchmark_name[0], flavor))

    else:
      build_functor = util.load_functor(
          self.config.get_flavor_func(build, benchmark),
          util.build_builder_functor_filename(False, False, benchmark_name[0], flavor))
      clean_functor = util.load_functor(
          self.config.get_flavor_func(build, benchmark),
          util.build_clean_functor_filename(benchmark_name[0], flavor))

    if build_functor.get_method()['active']:
      build_functor.active(benchmark, **kwargs)

    else:
      try:
        commandbuild = build_functor.passive(benchmark, **kwargs)
        commandclean = clean_functor.passive(benchmark, **kwargs)
        util.change_cwd(benchmark)
        logging.get_logger().log('Making clean in ' + benchmark, level='debug')
        util.shell(commandclean)
        #util.unload_functo(clean_functor,'clean_'+flavor)
        logging.get_logger().log('Building with command: ' + commandbuild)
        util.shell(commandbuild)
        #util.unload_functo(build_functor,flavor)

      except Exception as e:
        logging.get_logger().log(e.message, level='warn')

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
