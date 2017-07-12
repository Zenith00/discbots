import os
import platform
import shutil
import subprocess
from utils import utils_text, utils_image, utils_parse, utils_file
import pip
import urllib.request

def install(package):
    pip.main(['install', package])

if __name__ != "__main__":
    to_install = ["regex", "python-Levenshtein", "imgurpython", "fuzzywuzzy", "dateparser", "convertdate", "asteval", "pymongo", "motor", "discord.py",
                  "unidecode", "PIL"]
    for x in to_install:
        install(x)

    if not os.path.isfile('config.py'):
        shutil.copy2('config_default.py', 'config.py')
    if not os.path.isfile('TOKENS.py'):
        shutil.copy2('TOKENS_DEFAULT.py', 'TOKENS.py')

    url = "https://fastdl.mongodb.org/win32/mongodb-win32-x86_64-2008plus-ssl-3.4.6-signed.msi"
    with urllib.request.urlopen(url) as response, open("mongodb-win32-x86_64-2008plus-ssl-3.4.6-signed.msi", 'wb') as out_file:
        data = response.read()
        out_file.write(data)

    flags = subprocess.CREATE_NEW_CONSOLE
    install_mongo = subprocess.Popen([r'powershell',
                                      '-ExecutionPolicy',
                                      'Unrestricted',
                                      './installmongo.ps1', ], creationflags=flags)

    result = install_mongo.wait()

    url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/python_Levenshtein-0.12.0-cp36-cp36m-win32.whl"
    with urllib.request.urlopen(url) as response, open("python_Levenshtein-0.12.0-cp36-cp36m-win32.whl", 'wb') as out_file:
        data = response.read()
        out_file.write(data)

    url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/Pillow-4.2.1-cp36-cp36m-win32.whl"
    with urllib.request.urlopen(url) as response, open("Pillow-4.2.1-cp36-cp36m-win32.whl", 'wb') as out_file:
        data = response.read()
        out_file.write(data)

    url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/numpy-1.13.1+mkl-cp36-cp36m-win32.whl"
    with urllib.request.urlopen(url) as response, open("numpy-1.13.1+mkl-cp36-cp36m-win32.whl", 'wb') as out_file:
        data = response.read()
        out_file.write(data)

    url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/scipy-0.19.1-cp36-cp36m-win32.whl"
    with urllib.request.urlopen(url) as response, open("scipy-0.19.1-cp36-cp36m-win32.whl", 'wb') as out_file:
        data = response.read()
        out_file.write(data)

subprocess.call("pip install {}".format("python_Levenshtein-0.12.0-cp36-cp36m-win32.whl"), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
