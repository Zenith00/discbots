import ast
import os
import string
import sys
import time
import xxhash

import imgurpython
import pymongo
from imgurpython import ImgurClient
import TOKENS
# import motor.motor_asyncio
from utils import utils_file
import traceback
path = "C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
global before
os.environ["PYTHONUNBUFFERED"] = "True"
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"



imgur = ImgurClient("5e1b2fcfcf0f36e",
                    "d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)
mongo_client = pymongo.MongoClient("mongodb://{usn}:{pwd}@nadir.space".format(usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS))

art_db = mongo_client.art
mercy_collection = art_db.mercy_collection

# PATHS = {'home': 'C:\\Users\\Austin\\Desktop\\Programming\\', 'art': "C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\", 'logs': 'C:\\Users\\Austin\\Desktop\\Programming\\Logs\\', 'comms': 'C:\\Users\\Austin\\Desktop\\Programming\\Comms\\'}
PATHS = {'art' : "/home/austin/Dropbox/Zenith's Fanart/"}


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
                        'album': 'PpALe'
                    }
                else:
                    config = {}
                if not result.raw_result["updatedExisting"]:
                    print("New file found. Uploading...")
                    try:
                        image = imgur.upload_from_path(filepath, config=config, anon=False)
                        # utils_file.append_line("C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\artlist.txt", image['link'])
                        print("Done")
                    except:
                        mercy_collection.delete_one({"hash":digest})
                        print("Rate limited. Waiting 5 minutes...")
                        time.sleep(60*10)




    print("End Sweep")


create()

while True:
    try:
        new()
    except:
        print(traceback.format_exc())
    time.sleep(10)
