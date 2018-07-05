def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'make ' + benchmark + '.' + kwargs['compiler'] + '.finstr'


def active(benchmark, **kwargs):
  pass
