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
        self.builds = [[]]
        self.items = [[]]
        self.prefix = []
        self.flavors = []
        self.instrument_analysis = []
        self.builders = []
        self.args = []
        self.runner = []
        self.submitter = []
        self.global_flavors = []
        self.global_submitter = []

    def set_build_directories(self, dirs):
        self.directories = dirs

    def set_glob_flavors(self,glob_flavors):
        self.global_flavors = glob_flavors

    def set_glob_submitter(self,glob_submitter):
        self.global_submitter = glob_submitter

    def set_prefix(self,prefix,count):
        self.builds[count][PREFIX] = prefix
            #self.builds[0][1] = prefix

    def set_items(self,items,count):
        self.builds[count][ITEMS] = items
        #self.items = items

    def set_flavours(self,flavours,count):
        self.builds[count][FLAVORS] = flavours

    def initialize_list(self,length):
        self.builds = [['']*NO_ELEMENTS_BUILD for i in range(length)]
        self.items = [['']*NO_ELEMENTS_ITEMS for i in range(length)]

    def set_item_instrument_analysis(self,inst_analysis,count):
        #self.instrument_analysis = self.instrument_analysis.append(inst_analysis)
        self.instrument_analysis.append(inst_analysis)
        self.items[count][INSTRUMENT_ANALYSIS] = self.instrument_analysis

    def set_item_builders(self,builders,count):
        self.builders.append(builders)
        self.items[count][BUILDERS] = self.builders

    def set_item_args(self,args,count):
        self.args.append(args)
        self.items[count][ARGS] = self.args

    def set_item_runner(self,runner,count):
        self.runner.append(runner)
        self.items[count][RUNNER] = self.runner

    def set_item_submitter(self,submitter,count):
        self.submitter.append(submitter)
        self.items[count][SUBMITTER] = self.submitter


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
        conf.initialize_list(len(conf.directories))
        conf.set_glob_flavors(util.json_to_canonic(json_tree['description']['glob-flavors']))
        conf.set_glob_submitter(util.json_to_canonic(json_tree['description']['glob-submitter']))
        count = 0
        for build_dirs in conf.directories:
            conf.set_prefix(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['prefix']),count)
            conf.set_items(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['items']),count)
            conf.set_flavours(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors'][build_dirs]),count)
            for items in conf.builds[count][1]:
                conf.set_item_instrument_analysis(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                       ['instrument-analysis'][items]),count)
                conf.set_item_builders(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                                       ['builders'][items]),count)
                conf.set_item_args(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                   ['run'][items]['args']),count)
                conf.set_item_runner(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                          ['run'][items]['runner']),count)
                conf.set_item_submitter(util.json_to_canonic(json_tree['description']['builds'][build_dirs]['flavors']
                                                          ['run'][items]['submitter']),count)

            count += 1
            conf.instrument_analysis = []
            conf.builders = []
            conf.args = []
            conf.runner = []
            conf.submitter = []
        return conf




