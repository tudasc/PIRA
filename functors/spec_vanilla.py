

def get_method():
    return {'passive' : True, 'active' : False}


def passive(benchmark, **kwargs):
    return 'make ' + benchmark + '.' + kwargs['compiler'] + '.vanilla'


def active(benchmark, **kwargs):
    pass