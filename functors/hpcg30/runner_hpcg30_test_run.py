def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return './bin/test_run-xhpcg --nx 104 --ny 104 --nz 104'


def active(benchmark, **kwargs):
  pass
