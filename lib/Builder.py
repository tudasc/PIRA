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
        self.build_no_instr = False;
        self.error = None

    def build(self):
        try:
            self.set_up()


            '''for benchmark in self.config.get_benchmarks():'''
            for build in self.config.get_builds():
                for benchmark in self.config.builds[build]['items']:
                    self.build_detail(build,benchmark)

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

    def build_detail(self, build,benchmark):
        #kwargs = {'compiler': 'gcc'}
        kwargs = {'compiler': ''}

        if self.config.builds[build]['flavours']:
            self.build_flavours(self.config.builds[build]['flavours'],build,benchmark,kwargs)

        else:
            self.build_flavours(self.config.global_flavors,build,benchmark,kwargs)

    def build_flavours(self,flavors,build,benchmark,kwargs):
        for flavor in flavors:
            #if(self.config.stop_iteration[build+benchmark+flavor] == False):
            if(self.build_no_instr == True):
                build_functor = util.load_functor(self.config.get_flavor_func(build,benchmark),'no_instr_'+flavor)

            else:
                build_functor = util.load_functor(self.config.get_flavor_func(build,benchmark),flavor)
                #print("Build Functor:"+build_functor)
            if build_functor.get_method()['active']:
                build_functor.active(benchmark, **kwargs)

            else:
                try:
                    command = build_functor.passive(benchmark, **kwargs)
                    print("Command:"+command)
                    util.change_cwd(benchmark)
                    util.shell('make clean')
                    util.shell(command)

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
                run_configs.append(((benchmark, flavor),rc))
        return run_configs
