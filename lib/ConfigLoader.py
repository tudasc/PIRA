import Utility as util
import Logging as log
import json


#
# TODO Add a possibility to add kwargs in the requirements for the functor
#


class Configuration:
    """
    A configuration for the Runner.
    """

    def __init__(self):
        self.benchmarks = []
        self.flavors = []
        self.top_level_directories = []
        self.builder_functors = {}  # flavor => [directory, module_name]
        self.generator_functors = {}  # flavor => [directory, module_name]
        self.submitter = None  # => [directory, module_name]

    def set_directories(self, dirs):
        self.top_level_directories = dirs

    def get_directories(self):
        return self.top_level_directories

    def set_benchmarks(self, benchmarks):
        self.benchmarks = benchmarks

    def get_benchmarks(self):
        return self.benchmarks

    def set_flavors(self, flavors):
        self.flavors = flavors

    def get_flavors(self):
        return self.flavors

    def set_flavor_func(self, flavor, func_tuple):
        store_tuple = self.absolutify_tuple(func_tuple)
        self.builder_functors[flavor] = store_tuple

    def get_flavor_func(self, flavor):
        return self.builder_functors[flavor]

    def set_flavor_run_generator(self, flavor, generator_tuple):
        store_tuple = self.absolutify_tuple(generator_tuple)
        self.generator_functors[flavor] = store_tuple

    def get_flavor_run_generator(self, flavor):
        return self.generator_functors[flavor]

    def set_submitter(self, submitter_tuple):
        store_tuple = self.absolutify_tuple(submitter_tuple)
        self.submitter = store_tuple

    def get_submitter(self):
        return self.submitter[1]  # XXX Makes sense?

    def absolutify_tuple(self, tuple):
        abs_path = util.get_absolute_path(tuple[0])
        store_tuple = [abs_path, tuple[1]]
        return store_tuple


class ConfigurationLoader:
    """
    Loads a provided configuration file. May be static in the future.

    """

    def __init__(self):
        self.config_cache = {}

    def load(self, config_file):
        if config_file in self.config_cache:
            return self.config_cache[config_file]

        file_content = util.read_file(config_file)
        json_tree = json.loads(file_content)
        configuration = self.construct_from_json(json_tree)
        self.config_cache[config_file] = configuration
        return configuration

    def construct_from_json(self, tree):
        config = Configuration()
        config.set_directories(util.json_to_canonic(tree['top_level_directories']))
        config.set_benchmarks(util.json_to_canonic(tree['benchmarks']))
        config.set_flavors(util.json_to_canonic(tree['flavors']))
        # XXX We may need to change that canonicalization here, as we expect to have tuples.
        for flavor in config.get_flavors():
            config.set_flavor_func(flavor, util.json_to_canonic(tree['flavor_tuples'][flavor]))
        run_parameters = tree['run_parameters']
        for flavor in config.get_flavors():
            generator = util.json_to_canonic(run_parameters['generators'][flavor])
            config.set_flavor_run_generator(flavor, generator)
        config.set_submitter(run_parameters['submitter'])

        log.get_logger().log('Constructed config from JSON')

        return config

    def get_runner(self):
        pass
