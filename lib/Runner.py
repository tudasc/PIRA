from ConfigLoader import ConfigurationLoader as CL
from Builder import Builder as B
import Logging as log


def run(path_to_config):
    try:
        config_loader = CL()
        configuration = config_loader.load(path_to_config)
        top_level_directories = configuration.get_directories()

        for directory in top_level_directories:
            builder = B(directory, configuration)

            builder.build()

            run_configs = builder.generate_run_configurations()

            runner = config_loader.get_runner()

            # runner.submit(run_configs)
            log.get_logger().dump_tape()

    except StandardError as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
