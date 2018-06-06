def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'time ./bin/test_run-xhpcg --nx 64 --ny 64 --nz 64'


def active(benchmark, **kwargs):
  pass
