import Utility as util


class Builder:
    """
    Class which builds a benchmark and the run configuration.
    """
    def __init__(self, dir_key, configuration):
        self.directory = dir_key
        self.config = configuration

    def build(self):
        # TODO We need to account for multiple benchmarks in the current top level working directory.
        self.set_up()
        self.build_detail()

    def set_up(self):
        util.check_provided_directory(self.directory)
        util.change_cwd(self.directory)

    def build_detail(self):
        # TODO Implement me
        for flavor in self.config.get_flavors():
            build_functor = util.load_functor(self.config.get_flavor_func(flavor))
            build_functor.build()
