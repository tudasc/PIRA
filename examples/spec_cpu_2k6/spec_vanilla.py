def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  cc = kwargs['compiler']
  return 'COMPILER=' + cc + ' COMPILERNAME=' + cc + ' FLAVOR=vanilla make ' + benchmark + '.' + cc + '.vanilla'


def active(benchmark, **kwargs):
  pass
