import urllib.request

from pymongo import MongoClient
import pymongo
import TOKENS

# TOKENSc = MongoClient(
#     "mongodb://{usn}:{pwd}@nadir.space".format(
#         usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS)
# )
# count = 0
#
# for dup in c.discord.userinfo.aggregate([
#     {"$group": {"_id": "user_id", "dups": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
#     {"$match": {"count": {"$gt": 1}}}
# ], allowDiskUse=True):
#     print(dup)
#     duplicates = dup["dups"]
#
# from utils import utils_file
#
# # utils_file.pickle_file(duplicates, "dups")
# duplicates = utils_file.unpickle_file("dups")

# print(dupslicates)

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
urllib.request.urlretrieve("https://www.dropbox.com/s/7sz2rzan8u74kw4/numpy-1.11.3%2Bmkl-cp36-cp36m-win32.whl?dl=1",
                           "numpy-1.13.1+mkl-cp36-cp36m-win32.whl")

a = ['relay', [['Server Joins', '--'], ('/r/Overwatch', "['2016-06-27 05:51:15.380000']"), ('Thonk-Collection', "['2017-07-11 07:03:58.272799']"),
               ('1072', "['2017-01-30 23:38:29.870000']"), ('Hype Nig (no space)', "['2017-01-23 01:09:10.820000']"),
               ('Reformed uwus', "['2017-01-04 00:31:01.594000']"), ('asdad', "['2017-07-12 05:37:37.059000']"),
               ('The Depths Of Hell', "['2017-02-15 04:56:32.638000']"), ('Discord Emotes', "['2017-01-04 00:31:15.593000']"),
               ('Discord Bots', "['2016-11-13 07:30:05.066000']"), ('Live in Five', "['2017-01-04 00:31:37.114000']"),
               ('Danmaku Paradise', "['2017-02-08 16:59:23.952000']"), ('Dofus', "['2017-01-04 00:30:53.106000']"),
               ('/r/HeroesOfTheStorm', "['2017-04-27 16:16:41.719135']"), ('Vinesauce Reddit Discord', "['2017-01-18 06:03:00.604000']"),
               ("Mum's House", "['2017-07-11 06:56:06.890774']"), ('Programming', "['2017-01-30 02:50:46.768000']"),
               ('The Portal', "['2017-01-18 05:59:21.101000']"), ('RemiWink', "['2017-07-11 07:04:00.976584']"),
               ('The Wired', "['2017-01-04 00:30:43.830000']"), ('Hot Gamer Sex Cave', "['2017-01-18 05:59:59.853000']"),
               ('#memesquad', "['2017-01-18 05:59:32.871000']"), ('Aurelion Sol Mains', "['2017-05-13 02:42:19.377775']"),
               ("Thinks 'n' Smugs 'n' Smags", "['2017-01-25 02:32:46.082000']"), ('Emote Central™ - Emote Server List', "['2017-04-28 07:20:31.909125']"),
               ("/SOP/ ~ Starlight's Obscene Poon", "['2016-12-05 06:59:20.090000']"), ('Chen Emotes Anonymous', "['2017-01-09 06:25:06.229000']"),
               ('FreekieServer', "['2017-01-09 06:26:40.966000']"), ('Academy City', "['2017-01-18 08:55:39.200000']"),
               ('InFlamesWeMust', "['2017-07-11 07:04:02.916509']"), ('r/osugame', "['2017-04-25 03:59:13.666698']"),
               ('TRUSTED GAMES', "['2017-01-21 23:16:52.576000']"), ('Brayve New World', "['2016-09-24 01:19:19.055000']"),
               ('MEMES', "['2016-10-08 19:14:50.848000']"), ("Ping and Salar's Emote List", "['2017-04-28 07:20:37.086805']"),
               ('Trivia-Bot', "['2017-03-27 15:53:33.637984']"), ('/r/Overwatch Scrims (Beta)', "['2016-10-14 04:24:21.468000']"),
               ('🌙 ²', "['2017-07-09 21:12:04.982131']"), ('Discord API', "['2016-10-25 03:30:58.456000']"), ('DND', "['2017-01-19 21:55:52.920000']"),
               ('Winja Cats', "['2017-06-15 06:16:44.837041']"), ('Art Gallery (WIP)', "['2017-02-26 20:48:30.327000']"),
               ("Gamer's Emoji Server (where no succ is given)", "['2017-01-18 05:59:52.682000']"), ('Tokyo Town', "['2017-04-28 07:21:03.654234']"),
               ('Duck World', "['2017-01-09 06:26:25.478000']"), ('/r/LeagueOfLegends', "['2017-04-18 17:39:54.122908']"),
               ('Dungeons & Dragons', "['2016-08-02 03:44:48.397000']"), ('Otaku Shelter', "['2017-01-09 06:26:15.688000']"),
               ('Team Salty Dogs', "['2016-05-15 04:52:10.131000']"), ('Gonzo Agonzo Ygonzo', "['2017-01-09 06:26:17.894000']"),
               ('thanks me too', "['2017-06-26 23:35:04.962648']"), ('aaaaaaaaaaaaaaaaaaa', "['2017-01-04 18:59:01.488000']"),
               ('Remote Server', "['2016-12-31 01:54:09.979000']"), ('M3R-CY', "['2017-01-27 01:19:42.647000']"),
               ('Discord Developers', "['2016-10-28 03:27:03.600000']"), ('Vayne Mains', "['2017-05-19 20:05:07.729919']"),
               ('JynGG', "['2017-04-28 07:20:41.634000']"), ('Bathrobe_Dwane covenant', "['2017-07-11 17:47:16.160266']"),
               ('/r/LoveLive', "['2017-01-18 05:59:48.102000']"), ('drawful', "['2017-01-21 07:07:50.190000']"), ('Rabbitu', "['2016-11-19 04:28:25.838000']"),
               ("TheZealotGamer's Code Geass Server", "['2017-01-18 05:56:46.233000']"), ('Harker League', "['2016-04-24 00:56:30.721000']"),
               ('Emote List', "['2017-01-04 00:30:32.824000']"), ('emotes, yeah.', "['2017-01-09 06:26:20.742000']"),
               ('TEST Squadron', "['2016-10-10 03:14:40.134000']"), ('apsisbot', "['2016-12-26 02:01:53.211000']"), (None, "['2016-11-02 02:13:33.942000']"),
               ('Best Girl? Best Girl.', "['2017-01-04 00:30:37.488000']"), ('QTmotes', "['2017-01-04 00:24:32.891000']"),
               ('✨💜', "['2017-04-28 07:20:43.067000']"), ('Discord Testers', "['2016-10-28 03:29:24.011000']"),
               ('Kappa | RIP onsWat', "['2017-01-09 06:26:07.514000']"), ('The Coding Den', "['2017-01-30 01:29:08.598000']"),
               ("Jefi's Nest", "['2017-01-04 00:30:54.811000']"), ('RELAY', "['2017-07-10 18:51:26.834000']"),
               ('pokedraft-test', "['2017-02-28 07:41:36.773000']"), ('Super Amazing Kool Ultra Jman Emote Server', "['2017-07-11 07:04:04.884706']"),
               ('Big Fan Squad', "['2017-01-09 06:26:28.571000']"), ('Ｃｈｒｉｓｔｃｏｒｄ', "['2017-01-09 06:26:13.215000']"),
               ('Public FenChat', "['2016-08-31 03:46:34.441000']"), ('翼★', "['2017-04-28 07:20:28.276000']"),
               ('Ice Alliance', "['2017-06-05 03:10:26.548000']"), ('Neko Nation :3', "['2017-01-15 23:18:08.735000']"),
               ('Crescent Moon Prime', "['2017-04-18 05:46:21.966539']"), ('FrankenCord', "['2017-01-04 00:30:50.884000']")], 'rows']
