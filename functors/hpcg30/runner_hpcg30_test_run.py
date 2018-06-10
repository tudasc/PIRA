def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'time ./bin/test_run-xhpcg --nx 16 --ny 16 --nz 16'


def active(benchmark, **kwargs):
  pass
