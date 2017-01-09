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
        self.error = None

    def build(self):
        try:
            self.set_up()

            for benchmark in self.config.get_benchmarks():
                self.build_detail(benchmark)

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

    def build_detail(self, benchmark):
        kwargs = {'compiler': 'gcc'}

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

    def generate_run_configurations(self):
        pass
