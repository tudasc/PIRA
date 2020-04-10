
def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'cd test && ' + kwargs['LD_PRELOAD'] + ' mpirun -np 8 ./amg2013 -pooldist 1 -r ' + str(kwargs['args'][1]) + ' ' + str(kwargs['args'][1]) + ' ' + str(kwargs['args'][1]) + ' -P 1 1 1 -printstats' 


def active(benchmark, **kwargs):
  pass
