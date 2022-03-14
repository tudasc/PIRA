def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return './gol ' + kwargs['args'][1]


def active(benchmark, **kwargs):
  pass
