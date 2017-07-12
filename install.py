import os
import shutil
import subprocess
import urllib.request

import pip
# import requests

def install(package):
    pip.main(['install', package])

def relative_path(file,relative):
    import os
    print(os.path.dirname(file))
    return os.path.join(os.path.dirname(file), relative)

if __name__ != "__main__":
    to_install = ["regex", "imgurpython", "fuzzywuzzy", "dateparser", "asteval","pyshorteners", "pymongo", "motor", "discord.py",
                  "unidecode"]
    for x in to_install:
        install(x)

    try:
        if not os.path.isfile('config.py'):
            shutil.copy2('config_default.py', 'config.py')
        if not os.path.isfile('TOKENS.py'):
            shutil.copy2('TOKENS_DEFAULT.py', 'TOKENS.py')
    except:
        pass

    # url = "https://fastdl.mongodb.org/win32/mongodb-win32-x86_64-2008plus-ssl-3.4.6-signed.msi"
    # with urllib.request.urlopen(url) as response, open("mongodb-win32-x86_64-2008plus-ssl-3.4.6-signed.msi", 'wb') as out_file:
    #     data = response.read()
    #     out_file.write(data)

    # flags = subprocess.CREATE_NEW_CONSOLE
    # install_mongo = subprocess.Popen([r'powershell',
    #                                   '-ExecutionPolicy',
    #                                   'Unrestricted',
    #                                   './installmongo.ps1', ], creationflags=flags)

    # result = install_mongo.wait()

    # url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/python_Levenshtein-0.12.0-cp36-cp36m-win32.whl"
    # response = requests.get(url)
    # with open("python_Levenshtein-0.12.0-cp36-cp36m-win32.whl", 'wb') as out_file:
    #     for block in response.iter_content(1024):
    #         out_file.write(block)
    #
    # url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/Pillow-4.2.1-cp36-cp36m-win32.whl"
    # response = requests.get(url)
    # with open("Pillow-4.2.1-cp36-cp36m-win32.whl", 'wb') as out_file:
    #     for block in response.iter_content(1024):
    #         out_file.write(block)
    #
    # url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/numpy-1.13.1+mkl-cp36-cp36m-win32.whl"
    # response = requests.get(url)
    # with open("numpy-1.13.1+mkl-cp36-cp36m-win32.whl", 'wb') as out_file:
    #     for block in response.iter_content(1024):
    #         out_file.write(block)
    #
    # url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/wu4bx7or/scipy-0.19.1-cp36-cp36m-win32.whl"
    # response = requests.get(url)
    # with open("scipy-0.19.1-cp36-cp36m-win32.whl", 'wb') as out_file:
    #     for block in response.iter_content(1024):
    #         out_file.write(block)

# subprocess.call("python -m pip install {}".format(relative_path(__file__, "python_Levenshtein-0.12.0-cp36-cp36m-win32.whl")))
# subprocess.call("python -m pip install {}".format(relative_path(__file__, "Pillow-4.2.1-cp36-cp36m-win32.whl")))
# subprocess.call("python -m pip install {}".format(relative_path(__file__, "numpy-1.13.1+mkl-cp36-cp36m-win32.whl")))
# subprocess.call("python -m pip install {}".format(relative_path(__file__, "scipy-0.19.1-cp36-cp36m-win32.whl")), cwd=)


subprocess.call("python -m pip install python-Levenshtein --force-reinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "python_Levenshtein-0.12.0-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
subprocess.call("python -m pip install pillow --force-reinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "Pillow-4.2.1-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
subprocess.call("python -m pip install numpy --force-reinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "numpy-1.13.1+mkl-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
subprocess.call("python -m pip install scipy --force-reholinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "scipy-0.19.1-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)




