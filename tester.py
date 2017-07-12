# from pymongo import MongoClient
# import pymongo
# import TOKENS
#
# c = MongoClient(
#     "mongodb://{usn}:{pwd}@nadir.space".format(
#         usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS)
# )

# d = {"_id_"        : {"ns": "overwatch.message_log", "v": 1, "key": [("_id", 1)]},
#  "message_id_1": {"v": 1, "unique": True, "key": [("message_id", 1.0)], "ns": "overwatch.message_log"},
#  "toxicity_1"  : {"v": 1, "key": [("toxicity", 1.0)], "ns": "overwatch.message_log"},
#  "server_id_1" : {"v": 1, "key": [("server_id", 1.0)], "ns": "overwatch.message_log"},
#  "channel_id_1": {"v": 1, "key": [("channel_id", 1.0)], "ns": "overwatch.message_log"},
#  "user_id_1"   : {"v": 1, "key": [("user_id", 1.0)], "ns": "overwatch.message_log"}, "date_1": {"v": 1, "key": [("date", 1.0)], "ns": "overwatch.message_log"}}
#
# print("message_id_1"[:-2])
# def log_query_parser(query):
#     try:
#         query_state = {"users":[], "channels":[], "servers":[]}
#         # query_list = query.split(" ")
#         target = ""
#         for word in query:
#             if word in ["user","channel","server"]:
#                 word += "s"
#             if word in query_state.keys():
#                 target = word
#                 continue
#             query_state[target].append(word)
#         return query_state
#     except:
#         return "Syntax not recognized. Proper syntax: user 1111 2222 channel 3333 4444 5555 server 66666"
#
# res = log_query_parser(["user", "11111", "2222", "channel", "4444", "servers", "66666"])
#
# filter = {}
# for key in res.keys():
#     translate = {"users": "user_id", "channels": "channel_id", "servers": "server_id"}
#     for key in res.keys():
#         filter[translate[key]] = {"$in": res[key]}
# print(filter)

text = "asdafdasfa \n asdasdasd \n asdasda".encode('utf-8')
print(text)