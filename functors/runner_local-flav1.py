def get_method():
    return {'passive': True, 'active': False}

def passive(benchmark, **kwargs):
    return './gol'+ kwargs['compiler']


def active(benchmark, **kwargs):
    pass
