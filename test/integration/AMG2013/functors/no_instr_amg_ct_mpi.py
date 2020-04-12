def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'make CC="OMPI_CC=clang mpicc" -j 16'


def active(benchmark, **kwargs):
  pass
