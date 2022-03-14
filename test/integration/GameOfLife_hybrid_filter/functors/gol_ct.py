def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'CXX="scorep --instrument-filter=' + kwargs['filter-file'] + ' clang++" make gol'


def active(benchmark, **kwargs):
  pass
