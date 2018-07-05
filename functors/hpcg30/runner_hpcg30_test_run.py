def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return './bin/test_run-xhpcg --nx 14 --ny 14 --nz 14'


def active(benchmark, **kwargs):
  pass
