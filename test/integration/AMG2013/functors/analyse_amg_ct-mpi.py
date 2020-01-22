def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'pgis_pira'


def active(benchmark, **kwargs):
  pass
