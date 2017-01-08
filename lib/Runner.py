from ConfigLoader import ConfigurationLoader as CL
from Builder import Builder as B


# TODO Test this :)
def run():
    # TODO Implement me
    configuration = CL.load('/path/to/config')
    top_level_directories = configuration.get_directories()

    for directory in top_level_directories:
        builder = B(directory, configuration)

        builder.build()

        run_config = builder.generate_run_configurations()

        runner = CL.get_runner()

        runner.submit(run_config)