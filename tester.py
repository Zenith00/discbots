from pymongo import MongoClient
import pymongo
import TOKENS

c = MongoClient(
    "mongodb://{usn}:{pwd}@nadir.space".format(
        usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS)
)
count = 0

for dup in c.discord.userinfo.aggregate([
    {"$group": {"_id": "user_id", "dups": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}}
], allowDiskUse=True):
    print(dup)
    duplicates = dup["dups"]
#
# from utils import utils_file
#
# # utils_file.pickle_file(duplicates, "dups")
# duplicates = utils_file.unpickle_file("dups")

print(duplicates)

# d = {"_id_" : {"ns": "overwatch.message_log", "v": 1, "key": [("_id", 1)]},
# "message_id_1": {"v": 1, "unique": True, "key": [("message_id", 1.0)], "ns": "overwatch.message_log"},
# "toxicity_1" : {"v": 1, "key": [("toxicity", 1.0)], "ns": "overwatch.message_log"},
# "server_id_1" : {"v": 1, "key": [("server_id", 1.0)], "ns": "overwatch.message_log"},
# "channel_id_1": {"v": 1, "key": [("channel_id", 1.0)], "ns": "overwatch.message_log"},
# "user_id_1" : {"v": 1, "key": [("user_id", 1.0)], "ns": "overwatch.message_log"}, "date_1": {"v": 1, "key": [("date", 1.0)], "ns": "overwatch.message_log"}}
#
# print("message_id_1"[:-2])
# def log_query_parser(query):
# try:
# query_state = {"users":[], "channels":[], "servers":[]}
# # query_list = query.split(" ")
# target = ""
# for word in query:
# if word in ["user","channel","server"]:
# word += "s"
# if word in query_state.keys():
# target = word
# continue
# query_state[target].append(word)
# return query_state
# except:
# return "Syntax not recognized. Proper syntax: user 1111 2222 channel 3333 4444 5555 server 66666"
#
# res = log_query_parser(["user", "11111", "2222", "channel", "4444", "servers", "66666"])
#
# filter = {}
# for key in res.keys():
# translate = {"users": "user_id", "channels": "channel_id", "servers": "server_id"}
# for key in res.keys():
# filter[translate[key]] = {"$in": res[key]}
# print(filter)

# text = "asdafdasfa \n asdasdasd \n asdasda".encode('utf-8')
# print(text)

# tok = "MjM2MzQxMTkzODQyMDk4MTc3.DEdB2Q.IoOntdD63XRGXABH_WClkupNu5c"
# import discord
#
# client = discord.Client()
#
#
# @client.event
# async def on_message(message_in):
# pass
#
# @client.event
# async def on_ready():
# print('Connected!')
# print('Username: ' + client.user.name)
# print('ID: ' + client.user.id)
#
#
#
# client.run(tok, bot=True)

# import pip
# print(pip.get_installed_dstributions())

a = ['relay', ['Server Joins', '', ('94882524378968064',
                                    "['2016-03-01 21:29:07.ding=json&v=6 │648000', '2016-06-16 19:43:21.667000']"),
               ('127283257120129035',
                "['2016-08-16 17:22:29.76|linkbot | INFO:discord.gateway:sent the identify payload to create the websocket │24000']"),
               ('236343416177295360', "['2017-05-08 13:36:58.271232']"), (
                   '41771983423143937', "['2016-04-27 12:49:29.627000']")], 'rows']
