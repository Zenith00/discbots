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

# FANARTBOT
path = "C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"

global PATHS
PATHS = {}

print(imgur.credits)
imgur = ImgurClient("5e1b2fcfcf0f36e", "d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)


print("IMGUR INIT")
with open("paths.txt", "r") as f:
    global PATHS
    pathList = f.read()
    PATHS = ast.literal_eval(pathList)
    print("PATHS: " + str(PATHS))

while True:
    print("uploader init")
    # grab first line
    with open(PATHS["comms"] + "toUpload.txt", "r+") as f:
        f.seek(0)
        fileToUpload = str(f.readline())

    if fileToUpload == "":
        time.sleep(5)
        continue

    print("File to upload found:")
    print(fileToUpload)
    print()
    # start imgur uploader




    print("UPLOADING FILE")
    # upload file
    fileToUpload = fileToUpload.strip("\n")
    try:
        image = imgur.upload_from_path(fileToUpload, config=None, anon=False)
        print(imgur.credits)
    except:
        print(traceback.format_exc())
        print("oops")
        continue
    print(image['link'])
	
    # remove first line
    for line_number, line in enumerate(fileinput.input(PATHS["comms"] + "toUpload.txt", inplace=1)):
        if line_number == 0:
            time.sleep(0)
        else:
            sys.stdout.write(line)

    print("WRITING LINK")
    # write link to botdata.txt and master image list
    with open(PATHS["comms"] + "botdata.txt", "a") as f:
        f.write(image['link'] + "\n")
    with open(PATHS["comms"] + "artlist.txt", "a") as f:
        f.write(image['link'] + "\n")
