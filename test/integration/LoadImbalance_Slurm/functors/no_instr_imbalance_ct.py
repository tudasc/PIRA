def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'make CC="OMPI_CC=clang mpicc"'


def active(benchmark, **kwargs):
  pass
