import Utility as util
import Logging as log
import json

#Some Contants
#For builds
PREFIX = 0
ITEMS = 1
FLAVORS = 2
#For Items
INSTRUMENT_ANALYSIS = 0
BUILDERS = 1
ARGS = 2
RUNNER = 3
SUBMITTER =4

NO_ELEMENTS_BUILD = 8
NO_ELEMENTS_ITEMS = 5




class ConfigurationNew:
    """
    A configuration for the Runner.
    """
    def __init__(self):
        self.directories = []
        self.builds = {}
        self.items = {}
        self.prefix = []
        self.flavors = []
        self.instrument_analysis = []
        self.builders = []
        self.args = []
        self.runner = []
        self.submitter = []
        self.global_flavors = []
        self.global_submitter = {}

    def set_build_directories(self, dirs):
        self.directories = dirs

    def set_glob_flavors(self,glob_flavors):
        self.global_flavors = glob_flavors

    def set_glob_submitter(self,glob_submitter,glob_flavor):
        self.global_submitter.update({glob_flavor:glob_submitter})

    def set_prefix(self,prefix,dir):
        self.builds[dir].update({'prefix':prefix})

    def set_items(self,items,dir):
        self.builds[dir].update({'items':items})

    def set_flavours(self,flavours,dir):
        self.builds[dir].update({'flavours':flavours})

    def initialize_list(self,length):
        self.builds = [['']*NO_ELEMENTS_BUILD for i in range(length)]
        self.items = [['']*NO_ELEMENTS_ITEMS for i in range(length)]

    def initialize_build_dict(self,dir):
        for dirs in dir:
            self.builds.update({dirs:{}})
            self.items.update({dirs:{}})

    def initialize_item_dict(self,dir,items):
        for item in items:
            self.items[dir].update({item:{}})

    def set_item_instrument_analysis(self,inst_analysis,dir,item):
        self.items[dir][item].update({'instrument_analysis':inst_analysis})

    def set_item_builders(self,builders,dir,item):
        self.items[dir][item].update({'builders':builders})

    def set_item_args(self,args,dir,item):
        self.items[dir][item].update({'args':args})

    def set_item_runner(self,runner,dir,item):
        self.items[dir][item].update({'runner':runner})

    def set_item_submitter(self,submitter,dir,item):
        self.items[dir][item].update({'submitter':submitter})

    def get_builds(self):
        return self.builds.keys()

    def get_flavor_func(self,build,item):
        return self.items[build][item]['builders']

    def get_runner_func(self,build,item):
        return self.items[build][item]['runner']

    def get_analyse_func(self,build,item):
        #print self.items[build][item]['instrument_analysis']
        return self.items[build][item]['instrument_analysis'][0]

    def get_analyser_exp_dir(self,build,item):
        return self.items[build][item]['instrument_analysis'][1]

    def get_analyser_dir(self,build,item):
        return self.items[build][item]['instrument_analysis'][2]


class ConfigurationLoader:

    """
    Loads a provided configuration file. May be static in the future.

    """
    def __init__(self):
        self.config_cache = {}

    def load_conf(self,config_file):
        if config_file in self.config_cache:
            return self.config_cache[config_file]

        file_content = util.read_file(config_file)
        json_tree = json.loads(file_content)
        configuration = self.construct_from_json(json_tree)
        self.config_cache[config_file] = configuration
        return configuration

    def construct_from_json(self,json_tree):
        conf = ConfigurationNew()
        conf.set_build_directories(util.json_to_canonic(json_tree['description']['directories']))
        conf.initialize_build_dict(conf.directories)
        conf.set_glob_flavors(util.json_to_canonic(json_tree['description']['glob-flavors']))
        for glob_flav in conf.global_flavors:
            conf.set_glob_submitter(util.json_to_canonic(json_tree['description']['glob-submitter'][glob_flav]),glob_flav)
        for build_dirs in conf.directories:
            conf.set_prefix(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['prefix']),build_dirs)
            conf.set_items(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['items']),build_dirs)
            conf.initialize_item_dict(build_dirs,conf.builds[build_dirs]['items'])
            conf.set_flavours(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors'][build_dirs]),build_dirs)
            for items in conf.builds[build_dirs]['items']:
                conf.set_item_instrument_analysis(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                       ['instrument-analysis'][items]),build_dirs,items)
                conf.set_item_builders(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                                       ['builders'][items]),build_dirs,items)
                conf.set_item_args(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                   ['run'][items]['args']),build_dirs,items)
                conf.set_item_runner(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                          ['run'][items]['runner']),build_dirs,items)
                conf.set_item_submitter(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                          ['run'][items]['submitter']),build_dirs,items)
        return conf




