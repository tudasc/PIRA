def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return 'make CXXFLAGS="$LULESH_CXXFLAGS" CXX="mpicxx" -j'


def active(benchmark, **kwargs):
    pass
