def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return kwargs['LD_PRELOAD'] + ' mpirun -c 8 ./bin/kripke.exe --procs 2,2,2 --groups ' + kwargs['args'][1]


def active(benchmark, **kwargs):
    pass
