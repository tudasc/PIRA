
temporary_it = 0

def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  global temporary_it
  temporary_it = 1
  return 'echo '


def active(benchmark, **kwargs):
  pass

def get_it():
  global temporary_it
  return temporary_it
