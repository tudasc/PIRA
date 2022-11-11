
def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'make clean'


def active(benchmark, **kwargs):
  pass
