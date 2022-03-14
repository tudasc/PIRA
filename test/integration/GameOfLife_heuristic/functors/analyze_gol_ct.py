def get_method():
  return {'passive': True, 'active': False}


def pre(**kwargs):
  pass


def passive(benchmark, **kwargs):
  return 'pgis_pira --heuristic-selection fp_and_mem_ops --cuttoff-selection unique_median'


def post(**kwargs):
  pass


def active(benchmark, **kwargs):
  pass
