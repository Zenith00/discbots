import inspect


def get_from_first_parent(key):
    try:
        return dict(inspect.getmembers(inspect.stack()[-1][0]))["f_globals"][key]
    except KeyError:
        return dict(inspect.getmembers(inspect.stack()[-1][0]))["f_locals"][key]
