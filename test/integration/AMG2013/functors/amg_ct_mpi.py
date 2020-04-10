
def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'make CC="OMPI_CC=clang scorep --instrument-filter=' + kwargs['filter-file'] + ' mpicc" -j 16'

def active(benchmark, **kwargs):
  pass
