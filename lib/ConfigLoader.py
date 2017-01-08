import Utility as util

import json


class Configuration:
    """
    A configuration for the Runner.
    """
    def __init__(self):
        self.benchmarks = []
        self.flavors = []
        self.top_level_directories = []
        self.flavor_build_functors = {} # (directory, module_name)

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
        self.flavor_build_functors[flavor] = func_tuple

    def get_flavor_func(self, flavor):
        return self.flavor_build_functors[flavor]


class ConfigurationLoader:
    """
    Loads a provided configuration file. May be static in the future.
    """
    def __init__(self):
        pass

    def load(self, config_file):
        file_content = util.read_file(config_file)
        json_tree = json.loads(file_content)
        configuration = self.construct_from_json(json_tree)
        return configuration

    def construct_from_json(self, tree):
        # TODO Actually implement me :)
        config = Configuration()
        config.set_directories(tree['top_level_directories'])
        config.set_benchmarks(tree['benchmarks'])
        config.set_flavors(tree['flavors'])
        return config

    def get_runner(self):
        pass
