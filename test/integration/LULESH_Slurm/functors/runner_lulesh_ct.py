def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return kwargs['LD_PRELOAD'] + ' mpirun -c 8 ./lulesh2.0 -b 1'


def active(benchmark, **kwargs):
    pass
