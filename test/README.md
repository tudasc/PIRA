# Resources used in PIRA tests

The directories contain the resources used for testing PIRA and are organized in the two categories *unit* and *integration*.
This corresponds to, as the names suggest, the size of the tests that go into both directories.

The third directory is meant to contain inputs to PIRA that are shared between unit and integration test cases, so we do not have to duplicate inputs.

## unit

Is meant to hold the unit tests that are run.

## integration

This folder has all resources required for our integration testing, i.e., invoking pira.py with some arguments.
The sub directories here are meant to hold those files (configs, etc), that are specific to ```targets``` and are only used in integration testing.

### configs

Contains various configs that are valid and invalid.
Test targeting the configuration should make sure that errors are caught as early as possible.

### functors

Contains various functors.
Some of the functors can / should be used together with a config, but that is not mandatory.

### targets

Contains target programs that we use to apply our toolchain to during integration testing.
