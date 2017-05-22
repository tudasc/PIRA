from ConfigLoader import ConfigurationLoader as CL
from ConfigLoaderNew import ConfigurationLoader as Conf
from Builder import Builder as B
import Logging as log
import Utility as util


def run(path_to_config):
    try:
        config_loader = Conf()
        configuration = config_loader.load_conf(path_to_config)
        #top_level_directories = configuration.get_directories()

        for directory in configuration.directories:
            builder = B(directory, configuration)

            builder.build()

            run_configs = builder.generate_run_configurations()

            run_dispatcher = configuration.get_submitter()

            # TODO Make these configuration options configurable (cli and .json)
            runs_per_job = configuration.get_num_runs_per_job()
            kwargs = {'util': util, 'runs_per_job': runs_per_job, 'dependent': True}
            run_dispatcher.dispatch(run_configs, **kwargs)

            log.get_logger().dump_tape()

    except StandardError as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
