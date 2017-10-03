def get_method():
    return {'passive': True, 'active': False}

def passive(benchmark, **kwargs):
    #runcommand = {"'./lulesh2.0'+ ' -i10'"}
    return './lulesh2.0'+ ' -i 1'+kwargs['compiler']



def active(benchmark, **kwargs):
    pass
