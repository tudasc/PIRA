def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'make' + kwargs['compiler']


def active(benchmark, **kwargs):
  pass
