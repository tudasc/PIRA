def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return 'make CXX_WRAP="mpicxx" -j'


def active(benchmark, **kwargs):
    pass
