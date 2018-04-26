import sys
sys.path.append('../')

from lib.ConfigLoaderNew import ConfigurationLoader as CL
import lib.Logging as logging
import lib.Utility as util

logger = logging.get_logger()
logger.set_state('debug')
logger.set_state('info')
logger.set_state('warn')

config_loader = CL()
configuration = config_loader.load_conf('../examples/item_based.json')

for key in configuration.builds:
    if(util.check_provided_directory(key) == False):
        logger.log("Build directory is invalid."+key,'error')
        exit(1)
    assert(configuration.directories[0] == key or configuration.directories[1] == key )
    assert(configuration.builds[key]['prefix'] == '')

    for item in configuration.builds[key]['items']:
        if(util.check_provided_directory(item) == False):
            logger.log("Item directory is invalid."+item,'error')
            exit(1)
        assert (item == '/home/sachin/MasterThesis/lulesh203' or item == '/home/sachin/MasterThesis/lulesh')

    for flavor in configuration.builds[key]['flavours']:
        assert (flavor == 'local-flav1' or flavor == 'vanilla')
#Check build config parameters

    for items in configuration.items[key]:
        for arg in configuration.items[key][items]['args']:
            assert (arg == '')

        #Check builders functor directory
        if(util.check_provided_directory(configuration.items[key][items]['builders']) == False):
            logger.log("Build functor directory is invalid."+configuration.items[key][items]['builders'],'error')
            exit(1)
        assert (configuration.items[key][items]['builders'] == '/home/sachin/IdeaProjects/master/benchpress/functors2' or
                configuration.items[key][items]['builders'] == '/home/sachin/IdeaProjects/master/benchpress/functors')

        if(configuration.items[key][items]['submitter'] == ''):
            #Check runner functor directory
            if(util.check_provided_directory(configuration.items[key][items]['runner']) == False):
                logger.log("Runner functor directory is invalid."+configuration.items[key][items]['runner'],'error')
                exit(1)
            assert (configuration.items[key][items]['runner'] == '/home/sachin/IdeaProjects/master/benchpress/functors2' or
                    configuration.items[key][items]['runner'] == '/home/sachin/IdeaProjects/master/benchpress/functors')

        else:
            #Check submitter functor
            if(util.check_provided_directory(configuration.items[key][items]['submitter']) == False):
                logger.log("Submitter functor directory is invalid."+configuration.items[key][items]['submitter'],'error')
                exit(1)
            assert (configuration.items[key][items]['submitter'] == '' or
                    configuration.items[key][items]['submitter'] == '')

        #Check analysis paths
        if(util.check_provided_directory(configuration.items[key][items]['instrument_analysis'][0]) == False):
            logger.log("Instrument Analysis functor directory is invalid."+configuration.items[key][items]['instrument_analysis'][0],'error')
            exit(1)
        assert (configuration.items[key][items]['instrument_analysis'][0] == '/home/sachin/IdeaProjects/master/benchpress/functors2' or
                configuration.items[key][items]['instrument_analysis'][0] == '/home/sachin/IdeaProjects/master/benchpress/functors')

        assert (configuration.items[key][items]['instrument_analysis'][1] == '/home/sachin/MasterThesis/lulesh203/lulesh' or
                configuration.items[key][items]['instrument_analysis'][1] == '/home/sachin/MasterThesis/lulesh/lulesh')


        if(util.check_provided_directory(configuration.items[key][items]['instrument_analysis'][2]) == False):
            logger.log("Instrument Analysis tool directory is invalid."+configuration.items[key][items]['instrument_analysis'][2],'error')
            exit(1)
        assert (configuration.items[key][items]['instrument_analysis'][2] == '/home/sachin/CLionProjects/pgoe' or
                configuration.items[key][items]['instrument_analysis'][2] == '/home/sachin/CLionProjects/pgoe')

for globalFlavor in configuration.global_flavors:
    assert (globalFlavor == 'local-flav1' or globalFlavor == 'local-flav2')
    if(util.check_provided_directory(configuration.global_submitter[globalFlavor]) == False):
        logger.log("Global Submitter directory is invalid."+configuration.items[key][items]['instrument_analysis'][2],'error')
        exit(1)
    assert (configuration.global_submitter[globalFlavor] == '/home/sachin/IdeaProjects/master/benchpress/functors2' or
            configuration.global_submitter[globalFlavor] == '/home/sachin/IdeaProjects/master/benchpress/functors')

logger.log('Configuration Valid!', 'info')