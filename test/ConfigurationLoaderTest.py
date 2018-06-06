import sys
sys.path.append('../')

from lib.ConfigLoader import ConfigurationLoader as CL
import lib.Logging as logging

logger = logging.get_logger()
logger.set_state('debug')
logger.set_state('info')
logger.set_state('warn')

config_loader = CL()
configuration = config_loader.load('../examples/my_example_config.json')

logger.log(configuration.get_directories(), 'debug')
logger.log(configuration.get_benchmarks(), 'debug')
logger.log(configuration.get_flavors(), 'debug')
for flavor in configuration.get_flavors():
  logger.log(configuration.get_flavor_func(flavor), 'debug')

assert (configuration.get_directories()[0] == '/path/to/A')
assert (configuration.get_directories()[1] == 'path/to/b')
assert (configuration.get_directories()[2] == './relative/path/to/my/work')

assert (configuration.get_benchmarks()[0] == 'Benchmark one')
assert (configuration.get_benchmarks()[1] == 'Benchmark Two')

assert (configuration.get_flavors()[0] == 'vanilla')
assert (configuration.get_flavors()[1] == 'finstr')
