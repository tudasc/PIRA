def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return 'make OMPI_CXX=clang++ CXX_WRAP="scorep --instrument-filter=' + kwargs['filter-file'] + ' mpicxx" -j'

def active(benchmark, **kwargs):
    pass
