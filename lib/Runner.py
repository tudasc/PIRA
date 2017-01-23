from ConfigLoader import ConfigurationLoader as CL
from Builder import Builder as B
import Logging as log
import Utility as util


def run(path_to_config, tld):
    try:
        if tld is not None:
            log.get_logger().log('Top Level Directory passed as CLI option')
            config_loader = CL(tld)
        else:
            config_loader = CL()
        configuration = config_loader.load(path_to_config)
        top_level_directories = configuration.get_directories()

        for directory in top_level_directories:
            log.get_logger().log('Creating builder for ' + directory, level='info')
            builder = B(directory, configuration)

            log.get_logger().log('Building ... ', level='info')
            builder.build()

            log.get_logger().log('Generate run configurations ... ', level='info')
            run_configs = builder.generate_run_configurations()

            log.get_logger().log('Retrieve submitter ... ', level='info')
            run_dispatcher = configuration.get_submitter()

            # TODO Make these configuration options configurable (cli and .json)
            runs_per_job = configuration.get_num_runs_per_job()
            kwargs = {'util': util, 'runs_per_job': runs_per_job, 'dependent': True}
            log.get_logger().log('Run dispatcher ... ', level='info')
            run_dispatcher.dispatch(run_configs, **kwargs)

            log.get_logger().dump_tape()

    except Exception as se:
        log.get_logger().log('Runner.run caught exception: ' + se.__class__.__name__ + ' Message: ' + se.message,
                             level='warn')
        log.get_logger().dump_tape()
