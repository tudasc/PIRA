def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return 'make INSTRFLAGS=\'-finstrument-functions -finstrument-functions-whitelist-inputfile="/home/sachin/CLionProjects/pgoe/out/instrumented-vanilla-lulesh.txt"\''+ kwargs['compiler']

def active(benchmark, **kwargs):
    pass
