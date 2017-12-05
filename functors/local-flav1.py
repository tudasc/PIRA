
def get_method():
    return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
    return 'make INSTRFLAGS=\'-finstrument-functions -finstrument-functions-whitelist-inputfile="/home/sachin/CLionProjects/pgoe/out/instrumented-local-flav1-lulesh2.0.3.txt"\''+ kwargs['compiler']

def active(benchmark, **kwargs):
    pass
