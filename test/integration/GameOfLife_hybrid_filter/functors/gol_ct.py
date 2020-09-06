def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'CXX="scorep --instrument-filter=${TEST_DIR}/../../../extern/install/pgis/bin/out/instrumented-gol_ct.txt clang++" make gol'


def active(benchmark, **kwargs):
  pass
