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

if __name__ == "__main__":
    to_install = ["regex", "imgurpython", "fuzzywuzzy", "dateparser", "asteval","pyshorteners", "pymongo", "motor", "discord.py[voice]",
                  "unidecode", "tqdm"]
    for x in to_install:
        install(x)

    try:
        if not os.path.isfile('config.py'):
            shutil.copy2('config_default.py', 'config.py')
        if not os.path.isfile('TOKENS.py'):
            shutil.copy2('TOKENS_DEFAULT.py', 'TOKENS.py')
    except:
        pass

    try:

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
    except Exception as e:
        print(e)

    urllib.request.urlretrieve("https://dl.dropboxusercontent.com/content_link/lmkJksU3EH2LMtFg7HmphQ1Z3vOyeLJMZwNtHkmV5V10PxjeUTpzG1ZaaVCPHDCy/file?dl=1", "numpy-1.13.1+mkl-cp36-cp36m-win32.whl")
    urllib.request.urlretrieve("https://dl.dropboxusercontent.com/content_link/KvmSlSHsLLb3T4SjjpYN5QCOo4xAnmUzL6YN70mA5nCXCQikOYtN272BBG75RyNN/file?dl=1", "Pillow-4.2.1-cp36-cp36m-win32.whl")
    urllib.request.urlretrieve("https://dl.dropboxusercontent.com/content_link/3QK9nGjLEGyrvUgXIbyJD6JcGvpQGCPl9iz2FdyLPSd6ylbXdF1tEJzQfQUhd8li/file?dl=1", "python_Levenshtein-0.12.0-cp36-cp36m-win32.whl")
    urllib.request.urlretrieve("https://dl.dropboxusercontent.com/content_link/M0dVXyWzNfyavcRgcH4qXMQkdaEsxi5bTfchF0CkxQbZd4CGbkrcxXPBtpX2oLFY/file?dl=1", "scipy-0.19.1-cp36-cp36m-win32.whl")


    subprocess.call("python -m pip install {}".format(relative_path(__file__, "python_Levenshtein-0.12.0-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    subprocess.call("python -m pip install {}".format(relative_path(__file__, "Pillow-4.2.1-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    # subprocess.call("python -m pip install {}".format(relative_path(__file__, "numpy-1.13.1+mkl-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    subprocess.call("python -m pip install {}".format(relative_path(__file__, "scipy-0.19.1-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)

    #
    # subprocess.call("python -m pip install python-Levenshtein --force-reinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "python_Levenshtein-0.12.0-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    # subprocess.call("python -m pip install pillow --force-reinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "Pillow-4.2.1-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    # subprocess.call("python -m pip install numpy --force-reinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "numpy-1.13.1+mkl-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    # subprocess.call("python -m pip install scipy --force-reholinstall --use-wheel --no-index --find-links={}".format(relative_path(__file__, "scipy-0.19.1-cp36-cp36m-win32.whl")), cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
    #



