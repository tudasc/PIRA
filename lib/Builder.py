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
        self.error = False

    def build(self):
        try:
            for benchmark in self.config.get_benchmarks():
                self.set_up(benchmark)
                self.build_detail(benchmark)
                self.tear_down(benchmark)

        except Exception as e:
            logging.get_logger().log('Caught exception ' + e.message, level='info')
            if self.error:
                raise Exception('Severe Problem in Builder.build')

    def set_up(self, benchmark):
        directory_good = util.check_provided_directory(self.directory)
        if directory_good:
            complete_path = self.directory + '/' + self.config.get_benchmark_to_directory_mapping()[benchmark]
            directory_good = util.check_provided_directory(complete_path)
            if directory_good:
                self.old_cwd = util.get_cwd()
                util.change_cwd(complete_path)
            else:
                self.error = True
                raise Exception('Exceptional directory ' + complete_path)
        else:
            self.error = True
            raise Exception('Exceptional directory ' + self.directory)

    def tear_down(self, benchmark):
        util.change_cwd(self.old_cwd)

    def build_detail(self, benchmark):
        kwargs = {'compiler': 'gcc'}

        try:
            for flavor in self.config.get_flavors():
                build_functor = util.load_functor(self.config.get_flavor_func(flavor))
                if build_functor.get_method()['active']:
                    build_functor.active(benchmark, **kwargs)

                else:
                    try:
                        command = build_functor.passive(benchmark, **kwargs)
                        util.shell(command)

                    except Exception as e:
                        logging.get_logger().log(e.message, level='warn')
        except Exception as e:
					self.error = True
					logging.get_logger().log(e.message, level='error')

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
                run_configs.append(((benchmark, flavor),rc))
        return run_configs
