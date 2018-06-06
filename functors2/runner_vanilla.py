def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return './local-flav1' + '  -i 1 -p' + kwargs['compiler']


def active(benchmark, **kwargs):
  pass
