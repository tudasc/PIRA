import Utility as util

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
        self.flavor_build_functors = {} # [directory, module_name]

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
        abs_path = util.get_absolute_path(func_tuple[0])
        store_tuple = [abs_path, func_tuple[1]]
        self.flavor_build_functors[flavor] = store_tuple

    def get_flavor_func(self, flavor):
        return self.flavor_build_functors[flavor]


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
        return config

    def get_runner(self):
        pass
