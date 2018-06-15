def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'CubeCallGraphTool'


def active(benchmark, **kwargs):
  pass
