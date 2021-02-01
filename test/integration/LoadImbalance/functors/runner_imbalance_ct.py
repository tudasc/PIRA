def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  # return kwargs['LD_PRELOAD'] + ' mpirun -np 8 imbalance-static.out'
  return kwargs['LD_PRELOAD'] + ' mpirun -np 8 imbalance-dynamic.out'

def active(benchmark, **kwargs):
  pass
