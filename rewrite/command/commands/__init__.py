import os
from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]


def reload():
    for module in os.listdir(dirname(__file__)):
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        __import__(module[:-3], locals(), globals())
