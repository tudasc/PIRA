import sys
sys.path.append('../')

from lib.ConfigLoaderNew import ConfigurationLoader as CL
import lib.Logging as logging

logger = logging.get_logger()
logger.set_state('debug')
logger.set_state('info')
logger.set_state('warn')

config_loader = CL()
configuration = config_loader.load_conf('../examples/item_based.json')

logger.log(configuration.directories, 'debug')
logger.log(configuration.global_flavors,'debug')
logger.log(configuration.global_submitter,'debug')

for key in configuration.builds:
    assert(configuration.directories[0] == key or configuration.directories[1] == key )

#Check build config parameters
assert(configuration.builds['one']['prefix'] == 'xx_')
assert(configuration.builds['one']['items'] == ['item1','item2'])
assert(configuration.builds['one']['flavours'] == ['local-flav1','local-flav2'])

#Check item config parameters
assert(configuration.items['one']['item1']['instrument_analysis'] == '/path/to/py/functor' )
assert(configuration.items['one']['item1']['builders'] == '/path/to/py/functor' )
assert(configuration.items['one']['item1']['args'] == ['123','abs'])
assert(configuration.items['one']['item1']['runner'] == 'path/to/py/func' )
assert(configuration.items['one']['item1']['submitter'] == '')

logger.log('Configuration Valid!', 'info')