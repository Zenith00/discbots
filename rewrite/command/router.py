import ast
import importlib
from .commands import *

class CommandRouter():
    def __init__(self):
        pass

    def build(self,command, args=None):
        params = {}
        if command == "refresh":
            reload()
            self.refresh_command(args)
            return
        if command[-1] == "!":
            command = command[:-1]
            params = ast.literal_eval(args)
            globals()[command].run(**params)
        else:
            globals()[command].get_arg_order()


    @staticmethod
    def refresh_command(command_name):
        importlib.reload(globals()[command_name])

