def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  return 'slurm submitter for hpcg'


def active(benchmark, **kwargs):
  pass
