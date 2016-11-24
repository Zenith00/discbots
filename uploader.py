import urllib
import imgurpython
from imgurpython import ImgurClient
import os, ast
# import win32file
# import win32con
import time, shutil, fileinput
from concurrent.futures import ProcessPoolExecutor
import sys
import traceback
import utils_file
import threading

# FANARTBOT
path = "C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"

PATHS = {}

imgur = ImgurClient("5e1b2fcfcf0f36e",
                    "d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)
print(imgur.credits)

print("IMGUR INIT")


def utils_file_prepend_line_wrapper(line, file):
    utils_file.prepend_line(line, file).send(None)


with open("paths.txt", "r") as f:
    global PATHS
    pathList = f.read()
    PATHS = ast.literal_eval(pathList)
    print("PATHS: " + str(PATHS))

while True:
    print("uploader init")
    with open(PATHS["comms"] + "toUpload.txt", "r+") as f:
        f.seek(0)
        fileToUpload = str(f.readline())
        f.close()
    with open(PATHS["comms"] + "toDelete.txt", "r+") as f:
        f.seek(0)
        fileToDelete = str(f.readline())
        f.close()
    if fileToUpload == "" and fileToDelete == "":
        time.sleep(5)
        continue


    print("File to upload found:")
    print(fileToUpload)
    if "nsfw" in fileToUpload:
        print("nsfw")
        continue
    if "\\mercy\\" in fileToUpload:
        config = {
            'album': 'umuvY'
        }
    elif "\\dva\\" in fileToUpload:
        config = {
            'album': 'xQXIi'
        }

    print("UPLOADING FILE")
    # upload file
    fileToUpload = fileToUpload.strip("\n")
    try:
        if fileToUpload != "":
            image = imgur.upload_from_path(fileToUpload, config=config, anon=False)
            # with open(PATHS["comms"] + "toUpload.txt", "r+") as toUpload:
            #     fileToUpload = toUpload.readline()
            utils_file.delete_lines(PATHS["comms"] + "toUpload.txt",1)
            utils_file_prepend_line_wrapper(PATHS["comms"] + "auto_art_list.txt", image['link'])
            print("WRITING LINK: " + image['link'])
        print(imgur.credits)
    except:
        print(traceback.format_exc())
        print("oops")
        continue


