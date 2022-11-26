def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'CXX=clang++ make gol'


def active(benchmark, **kwargs):
  pass
