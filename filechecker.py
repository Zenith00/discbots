import os
import time
import sys, string, ast
import xxhash
import pymongo
import imgurpython
from pymongo import ReturnDocument
from imgurpython import ImgurClient
# import motor.motor_asyncio
import utils_file

path = "C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
global before

refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"



imgur = ImgurClient("5e1b2fcfcf0f36e",
                    "d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)
mongo_client = pymongo.MongoClient()

art_db = mongo_client.art
mercy_collection = art_db.mercy_collection




with open("paths.txt", "r") as f:
    global PATHS
    pathList = f.read()
    PATHS = ast.literal_eval(pathList)
    print("PATHS: " + str(PATHS))

def clean_string(string):
    return (string.encode(sys.stdout.encoding, errors='replace')).decode("utf-8")


count = 99


def create():
    mercy_collection.create_index([('hash', pymongo.ASCENDING)], unique=True)


def fix_names():
    for folderTuple in os.walk(PATHS["art"]):
        for file in folderTuple[2]:
            new_file_name = ''.join(c for c in file if c in string.printable)
            if new_file_name != file:
                try:
                    os.rename(os.path.join(folderTuple[0], file), os.path.join(folderTuple[0], new_file_name))
                except FileExistsError:
                    os.remove(os.path.join(folderTuple[0], file))
                print("renaming to " + new_file_name)
    return


def new():
    fix_names()
    for folderTuple in os.walk(PATHS["art"]):
        for file in folderTuple[2]:
            if "NSFW" not in folderTuple[0]:
                # print("call")
                filepath = os.path.join(folderTuple[0], file)
                x = xxhash.xxh32()
                with open(filepath, "rb") as image:
                    data = image.read()
                x.update(data)
                digest = x.digest()

                result = mercy_collection.update_one(
                    {"hash": digest},
                    {"$set": {"path": filepath}}, upsert=True
                )
                if "mercy" in folderTuple[0]:
                    config = {
                        'album': 'umuvY'
                    }
                else:
                    config = {}
                if not result.raw_result["updatedExisting"]:
                    print("New file found. Uploading...")
                    success = False
                    while not success:
                        try:
                            image = imgur.upload_from_path(filepath, config=config, anon=False)
                            success = True
                        except:
                            success = False
                            print("FAIL")

                    utils_file.append_line(PATHS["comms"] + "artlist.txt", image['link'])
                    print("Done")

    print("End Sweep")


create()

while True:
    new()
    time.sleep(10)
