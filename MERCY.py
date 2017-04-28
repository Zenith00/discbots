import heapq
import logging
import random
import textwrap
from collections import defaultdict

# class Unbuffered(object):
#     def __init__(self, stream):
#         self.stream = stream
#
#     def write(self, data):
#         self.stream.write(data)
#         self.stream.flush()
#
#     def __getattr__(self, attr):
#         return getattr(self.stream, attr)
#
# import sys
#
# sys.stdout = Unbuffered(sys.stdout)

import discord
import motor.motor_asyncio
import pymongo
# import wolframalpha
# from asteval import Interpreter
# import fuzzywuzzy
from fuzzywuzzy import fuzz, process
# from imgurpython import ImgurClient
from pymongo import ReturnDocument
# from simplegist.simplegist import Simplegist
from simplegist.simplegist import Simplegist
from unidecode import unidecode
# import Color
import constants
import TOKENS
from utils.utils_parse import *
from utils.utils_text import *
from utils import utils_image
import dateparser
import os, sys

os.environ["PYTHONUNBUFFERED"] = "True"
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
logging.basicConfig(level=logging.INFO)

# Clients

# imgur = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
#                     IMGUR_REFRESH_TOKEN)
# WA_client = wolframalpha.Client(WA_ID)
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://{usn}:{pwd}@nadir.space".format(usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS))
# mongo_client = motor.motor_asyncio.AsyncIOMotorClient()

overwatch_db = mongo_client.overwatch

auths_collection = overwatch_db.auths
mongo_client_static = pymongo.MongoClient()
# aeval = Interpreter()
gistClient = Simplegist()
# scrim
scrim = None
client = discord.Client()
heatmap = None
temproles = None
id_channel_dict = {}
join_warn = False
ID_ROLENAME_DICT = dict([[v, k] for k, v in constants.ROLENAME_ID_DICT.items()])
BLACKLISTED_CHANNELS = (
    constants.CHANNELNAME_CHANNELID_DICT["bot-log"], constants.CHANNELNAME_CHANNELID_DICT["server-log"],
    constants.CHANNELNAME_CHANNELID_DICT["voice-channel-output"])
SERVERS = {}
CHANNELNAME_CHANNEL_DICT = {}

STATES = {"init": False}


#
# class ScrimTeam:
#     def __init__(self, id, channel):
#         self.members = []
#         self.name = id
#         self.vc = channel
#
# class ScrimMaster:
#     def __init__(self, scr1, scr2, txt, spec, output):
#         self.output = output
#         self.team1 = scr1
#         self.team2 = scr2
#         self.text = txt
#         self.spectate = spec
#         self.masters = []
#
#     async def get_managers(self):
#         managers = []
#         manager_cursor = overwatch_db.scrim.find({"manager": 1})
#         async for manager in manager_cursor:
#             managers.append(manager["userid"])
#
#         return managers
#
#     async def end(self):
#         await client.delete_channel(self.team1.vc)
#         await client.delete_channel(self.team2.vc)
#         await client.delete_channel(self.text)
#         await client.delete_channel(self.spectate)
#         await overwatch_db.scrim.update_many({}, {"$set": {"active": False, "pos": 0, "status": ""}})
#
#     async def assign(self, member, team):
#         await self.deauth(member)
#         return await self.auth(member, team)
#
#     async def reset(self):
#         cursor = overwatch_db.scrim.find({"active": True})
#         server = self.output.server
#         async for person in cursor:
#             await self.deauth(server.get_member(person["userid"]))
#         await overwatch_db.scrim.update_many({"status": "playing"}, {"$set": {"active": False}})
#
#     async def auth(self, member, team):
#         print("Assigning {} to {}".format(member.id, team))
#         if team == "1":
#             target_team = self.team1
#         elif team == "2":  # team == "2":
#             target_team = self.team2
#         else:
#             return
#         # self.members[member.id] = team
#         await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"team": target_team.name}})
#
#         target_team.members.append(member.id)
#         user_overwrite_vc = discord.PermissionOverwrite(connect=True)
#         await client.edit_channel_permissions(target_team.vc, member, user_overwrite_vc)
#         return member.mention + " added to team " + target_team.name
#
#     async def deauth(self, member):
#         if not member:
#             return
#         target_member = await overwatch_db.scrim.find_one({"userid": member.id})
#         if not target_member:
#             print("FAILED TO FIND {}".format(member.id))
#             return
#         if "team" not in target_member.keys():
#             return
#         target = target_member["team"]
#         if target == "1":
#             target_team = self.team1
#         elif target == "2":
#             target_team = self.team2
#         else:
#             return
#         await client.delete_channel_permissions(target_team.vc, member)
#
#     async def force_register(self, message):
#         command_list = message.content.split(" ")
#         print(command_list)
#         print("Registering")
#         await overwatch_db.scrim.update_one({"userid": command_list[5]},
#                                             {"$set": {"rank"  : command_list[3].lower(), "btag": command_list[2],
#                                                       "region": command_list[4], "active": True}}, upsert=True)
#         await scrim.add_user(self.output.server.get_member(command_list[5]))
#
#     async def register(self, message):
#         command_list = message.content.split(" ")
#         await overwatch_db.scrim.update_one({"userid": message.author.id},
#                                             {"$set": {"rank"  : command_list[1].lower(), "btag": command_list[0],
#                                                       "region": command_list[2], "active": True}}, upsert=True)
#         await scrim.add_user(message.author)
#
#     async def serve_scrim_prompt(self, member):
#         user = await overwatch_db.scrim.find_one({"userid": member.id, "btag": {"$exists": True}})
#         if user:
#             confirmation = "Joining scrim as [{region}] {btag} with an SR of {sr}".format(region=user["region"],
#                                                                                           btag=user["btag"],
#                                                                                           sr=user["rank"])
#             await client.send_message(member, confirmation)
#             await scrim.add_user(member)
#         else:
#             await client.send_message(member,
#                                       "Please enter your battletag, highest SR, and region (EU, NA, KR) in the format:\nBattleTag#0000 2500 EU\n or Battletag#00000 unplaced NA")
#
#     async def add_user(self, member):
#         size = 12
#         # base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.DESCENDING)])
#         await self.compress()
#         cursor = overwatch_db.scrim.find({"active": True})
#         count = await cursor.count()
#         print(count)
#
#         await overwatch_db.scrim.update_one({"userid": member.id},
#                                             {"$set": {"active": True, "pos": count, "status": "pending",
#                                                       "team"  : ""}})
#
#         new_joined = await overwatch_db.scrim.find_one({"userid": member.id})
#         cursor = overwatch_db.scrim.find({"active": True})
#         count = await cursor.count()
#         print(count)
#         update = "[{region}] {btag} ({mention}) has joined the scrim with an SR of {sr} ({count}/{size})".format(
#             region=new_joined["region"], btag=new_joined["btag"], mention=member.mention, sr=new_joined["rank"],
#             count=count, size=size)
#         await client.send_message(self.output, update)
#
#     async def start(self):
#         await self.compress()
#
#         overwatch_db.scrim.update_many({"active": True}, {"$set": {"team": "pending"}})
#         # await self.reset()
#         size = 12
#         cursor = overwatch_db.scrim.find({"active": True})
#         count = await cursor.count()
#         if count < size:
#             await client.send_message(self.output,
#                                       "Not enough players: ({count}/{size})".format(count=count, size=size))
#             return
#         else:
#             base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.ASCENDING)])
#             if not base:
#                 print("BLAHAHAHAH")
#                 return
#             if base["pos"] != 1:
#                 print(str(base["pos"]) + " " + base["btag"])
#                 start = 1 - base["pos"]
#                 await overwatch_db.scrim.update_many({"active": True}, {"$inc": {"pos": start}})
#
#             await client.send_message(self.output, "Starting...")
#             await overwatch_db.scrim.update_many({"active": True, "pos": {"$lt": size + 1}},
#                                                  {"$set": {"status": "playing"}})
#             await self.autobalance()
#             await self.output_teams()
#             await overwatch_db.scrim.update_many({"status": "playing"}, {"active": False, "pos": ""})
#             base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.ASCENDING)])
#             if not base:
#                 print("BLAHAHAHAH")
#                 return
#             if base["pos"] != 1:
#                 start = 1 - base["pos"]
#                 await overwatch_db.scrim.update_many({"active": True}, {"$inc": {"pos": start}})
#
#     async def leave(self, member):
#         userid = member.id
#         await overwatch_db.scrim.update_one({"userid": userid},
#                                             {"$set": {"team": "0", "active": False, "manager": 0, "status": "",}})
#         return "Removed " + member.mention + " from the active user pool"
#
#     # async def register(self, member, btag, sr, region):
#     #
#     #     await overwatch_db.scrim.update_one({"userid": member.id},
#     #                                         {"$set": {"rank": sr, "btag": btag, "region": region, "active": True}},
#     #                                         upsert=True)
#
#     async def refresh(self, member):
#         user = await overwatch_db.scrim.find_one({"userid": member.id})
#         await self.register(member, user["btag"])
#
#     async def autobalance(self):
#         server = self.output.server
#
#         cursor = overwatch_db.scrim.find(
#             {"active": True, "status": "playing"},
#             projection=["userid", "rank"])
#
#         cursor.sort("rank", -1)
#         members = await cursor.to_list(None)
#         print(members)
#         counter = 0
#         for user in members:
#             if counter == 4:
#                 counter = 0
#             if counter == 0 or counter == 3:
#                 await scrim.assign(server.get_member(user["userid"]), "1")
#
#             elif counter == 1 or counter == 2:
#                 await scrim.assign(server.get_member(user["userid"]), "2")
#             counter += 1
#         await client.send_message(self.output, "Autobalancing completed")
#
#     async def compress(self):
#         count = 1
#         cursor = overwatch_db.scrim.find({"active": True})
#         cursor.sort("pos", pymongo.ASCENDING)
#         async for item in cursor:
#             print(item)
#             print(count)
#             result = await overwatch_db.scrim.update_one({"userid": item["userid"]}, {"$set": {"pos": count}})
#             print(result.raw_result)
#             count += 1
#
#     async def output_teams_list(self):
#         await self.compress()
#         cursor = overwatch_db.scrim.find({"active": True})
#
#         cursor.sort("pos", pymongo.ASCENDING)
#
#         userlist = [["Name", "Battletag", "SR", "Position"]]
#         async for user in cursor:
#             print(user)
#             user_entry = []
#             try:
#                 user_entry.append(unidecode(self.output.server.get_member(user["userid"]).name))
#             except:
#                 user_entry.append("MISSING")
#
#             user_entry.append(user["btag"])
#             user_entry.append(user["rank"])
#             user_entry.append(str(user["pos"]))
#             userlist.append(user_entry)
#         await send(self.output, userlist, "rows")
#
#     async def output_teams(self):
#         cursor = overwatch_db.scrim.find({"active": True, "status": "playing"})
#         team1 = [["Team 1", "", "", ""], ["Name", "Battletag", "SR", "ID"]]
#         team2 = [["Team 2", "", "", ""], ["Name", "Battletag", "SR", "ID"]]
#         async for user in cursor:
#             team = user["team"]
#
#             if team == "1":
#                 target_team = team1
#             elif team == "2":
#                 target_team = team2
#             else:
#                 print("fail - check teams")
#                 return
#
#             user_entry = []
#
#             user_entry.append(unidecode(self.output.server.get_member(user["userid"]).name))
#             user_entry.append(user["btag"])
#             user_entry.append(user["rank"])
#             user_entry.append(user["userid"])
#             try:
#                 target_team.append(user_entry)
#             except:
#                 print(user)
#         for item in [team1, team2]:
#             await send(destination=self.output, text=item, send_type="rows")

@client.event
async def on_member_remove(member):
    if not STATES["init"]: return
    if member.server.id == constants.OVERWATCH_SERVER_ID:
        await import_to_user_set(member=member, set_name="server_leaves", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_member_ban(member):
    if not STATES["init"]: return
    if member.server.id == constants.OVERWATCH_SERVER_ID:
        await import_to_user_set(member=member, set_name="bans", entry=datetime.utcnow().isoformat(" "))
        await open_ban(member)


@client.event
async def on_member_unban(server, member):
    if not STATES["init"]: return

    if server.id == constants.OVERWATCH_SERVER_ID:
        await import_to_user_set(member=member, set_name="unbans", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_voice_state_update(before, after):
    """
    :type after: discord.Member
    :type before: discord.Member
    """
    pass


# noinspection PyShadowingNames
@client.event
async def on_member_update(before, after):
    """

    :type after: discord.Member
    :type before: discord.Member
    """
    if before.server.id == constants.OVERWATCH_SERVER_ID:
        if before.nick != after.nick:
            await import_to_user_set(member=after, set_name="nicks", entry=after.nick)
        if before.name != after.name:
            await import_to_user_set(member=after, set_name="names", entry=after.nick)
    if before.voice == after.voice:
        await import_user(after)


@client.event
async def on_message_delete(message):
    pass


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    # global INITIALIZED


@client.event
async def on_member_join(member):
    # await add_to_nick_id_list(member)
    if member.server.id == constants.OVERWATCH_SERVER_ID:
        await import_user(member)
        if STATES["init"]:
            role = await temproles.check(member)
            if role:
                await log_automated(
                    "reapplied {role} to {mention}".format(role=role.name if role.mentionable else role.mention,
                                                           mention=member.mention),
                    log_type="autorole")
        age = abs(datetime.utcnow() - member.created_at)
        if age.total_seconds() < 60 * 10 and join_warn:
            await alert(
                "{mention} joined with an age of {age}".format(mention=member.mention, age=format_timedelta(age)))
        check_open_ban = await overwatch_db.userinfo.find_one({"userid": member.id, "banstatus": "open"})
        if check_open_ban:
            await close_ban(member)


# noinspection PyUnusedLocal



@client.event
async def on_message_edit(before, after):
    if before.server.id == constants.OVERWATCH_SERVER_ID:
        auths = await get_auths(after.author)
        if "mod" not in auths:
            await parse_triggers(after)


@client.event
async def on_message(message_in):
    # global VCMess
    # global VCInvite
    # global PATHS
    # global ENABLED
    # global INITIALIZED
    if message_in.server.id == "266279338305912832":
        crown = await get_role(message_in.server, "307400427954110465")
        print("reg")
        print(str(list(role.id for role in message_in.author.roles)))
        if "307400427954110465" in list(role.id for role in message_in.author.roles):
            print("asdasdasdad")
            print(int("%06x" % random.randint(0, 0xFFFFFF), 16))
            await client.edit_role(message_in.server, crown, color=discord.Color(int("%06x" % random.randint(0, 0xFFFFFF), 16)))
        print("asdad")
    if not STATES["init"]:
        print("Ignoring message...")
        return
    if message_in.author.id == client.user.id:
        return
    if message_in.author.id == constants.ZENITH_ID:
        heatmap.register(message_in.author.id, "message", message_in)
    if message_in.server is None:
        def scrim_register(msg):
            content = msg.content
            items = content.split(" ")
            if len(items) == 3 and regex_test(reg_str=r"^\D.{2,12}#\d{4,6}$", string=items[0]) and \
                    regex_test(reg_str=r"^(\d{1,4})|(unplaced)$", string=items[1]) and \
                    regex_test(reg_str=r"^(EU|NA|KR)$", string=items[2]):
                return True

            return False

        if scrim and scrim_register(message_in):
            await scrim.register(message_in)

        await client.send_message(await client.get_user_info(constants.ZENITH_ID),
                                  "[" + message_in.author.name + "]: " + message_in.content)
        return

    auths = await get_auths(message_in.author)
    trigger = ".."

    if message_in.content.startswith(trigger):
        full_command = message_in.content.replace(trigger, "")
        segmented_command = full_command.split(" ", 1)
        command = segmented_command[0]
        params = segmented_command[1] if len(segmented_command) == 2 else None
        await perform_command(command=command, params=params, message_in=message_in)

    if message_in.server.id == constants.OVERWATCH_SERVER_ID:
        # if message_in.content.startswith("`scrim start"):
        #     await scrim_start(message_in)
        #     return
        await import_message(message_in)

        if "mod" not in auths:
            if message_in.author.id not in STATES["trigger_whitelist"]:
                await parse_triggers(message_in)


async def get_auths(member):
    """
    :type member: discord.Member
    """
    author_info = await parse_member_info(member)
    role_whitelist = any(x in [constants.ROLENAME_ID_DICT["TRUSTED_ROLE"], constants.ROLENAME_ID_DICT["MVP_ROLE"]]
                         for x in author_info["role_ids"])

    mods = await get_moderators(member.server)
    auths = set()
    if member.id == constants.ZENITH_ID:
        auths |= {"zenith"}
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"mod"}
    if member in mods:
        auths |= {"mod"}
        auths |= {"warn"}
        auths |= {"trusted"}
    if role_whitelist:
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"lfg"}
    if any(x in "138132942542077952" for x in author_info["role_ids"]):
        auths |= {"mod"}

    if member.server.id == "236343416177295360":
        if "261550254418034688" in [role.id for role in member.roles]:
            auths |= {"host"}
    return auths


async def perform_command(command, params, message_in):
    global STATES
    if params:
        params = await mention_to_id(params.split(" "))
    output = []
    auths = await get_auths(message_in.author)
    called = False
    try:
        # if command == "scrim":
        #     await scrim_manage(message_in)
        if command in ["names", "firstjoins", "mostactive", "channeldist", "superlog", "rebuildnicks", "wa", "reboot",
                       "rebuild", "ui", "userinfo", "ping", "lfg",
                       "serverlog", "timenow", "say", "raw", "getroles", "moveafk", "help", "join", "tag", "tagreg",
                       "userlog", "channeldist", "unmute",
                       "channelinfo", "fixhighlights"]:
            called = True
        # print("Firing...")
        if "zenith" in auths:
            if command == "trustedinfo":
                results = await trusted_analysis()
                output.extend(results)
            elif command == "wipeinvites":
                print("wiping...")
                count = 0
                try:
                    invite_list = await client.invites_from(message_in.server)
                    for invite in invite_list:
                        if invite.inviter.id == client.user.id:
                            print(invite.inviter.name)
                            print(count)
                            count = count + 1
                            await client.delete_invite(invite)
                except:
                    print(traceback.format_exc())
            elif command == "fix":
                for server in client.servers:
                    if server.id != "94882524378968064" and "Overwatch" not in server.name:
                        print(server.name)
                        await client.leave_server(server)
            elif command == "oauth":
                print(discord.utils.oauth_url(client.user.id))
            if command == "togglestatus":
                if message_in.server.me.status == discord.Status.invisible:
                    await client.change_presence(status=discord.Status.online)
                else:
                    await client.change_presence(status=discord.Status.invisible)
            if command == "statusreset":
                await client.change_presence(status=discord.Status.online)

            elif command == "names":
                count = 0
                text = ""
                for member in message_in.server.members:
                    if count >= int(params[0]):
                        break
                    else:
                        count += 1
                    text += member.name + "\n"
                output.append((text, None))

            elif command == "fixhighlights":
                # def check(message):
                #     if message.content:
                #         if regex_test(
                #                 r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)",
                #                 message.content):
                #             return False
                #         else:
                #             return True
                #     else:
                #         return False
                # await client.purge_from(message_in.channel, check=check)
                async for message in client.logs_from(message_in.channel, limit=15000):
                    if message.content:
                        if not regex_test(
                                r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)",
                                message.content):
                            await client.delete_message(message)

            elif command == "mostactive":
                output.append(await generate_activity_hist(message_in))
            elif command == "channelsdist":
                output.append(await generate_user_channel_activity_hist(message_in.server, params[0], gist=True))
            elif command == "superlog":
                await rebuild_logs(message_in)
            elif command == "rebuildnicks":
                await rebuild_nicks(message_in)
            # elif command == "wa":
            #     await wolfram(message_in)
            elif command == "reboot":
                await client.logout()
            elif command == "setv":
                version = params[0]
                await client.change_presence(game=discord.Game(name=version), afk=False)
            elif command == "rebuild":
                count = 0
                memberlist = []
                for member in message_in.server.members:
                    memberlist.append(member)
                for member in memberlist:
                    print(count)
                    count += 1
                    await import_to_user_set(member, "server_joins", member.joined_at.isoformat(" "))
            elif command == "test":
                user = await client.get_user_info(user_id="222941072404381697")
                await client.send_message(user, "Test")
            elif command == "multihist":
                output.append(
                    await generate_multi_user_channel_activity_hist(server=message_in.server, userid_list=params,
                                                                    gist=True))
            elif command == "rebuild_muted_perms":
                muted_perms = discord.PermissionOverwrite()
                muted_perms.connect = False
                muted_perms.speak = False
                muted_perms.mute_members = False
                muted_perms.deafen_members = False
                muted_perms.move_members = False
                muted_perms.use_voice_activation = False
                for channel in message_in.server.channels:
                    if channel.type == discord.ChannelType.voice:
                        await client.edit_channel_permissions(channel,
                                                              await get_role(message_in.server, "110595961490792448"),
                                                              overwrite=muted_perms)
                        print("Applying to...{}".format(channel.name))

        if "trusted" in auths:
            if command == "ui" or command == "userinfo":
                if params:
                    userid = params[0]
                else:
                    userid = message_in.author.id

                embed = await output_user_embed(userid, message_in)
                if embed:
                    await client.send_message(destination=message_in.channel, content=None, embed=embed)
                else:
                    await client.send_message(destination=message_in.channel, content="User not found")
            elif command == "ping":
                print("FIRING PINGER")
                await ping(message_in)

            elif command == "lfg":
                await serve_lfg(message_in)

        if "mod" in auths:
            print(command)
            if command == "getrolemembers":
                role_name = " ".join(params[0:])
                role = await get_role_from_name(message_in.server, role_name)
                print(role)
                role_members = await get_role_members(role)
                member_list = [[unidecode(member.name), member.id] for member in role_members]
                output.append((member_list, "rows"))
            elif command == "purge":
                offset = 1
                dest = client.get_channel(params[0])
                if not dest:
                    offset = 0
                    dest = message_in.server
                await client.delete_message(message_in)
                try:
                    await purge_from(dest=dest, member_id=params[0 + offset], count=int(params[1 + offset]))
                except IndexError:
                    output.append(("Syntax not recognized", None))
            elif command == "fixchannels":
                for channel in message_in.server.channels:
                    channel_id_name = reverse_dict(constants.CHANNELNAME_CHANNELID_DICT)
                    if channel.id in channel_id_name.keys():
                        await client.edit_channel(channel, name=channel_id_name[channel.id])

            elif command == "dumpinfo":
                target = await export_user(params[0])
                rows = [(k, str(v)) for k, v in target.items()]
                print(rows)
                output.append((rows, "rows"))
            elif command == "serverlog":
                result = await overwatch_db.config.find_one({"type": "log"})
                if not params:
                    await client.send_message(message_in.channel, "Server log is currently {state}".format(
                        state="on" if result["server_log"] else "off"))
                else:
                    new_state = parse_bool(params[0])
                    await overwatch_db.config.update_one({"type": "log"}, {"$set": {"server_log": new_state}},
                                                         upsert=True)
                    STATES["server_log"] = new_state
                    await client.send_message(message_in.channel, "Setting server log to {state}".format(
                        state="on" if result["server_log"] else "off"))
            elif command == "joinwarn":
                global join_warn
                join_warn = not join_warn
                await client.send_message(message_in.channel, "Setting join warning to " + str(join_warn))
            elif command == "watcher":
                try:
                    message = await client.get_message(client.get_channel("252976184344838144"), params[0])
                    content = message.content
                except:
                    await client.send_message(message_in.channel, "Message not found")

                id_list = re.findall(r"(?<!\/)\d{18}", content)
                if id_list:
                    pass
                else:
                    await client.send_message(message_in.channel, "Message syntax not recognized")
                    return
                id_list = list(set(id_list))
                await client.send_message(message_in.channel, "**Found Members:**\n<@!" + "> <@!".join(
                    id_list) + ">\n\nWould you like to ban these?")
                answer = (await client.wait_for_message(author=message_in.author, channel=message_in.channel)).content
                answer = parse_bool(answer)
                if answer:
                    for user_id in id_list:
                        await client.http.ban(user_id=user_id, guild_id=message_in.server.id, delete_message_days=7)
                else:
                    await client.send_message(message_in.channel, "Cancelling...")
            elif command == "filter":
                if params[0] == "add":
                    STATES["trigger_whitelist"].add(params[1])
                elif params[0] == "remove":
                    STATES["trigger_whitelist"].remove(params[1])

            elif command == "channelinfo":
                embed = await output_channel_embed(server=message_in.server, channel_name_or_id=" ".join(params))
                if embed:
                    await client.send_message(destination=message_in.channel, content=None, embed=embed)
                else:
                    await client.send_message(destination=message_in.channel, content="Channel not found")
                called = True
            elif command == "jukeskip":
                await skip_jukebox(" ".join(params[1:]), params[0], message_in)
            elif command == "timenow":
                output.append(await output_timenow())
            elif command == "say":
                await serve_say(message_in)  # Give a user perms
            elif command == "raw":
                output.append(await output_message_raw(channel=message_in.channel, message_id=params[0]))
            elif command == "redraw":
                channel = message_in.channel_mentions[0]
                output.append(await output_message_raw(channel=channel, message_id=params[1]))
            elif command == "forceban":
                id = params[0]
                result = await client.http.ban(user_id=id, guild_id=message_in.server.id, delete_message_days=7)
                print(result)
            elif command == "getroles":
                output.append(await output_roles(message_in))
            elif command == "moveafk":
                await move_to_afk(params[0], message_in.server)
            elif command == "help":
                commands_help = await output_command_list(auths=auths)
                output.append(commands_help[0])
                output.append(commands_help[1])
            elif command == "join":
                print("firing joiner")
                output.append(await output_join_link(message_in.server.get_member(params[0])))
            elif command == "find":
                # await output_find_user(message_in)
                raw_params = " ".join(params)
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(
                        await find_user(matching_ident=params[0], find_type="current", server=message_in.server,
                                        count=int(params[1])))
                else:
                    output.append(
                        await find_user(matching_ident=params[0], find_type="current", server=message_in.server))
            elif command == "findall":
                # await output_find_user(message_in)
                raw_params = " ".join(params)
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(
                        await find_user(matching_ident=params[0], find_type="history", server=message_in.server,
                                        count=int(params[1])))
                else:
                    output.append(
                        await find_user(matching_ident=params[0], find_type="history", server=message_in.server))

            elif command == "findban":
                raw_params = " ".join(params)
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(await find_user(matching_ident=params[0], find_type="bans", server=message_in.server,
                                                  count=int(params[1])))
                else:
                    output.append(await find_user(matching_ident=params[0], find_type="bans", server=message_in.server))


            elif command == "tag":
                await tag_str(trigger=" ".join(params), message=message_in, regex=False)
            elif command == "tagreg":
                await tag_str(trigger=" ".join(params), message=message_in, regex=True)
            elif command == "userlogs":
                output.append(await output_logs(userid=params[0], count=params[1], message_in=message_in))
            elif command == "channeldist":
                output.append(await output_channel_dist(message_in.channel, params[0]))
            elif command == "firstmsgs":
                output.append(await output_first_messages(userid=params[0], message_in=message_in))
            elif command == "unmute":
                member = message_in.server.get_member(params[0])
                await unmute(member)
            elif command == "id":
                pass
            elif command == "unban":
                user_id = params[0]
                user = await client.get_user_info(user_id)
                await client.unban(message_in.server, user)
                output.append(("Unbanned: {mention}".format(mention="<@!" + user_id + ">"), None))

            elif command == "temprole":
                global temproles
                if params[0] in ["add", "+"]:
                    member = message_in.server.get_member(params[1])
                    role_name = ""
                    role = None
                    duration = ""
                    for param in params[2:]:
                        if not role:
                            print(role_name)
                            role_name += param
                            role = await get_role_from_name(message_in.server, role_name)
                        else:
                            print("FOUND:")
                            print(role.name)
                            duration += param
                    if not role:
                        await client.send_message(message_in.channel, "Role not recognized")
                        return
                    time_dict = await parse_time_to_end(duration)
                    if not time_dict:
                        await client.send_message(message_in.channel, "Duration not recognized")
                        return
                    text = "Adding role {rolename} to {mention} [{id}] for {dur}".format(rolename=role.mention,
                                                                                         mention=member.mention,
                                                                                         id=member.id,
                                                                                         dur=time_dict["readable"])
                    text = await scrub_text(text, message_in.channel)
                    await temproles.add_role(member=member, role=role, end_dict=time_dict)
                    output.append((text, None))
                if params[0] in ["remove", "-"]:
                    member = message_in.server.get_member(params[1])
                    await temproles.clear_member(member)

                if params[0] == "tick":
                    await temproles.tick()
                if params[0] == "list":
                    roles = [["Member ID", "Member Name", "Role Name", "Role ID", "Ending in"]]
                    temproles_dump = await temproles.dump()
                    for temprole_dict in temproles_dump:
                        # return {"member_id": self.member_id, "role": self.role, "end": self.end, "server": self.server}
                        member = message_in.server.get_member(temprole_dict["member_id"])
                        role = temprole_dict["role"]
                        end_time = temprole_dict["end"] - datetime.now()
                        end_time = format_timedelta(end_time)
                        if not (member and role and end_time):
                            continue
                        role_entry = [member.id, member.name + "#" + member.discriminator, role.name, role.id, end_time]
                        roles.append(role_entry)
                    await send(destination=message_in.channel, text=roles, send_type="rows")
            elif command == "channelmute":
                type = params[0]
                channel_name = " ".join(params[1:])
                channel = await get_channel_from_name(server=message_in.server, channel_name=channel_name, type=None)
                if channel:
                    for member in channel.voice_members:
                        if type == "+":
                            await client.server_voice_state(member, mute=True)
                        else:
                            await client.server_voice_state(member, mute=False)

            elif command == "mute":
                role = await get_role(message_in.server, "110595961490792448")
                member = message_in.server.get_member(params[0])
                time_dict = await parse_time_to_end(" ".join(params[1:]))
                if not member:
                    member = await client.get_user_info(params[0])
                    if not member:
                        await client.send_message(message_in.channel, "User not recognized")
                        return
                    await client.send_message(message_in.channel, "User is not a member. Applying pre-emptive mute...")
                if not time_dict:
                    await client.send_message(message_in.channel, "Duration not recognized")
                    return
                output.append(("Muting {mention} [{id}] for {dur}".format(mention=member.mention, id=member.id,
                                                                          dur=time_dict["readable"]), None))
                await temproles.add_role(member=member, role=role, end_dict=time_dict)
            elif command == "massban":
                print("CALLING")
                start = params[0]
                end = params[1]
                server_log = overwatch_db.server_log
                start_doc = await server_log.find_one({"action": "join", "id": start})
                end_doc = await server_log.find_one({"action": "join", "id": end})
                print(start_doc)
                print(end_doc)
                base_date = dateparser.parse(start_doc["date"])
                threshold = " ".join(params[2:])
                dur = await parse_time_to_end(threshold)
                dur = dur["duration"].total_seconds()

                cursor = server_log.find(
                    {"action": "join", "date": {"$gte": start_doc["date"], "$lte": end_doc["date"]}})
                async for document in cursor:
                    doc_date = parse_date(document["date"])
                    delta = doc_date - base_date
                    delta = abs(delta.to_seconds())
                    print(delta)
                    if delta < dur:
                        print(document["id"])
                        # result = await client.http.ban(user_id=document["id"], guild_id=message_in.server.id, delete_message_days=7)
            elif command == "remindme":
                member = message_in.author
                raw = " ".join(params)

                time_dict = await parse_time_to_end(raw.split(",")[-1])
                await asyncio.sleep(time_dict["duration"].total_seconds())

                await client.send_message(message_in.channel,
                                          "{}, reminding you after {}: `{}`".format(message_in.author.mention,
                                                                                    time_dict["readable"],
                                                                                    raw.split(",")[0]))

        if "trusted" not in auths:
            return
        if called:
            await client.delete_message(message_in)
        if output:
            for item in output:
                await send(destination=message_in.channel, text=item[0], send_type=item[1])
    except:
        print(traceback.format_exc())


async def unmute(member):
    await client.server_voice_state(member, mute=False)


async def parse_time_to_end(time_string):
    print(time_string)
    try:
        if is_int(time_string):
            delt = timedelta(minutes=int(time_string))
            delt = round_timedelta(delt)
            readable = format_timedelta(delt)
            return {"end": datetime.now() + delt, "duration": delt, "readable": readable}
        else:
            end = dateparser.parse("in " + time_string)
            delt = end - datetime.now()
            delt = round_timedelta(delt)
            readable = format_timedelta(delt)
            return {"end": end, "duration": delt, "readable": readable}
    except:
        print(traceback.format_exc())
        return None


async def skip_jukebox(song_name, member_id, message_in):
    jukebox = client.get_server(constants.OVERWATCH_SERVER_ID).get_channel(
        constants.CHANNELNAME_CHANNELID_DICT["jukebox"])
    await client.send_message(jukebox,
                              "Skipping song `{songname}`, {mention}".format(songname=song_name.replace("`", ""),
                                                                             mention=message_in.author.mention))
    target_member = message_in.server.get_member(member_id)

    def check(msg):
        if not regex_test(r"<@!?{id}>".format(id=member_id), msg.content):
            return False
        if msg.author.id != "248841864831041547":
            return False

        match = re.search(r"(?<=your song \*\*)(.+?)(?=\*\* is now playing in ♫ Jukebox!)", msg.content)
        if match:
            song_title = match.group(0)

            if int(fuzz.ratio(song_name.lower(), song_title.lower())) > 85:
                return True
        return False

    await client.wait_for_message(channel=jukebox, check=check)
    await client.send_message(jukebox, ".skip")


async def serve_say(message_in):
    command = message_in.content.replace("`say ", "")
    command_list = command.split(" | ")
    await client.delete_message(message_in)
    if len(command_list) == 1:
        await client.send_message(message_in.channel, command_list[0])
    else:
        await client.send_message(message_in.channel_mentions[0], command_list[1])


async def output_timenow():
    return (await get_redirected_url("http://imgs.xkcd.com/comics/now.png"), None)


async def output_message_raw(channel, message_id):
    text = (await client.get_message(channel, message_id)).content
    text = text.replace("```", "")
    return ("```{text}```".format(text=text), None)


async def move_to_afk(user, server):
    target = server.get_member(user)
    afk = server.get_channel("94939166399270912")
    await client.move_member(target, afk)


async def output_find_user(message_in):
    command = message_in.content[7:]
    command = command.lower()
    command = command.split("|", 2)
    await fuzzy_match(message_in, *command)


async def output_join_link(member):
    vc = member.voice.voice_channel
    try:
        invite = await client.create_invite(vc, max_uses=1, max_age=6, unique=False)
    except:
        return ("Error generating invite link...", None)
    print("Creating Invite...")
    if invite:
        return (invite.url, None)
    else:
        return ("User not in a visible voice channel", None)


async def purge_from(dest, member_id, count):
    print(dest.name)
    print(member_id)
    print(count)

    def check(msg):
        nonlocal count
        if msg.author.id == member_id and count > 0:
            count -= 1
            return True

    if isinstance(dest, discord.Server):
        for channel in [dest for dest in dest.channels if dest.type == discord.ChannelType.text]:
            try:
                print("Purging from {name}".format(name=channel.name))
                await client.purge_from(channel=channel, check=check)
            except:
                pass
    else:
        print("Purging from {name}".format(name=dest.name))
        await client.purge_from(channel=dest, check=check)


async def output_channel_embed(server, channel_name_or_id):
    channel_name_or_id = channel_name_or_id.strip()
    channel = client.get_channel(channel_name_or_id)
    if not channel:
        channel = await get_channel_from_name(server=server, channel_name=channel_name_or_id, type=None)
    if not channel:
        return None
    name = "   ".join(w.capitalize() for w in channel.name.split("-"))
    embed = discord.Embed(title="{channelname}  info".format(channelname=name) + ' ' * 180 + "​​​​​​")

    embed.add_field(name="ID", value=channel.id, inline=True)
    embed.add_field(name="Position", value=channel.position, inline=True)
    embed.add_field(name="Creation", value=channel.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Type", value=str(channel.type), inline=False)
    if channel.topic:
        embed.add_field(name="Topic", value=channel.topic, inline=False)
    if channel.type == discord.ChannelType.text:
        embed.set_thumbnail(url="http://i.imgur.com/AAwO8W4.png")
    if channel.type == discord.ChannelType.voice:
        embed.add_field(name="Bitrate", value=str(int(float(channel.bitrate) / 1000)) + " kbps", inline=True)
        embed.add_field(name="User Limit", value=str(channel.user_limit), inline=True)
        embed.set_thumbnail(url="http://i.imgur.com/imQSkaz.png")
    # for overwrite in channel.overwrites:
    #
    #     embed.add_field(name=overwrite[0].name)
    #     print(str(overwrite[0].name))
    #     pair = overwrite[1].pair()
    #     print(pair[0])
    #     print(pair[1])
    return embed


async def output_user_embed(member_id, message_in):
    # target_member = message_in.author
    target_member = message_in.server.get_member(member_id)
    if not target_member:
        target_member = await client.get_user_info(member_id)
    if not target_member:
        target_member = message_in.author

    user_dict = await export_user(target_member.id)

    embed = discord.Embed(title="{name}#{discrim}'s userinfo".format(name=target_member.name,
                                                                     discrim=str(target_member.discriminator)),
                          type="rich")

    # avatar_link = shorten_link(target_member.avatar_url)

    avatar_link = target_member.avatar_url

    # color = "0x" + color


    embed.add_field(name="ID", value=target_member.id, inline=True)
    if user_dict:
        if "server_joins" in user_dict.keys():
            server_joins = user_dict["server_joins"]
            server_joins = [join[:10] for join in server_joins]

            embed.add_field(name="First Join", value=server_joins[0], inline=True)
        if "bans" in user_dict.keys():
            bans = user_dict["bans"]
            bans = [ban[:10] for ban in bans]
            bans = str(bans)[1:-1]
            embed.add_field(name="Bans", value=bans, inline=True)
        if "unbans" in user_dict.keys():
            unbans = user_dict["unbans"]
            unbans = [unban[:10] for unban in unbans]
            unbans = str(unbans)[1:-1]
            embed.add_field(name="Unbans", value=unbans, inline=True)
    embed.add_field(name="Creation", value=target_member.created_at.strftime("%B %d, %Y"), inline=True)

    if isinstance(target_member, discord.Member):
        roles = [role.name for role in target_member.roles][1:]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles), inline=True)
        voice = target_member.voice
        if voice.voice_channel:
            voice_name = voice.voice_channel.name
            embed.add_field(name="Current VC", value=voice_name)
        status = str(target_member.status)
    else:
        if target_member in await client.get_bans(message_in.server):
            status = "Banned"
        else:
            status = "Not part of the server"
    embed.add_field(name="Status", value=status, inline=False)
    if avatar_link:
        embed.set_thumbnail(url=avatar_link)
        color = utils_image.average_color_url(avatar_link)
        embed.add_field(name="Avatar", value=avatar_link.replace(".webp", ".png"), inline=False)
        hex_int = int(color, 16)
        embed.colour = discord.Colour(hex_int)
        embed.set_thumbnail(url=target_member.avatar_url)
    return embed


async def serve_lfg(message_in):
    found_message = None
    warn_user = None
    if len(message_in.mentions) == 0:
        found_message = await finder(message=message_in, regex=constants.LFG_REGEX, blacklist="mod")
    else:
        warn_user = message_in.mentions[0]
    # await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
    #                           "`lfg called by " + message_in.author.name)
    await lfg_warner(found_message=found_message, warn_type="targeted", warn_user=warn_user,
                     channel=message_in.channel)
    await client.delete_message(message_in)


async def ping(message):
    """
    :type message: discord.Message
    """
    timestamp = message.timestamp
    channel = message.channel
    # await client.delete_message(message)
    if message.author.id == "90302230506258432":
        voice = message.author.mention + " HAMMERDOWN!!"
    elif message.author.id == "106391128718245888":
        voice = message.author.mention + " Let's break it DOWN!"
    elif message.author.id == "66093947541266432":
        voice = message.author.mention + " ¡Apagando las luces!"
    elif message.author.id == "126861133955989504":
        voice = message.author.mention + " Put your faith in the light!"
    elif message.author.id == "103057791312203776":
        voice = message.author.mention + " Cheers Love! The Cavalry's Here!"
    elif message.author.id == constants.ZENITH_ID:
        voice = message.author.mention + " Test"
    else:
        voice = message.author.mention + " " + random.choice(constants.VOICE_LINES)

    sent = await client.send_message(channel, voice)
    await client.edit_message(sent,
                              voice + " (" + str(
                                  (sent.timestamp - timestamp).total_seconds() * 500) + " ms)")


async def output_roles(message):
    role_list = []
    role_list.append(["Name", "ID", "Position", "Color", "Hoisted", "Mentionable"])
    for role in message.server.role_hierarchy:
        new_entry = [role.name, str(role.id), str(role.position), str(role.colour.to_tuple()), str(role.hoist),
                     str(role.mentionable)]
        role_list.append(new_entry)
    return (role_list, "rows")


async def output_command_list(auths):
    commands = [["Command", "Params", "Description", "Note"],
                ["timenow", "", "Outputs a radial world map with timezones", ""],
                ["say", "<channel> | <text>", "Outputs <text> to <channel>", ""],
                ["raw", "<messageid>", "Outputs the raw text from a message", ""],
                ["getroles", "", "Outputs a list of [Role Name, ID, Position, Color, Hoist, Mentionable]", ""],
                ["moveafk", "<mention/id>", "Moves the user to the AFK channel", ""],
                ["tag", "<str>", "Begins blacklist process for <str>", "+"],
                ["ui", "<mention/id>", "Outputs userinfo for the user", ""],
                ["join", "<mention/id>", "Outputs a VC link to the user's voice channel", ""],
                ["userlogs", "<mention/id> <count>", "Outputs <count> messages from user", "-"],
                ["ping", "", "Gives M3R-CY's current ping", ""],
                ["lfg", "*<mention/id>", "Outputs the automated LFG warner", ""],
                ["firstmsgs", "<mention/id>", "Outputs the first 50 messages of user", ""],
                ["serverlog", "<on/off>", "Enables or disables the server log", ""],
                ["channelinfo", "<channelname/id>", "Outputs information about the channel"]]

    notes = "```*Optional\n+Requires additional input\n-Slow```"
    output = [
        (commands, "rows"),
        (notes, None)
    ]
    return output


async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members


async def get_moderators(server):
    users = []
    for role in server.roles:
        if role.permissions.manage_roles or role.permissions.ban_members:
            members = await get_role_members(role)
            users.extend(members)
    return users


async def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x


async def trusted_analysis():
    ow = SERVERS["OW"]
    trusted = await get_role(ow, "169728613216813056")
    trusteds = await get_role_members(trusted)
    gists = []
    for member in trusteds:
        try:
            result = await generate_user_channel_activity_hist(ow, member.id, False)
            gists[ascii(member.name)] = result
        except:
            print(member.name)
    return [(gist, None) for gist in gists]


async def get_channel_from_name(server, channel_name, type):
    channelname_channel_dict = {}
    for channel in server.channels:
        if not type or channel.type == type:
            channelname_channel_dict[channel.name] = channel
    channel = process.extractOne(channel_name, list(channelname_channel_dict.keys()))
    if channel[1] > 85:
        return channelname_channel_dict[channel[0]]
    else:
        return None


async def get_role_from_name(server, role_name):
    rolename_role_dict = {}
    for role in server.roles:
        rolename_role_dict[role.name] = role

    role = process.extractOne(role_name, list(rolename_role_dict.keys()))
    print(role)
    if role[1] > 90:
        return rolename_role_dict[role[0]]
    else:
        return None


# Tagging
async def add_tag(string, note, action, categories):
    await overwatch_db.trigger_str_collection.update_one({"string": string}, {
        "$addtoset": {"actions": action,
                      "note": note,
                      "categories": {"$each": categories}}})


async def tag_str(trigger, message, regex):
    if not regex:
        trigger = re.escape(trigger)

    # if overwatch_db.trigger_str_collection.find_one({"trigger": string}):
    #     await tag_update(message)
    #     return

    # if string == "reset":
    #     await overwatch_db.trigger_str_collection.remove({})
    #     await overwatch_db.trigger_str_collection.create_index([("trigger", pymongo.DESCENDING)], unique=True)
    #     return

    interact = await client.send_message(message.channel,
                                         "Tagging string: \n `{trigger}`\nShould I match whole words only? \n (yes/no)".format(
                                             trigger=trigger))
    answer = (await client.wait_for_message(author=message.author, channel=message.channel)).content

    bounded = parse_bool(answer)

    await client.send_message(message.channel,
                              "Registering `{trigger}` as a{bounded}bounded string".format(trigger=trigger,
                                                                                           bounded=" " if bounded else "n un"))

    trigger = "{b}{trigger}{b}".format(b=r"\b" if bounded else "", trigger=trigger)

    await client.send_message(message.channel,
                              "What actions should I take? (kick, delete, alert)")
    action_response = (await client.wait_for_message(author=message.author, channel=message.channel)).content
    action_response = " ".join((await mention_to_id(action_response.split(" "))))
    action_response = action_response.split("&")
    actions = []
    for action in action_response:
        action_list = action.split(" ", 1)

        if action_list[0] in ["kick", "delete", "alert"]:
            if len(action_list) == 1:
                note = "containing the {b}bounded string {trigger}".format(b="" if bounded else "un", trigger=trigger[
                                                                                                              2:-2] if bounded else trigger)
            else:
                note = action_list[1]
            result = await overwatch_db.trigger_str_collection.insert_one(
                {"trigger": trigger, "action": action_list[0], "note": note})
        if action_list[0] == "mute":
            if len(action_list) == 2:
                note = "containing the string {}".format(trigger)
            else:
                note = action_list[2]
            action_list = (" ".join(action_list)).split(" ", 2)
            await overwatch_db.trigger_str_collection.insert_one(
                {"trigger": trigger, "action": action_list[0], "duration": action_list[1], "note": action_list[2]})



            #
            # else:
            #     await client.edit_message(interact, "Syntax not recognized. Please restart")
            #     return
            #     # result = await overwatch_db.trigger_str_collection.insert_one(database_entry)
            #     # print(result)


async def parse_triggers(message) -> list:
    response_docs = []
    content = unidecode(strip_markdown(message.content))
    # trigger_cursor = overwatch_db.trigger_str_collection.find()
    # trigger_dict = await trigger_cursor.to_list()
    # trigger_list = [item["trigger"] for item in trigger_dict]
    # print("Parsing triggers for " + content)
    async for doc in overwatch_db.trigger_str_collection.find():

        if regex_test(doc["trigger"], content):
            print("Found: " + doc["trigger"])
            response_docs.append(doc)

    match = re.search(constants.INVITE_REGEX, content)

    if match:
        inv_link = match.group(0)
        try:
            invite = await client.get_invite(inv_link)
            if invite.server.id == message.server.id:
                if message.channel.id in [constants.CHANNELNAME_CHANNELID_DICT["general-discussion"],
                                          constants.CHANNELNAME_CHANNELID_DICT["overwatch-discussion"]]:
                    party = re.search(r"(^\[)\w+.\w+\]", invite.channel.name, flags=re.IGNORECASE)
                    if party:
                        response_docs.append({"action": "delete",
                                              "note": "Please keep LFGs to <#182420486582435840> <#185665683009306625>"})
            else:
                response_docs.append({"action": "external_invite", "invite": invite,
                                      "note": "Please don't link other discord servers here"})
        except discord.errors.NotFound:
            pass

    await act_triggers(response_docs, message)


async def act_triggers(response_docs, message):
    for doc in response_docs:
        try:
            if doc["action"] == "delete":
                await log_automated("deleted {author}'s message from {channel} ```{content}``` because: {note}".format(
                    author=message.author.mention, content=message.content.replace("```", "").replace("`", ""),
                    channel=message.channel.mention, note=doc["note"]), "deletion")
                await client.delete_message(message)

            if doc["action"] == "kick":
                # await client.kick(message.author)
                await log_automated("kicked {author} because of the message ```{content}```because: {note}".format(
                    author=message.author.mention, content=message.content.replace("```", ""), note=doc["note"]),
                    "action")
            if doc["action"] == "alert":
                await log_automated("registered {author}'s message ```{content}```because: {note}".format(
                    author=message.author.mention, content=message.content.replace("```", ""), note=doc["note"]),
                    "alert")
            if doc["action"] == "mute":
                pass
            if doc["action"] == "external_invite":
                await log_automated(
                    "deleted {author}'s message from {channel} ```Invite to {server_name}``` because: {note}".format(
                        author=message.author.mention,
                        channel=message.channel.mention,
                        server_name=doc["invite"].server.name,
                        note=doc["note"]), "deletion")
                # await log_automated(
                #     "deleted an external invite to " + str(doc["invite"].url) + " from " + message.author.mention + " in " + message.channel.mention, "alert")
                await client.delete_message(message)
        except (discord.Forbidden, discord.HTTPException):
            print(traceback.format_exc())


# Log Based
async def output_logs(userid, count, message_in):
    cursor = overwatch_db.message_log.find({"userid": userid}, limit=int(count))
    cursor.sort("date", -1)
    message_list = []
    count = 0
    async for message_dict in cursor:
        if count % 500 == 0:
            print(count)
        count += 1
        message_list.append(await format_message_to_log(message_dict))
    if count == 0:
        return ("No logs found", None)

    if message_list:
        gist = gistClient.create(name="User Log", description=(await client.get_user_info(userid)).name + "'s Logs",
                                 public=False,
                                 content="\n".join(message_list))
        return (gist["Gist-Link"], None)
    else:
        return ("No logs found", None)


async def output_first_messages(userid, message_in):
    member = message_in.server.get_member(userid)
    cursor = overwatch_db.message_log.find({"userid": userid}, limit=50)
    cursor.sort("date", 1)
    message_list = []
    async for message_dict in cursor:
        message_list.append(await format_message_to_log(message_dict))

    logs = message_list
    gist = gistClient.create(name="First Messages",
                             description=userid if not member else member.name + "'s First Messages",
                             public=False,
                             content="\n".join(logs))
    return (gist["Gist-Link"], None)


async def rebuild_logs(message_in):
    server = message_in.server
    # await client.delete_message(message_in)
    for channel in server.channels:
        count = 0
        async for retrieved_message in client.logs_from(channel, limit=1000000000000):
            if count % 100 == 0:
                print("Message got " + str(count))
            await import_message(retrieved_message)
            count += 1


async def rebuild_nicks(message_in):
    memberlist = []
    for member in message_in.server.members:
        memberlist.append(member)
    for member in memberlist:
        print(member.name)
        await import_user(member)


async def generate_user_channel_activity_hist(server, userid, gist=False):
    hist = defaultdict(int)
    member_name = server.get_member(userid).name
    async for doc in overwatch_db.message_log.find({"userid": userid, "date": {"$gt": "2017-01-25"}}):
        hist[doc["channel_id"]] += len(doc["content"].split(" "))
        hist["Total"] += len(doc["content"].split(" "))
        print("Found a message from " + str(doc["userid"]))
    named_hist = {}
    hist = dict(hist)
    for key in hist.keys():
        try:
            named_hist[constants.CHANNELID_CHANNELNAME_DICT[key]] = hist[key]
        except:
            try:
                name = server.get_channel(key).name
                named_hist[name] = hist[key]
            except:
                name = key
                named_hist[name] = hist[key]
    if not gist:
        return hist

    sort = sorted(named_hist.items(), key=lambda x: x[1])
    hist = "\n".join("%s,%s" % tup for tup in sort)
    if hist:
        gist_response = gistClient.create(name=member_name + "'s Channelhist",
                                          description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                          public=False,
                                          content=hist)
    else:
        return

    return (gist_response["Gist-Link"], None)


async def generate_multi_user_channel_activity_hist(server, userid_list, gist=False):
    text = "ID, Name, Total, 109672661671505920, 106091034852794368, 152757147288076297, 200185170249252865, 188949683589218304, 182420486582435840, 233904315247362048, 95324409270636544, 241964387609477120, 170983565146849280, 184770081333444608, 170185225526181890, 94882524378968064, 177136656846028801, 185665683009306625, 168567769573490688, 107255001163788288, 180471683759472640, 95632031966310400, 209609220084072450, 176236425384034304, 174457179850539009, 170179130694828032, 147153976687591424, 240320691868663809, 252976184344838144"
    for userid in userid_list:
        print("Parsing... {}".format(userid))
        hist = defaultdict(int)
        member_name = server.get_member(userid).name
        async for doc in overwatch_db.message_log.find(
                {"userid": userid, "date": {"$gt": (datetime.utcnow() - timedelta(days=30)).isoformat(" ")}}):
            hist[doc["channel_id"]] += len(doc["content"].split(" "))
            hist["Total"] += len(doc["content"].split(" "))
            # print("Found a message from " + str(doc["userid"]))
        text += "\n " + userid + ", " + member_name + ", "
        for column in ["Total", "109672661671505920",
                       "106091034852794368",
                       "152757147288076297",
                       "200185170249252865",
                       "188949683589218304",
                       "182420486582435840",
                       "233904315247362048",
                       "95324409270636544",
                       "241964387609477120",
                       "170983565146849280",
                       "184770081333444608",
                       "170185225526181890",
                       "94882524378968064",
                       "177136656846028801",
                       "185665683009306625",
                       "168567769573490688",
                       "107255001163788288",
                       "180471683759472640",
                       "95632031966310400",
                       "209609220084072450",
                       "176236425384034304",
                       "174457179850539009",
                       "170179130694828032",
                       "147153976687591424",
                       "240320691868663809",
                       "252976184344838144"]:
            text += str(hist[column]) + ", "
    gist_response = gistClient.create(name="Multhist of " + str(userid_list),
                                      description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                      public=False,
                                      content=text)
    return (gist_response["Gist-Link"], None)


async def generate_activity_hist(message):
    if message.content.startswith("`mostactive"):
        print("STARTING")
        activity = defaultdict(int)
        count = 0
        async for mess in overwatch_db.message_log.find({"date": {"$gt": "2016-11-18"}}):
            content = mess["content"]
            length = len(content.split(" "))
            activity[mess["userid"]] += length
            count += 1
            print(count)

        activity = dict(activity)
        newactivity = {}
        for ID in activity.keys():
            try:
                info = await export_user(ID)
                name = info["names"][-1]
                print("querying")
            except:
                print("reverting to server")
                try:
                    name = message.server.get_member(ID).name
                except:
                    print("reverting to user")
                    try:
                        name = client.get_user_info(ID).name
                    except:
                        name = ID
            newactivity[name] = activity[ID]

        sort = sorted(newactivity.items(), key=lambda x: x[1])
        print(sort)
        hist = "\n".join("%s,%s" % tup for tup in sort)

        gist = gistClient.create(name="Userhist",
                                 description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                 public=False,
                                 content=hist)
        return (gist["Gist-Link"], None)


async def format_message_to_log(message_dict):
    cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
    try:
        name = cursor["names"][-1]
        if not name:
            name = cursor["names"][-2]
    except:
        try:
            await import_user(SERVERS["OW"].get_member(message_dict["userid"]))
            cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
            name = cursor["names"][-1]
        except:
            name = message_dict["userid"]
        if not name:
            name = message_dict["userid"]

    try:
        content = message_dict["content"].replace("```", "")
        try:
            channel_name = constants.CHANNELID_CHANNELNAME_DICT[str(message_dict["channel_id"])]
        except KeyError:
            channel_name = "Unknown"

        return "[" + message_dict["date"][:19] + "][" + channel_name + "][" + str(name) + "]:" + content

    except:
        print(traceback.format_exc())
        return "Errored Message : " + str(message_dict)


async def output_channel_dist(channel, days):
    activity = defaultdict(int)
    count = 0
    date = datetime.utcnow() - timedelta(days=int(days))
    date = date.isoformat(" ")
    print(date)
    async for mess in overwatch_db.message_log.find({"date": {"$gt": date}, "channel_id": channel.id}):
        activity[mess["userid"]] += len(mess["content"].split(" "))
        print(mess["date"])
        print(mess["channel_id"])
        print(count)
        count += 1
    newactivity = dict(activity)
    newact = {}
    for key in newactivity.keys():
        member = channel.server.get_member(key)
        if member:
            name = member.name
        else:
            name = key
        newact[name] = newactivity[key]
    sort = sorted(newact.items(), key=lambda x: x[1], reverse=True)

    hist = "\n".join("%s,%s" % tup for tup in sort)

    gist = gistClient.create(name="Userhist",
                             description="Words sent, Last month",
                             public=False,
                             content=hist)
    return (gist["Gist-Link"], None)


async def log_automated(description: object, log_type) -> None:
    action = ("At " + str(datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S] ")) + ", I automatically " + str(description))
    if log_type == "alert" or log_type == "autorole":
        target = constants.CHANNELNAME_CHANNELID_DICT["alerts"]
    elif log_type == "deletion":
        target = constants.CHANNELNAME_CHANNELID_DICT["bot-log"]

    else:
        target = constants.CHANNELNAME_CHANNELID_DICT["spam-channel"]
    await client.send_message(client.get_channel(target), action)


async def alert(text):
    text = "At " + str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S], ")) + text
    await client.send_message(client.get_channel("252976184344838144"), text)


# Database
# Database Query
async def import_message(mess):
    messInfo = await parse_message_info(mess)
    try:
        await overwatch_db.message_log.insert_one(messInfo)
    except:
        pass


async def import_to_user_set(member, set_name, entry):
    await overwatch_db.userinfo.update_one(
        {"userid": member.id},
        {
            "$addToSet": {set_name: entry}
        }
    )


async def import_user(member):
    user_info = await parse_member_info(member)
    result = await overwatch_db.userinfo.update_one(
        {"userid": member.id},
        {
            "$addToSet": {"nicks": {
                "$each": [user_info["nick"], user_info["name"], user_info["name"] + "#" + str(user_info["discrim"])]},
                "names": user_info["name"],
                "avatar_urls": user_info["avatar_url"],
                "server_joins": user_info["joined_at"]},
            "$set": {"mention_str": user_info["mention_str"],
                     "created_at": user_info["created_at"]},

        }
        , upsert=True
    )
    pass


async def export_user(member_id):
    """

    :type member: discord.Member
    """
    userinfo = await overwatch_db.userinfo.find_one(
        {"userid": member_id}, projection={"_id": False, "mention_str": False, "avatar_urls": False, "lfg_count": False}
    )
    if not userinfo:
        return None
    return userinfo


async def send(destination, text, send_type, delete_in=0):
    if isinstance(destination, str):
        destination = await client.get_channel(destination)

    if send_type == "rows":
        print("FIRING")
        message_list = format_rows(text)
        for message in message_list:
            try:
                await client.send_message(destination, "```" + message.rstrip() + "```")
            except:
                print(message.rstrip())
                print(len(message.rstrip()))
                print(traceback.format_exc())
        return
    if send_type == "list":
        text = str(text)[1:-1]

    text = str(text)
    text = text.replace("\n", "<NL<")
    lines = textwrap.wrap(text, 1500, break_long_words=False)

    for line in lines:
        if len(line) > 1500:
            continue
        line = line.replace("<NL<", "\n")
        await client.send_message(destination, line)


async def mention_to_id(command_list):
    """

    :type command: list
    """
    new_command = []
    reg = re.compile(r"<[@#](!?)\d*>", re.IGNORECASE)
    for item in command_list:
        match = reg.search(item)
        if match is None:
            new_command.append(item)
        else:
            idmatch = re.compile(r"\d")
            id_chars = "".join(idmatch.findall(item))
            new_command.append(id_chars)
    return new_command


async def invite_checker(message, regex_match):
    try:
        invite = await client.get_invite(str(regex_match.group(1)))
        if invite.server.id != constants.OVERWATCH_SERVER_ID:
            channel = message.channel
            # warn = await client.send_message(message.channel,
            #                                  "Please don't link other discord servers here " + message.author.mention)
            # await log_action()
            await act_triggers(response_docs=[{"note": "External server invite", "action": "delete"}], message=message)
            # await client.delete_message(message)
            await log_automated("deleted an external invite to " + str(
                invite.url) + " from " + message.author.mention + " in " + message.channel.mention, "alert")
            skycoder_mess = await client.send_message(
                CHANNELNAME_CHANNEL_DICT["spam-channel"],
                "~an " + message.author.mention +
                " AUTOMATED: Posted a link to another server")
            await client.send_message(skycoder_mess.channel, "~rn " + message.author.mention)
        elif message.channel == CHANNELNAME_CHANNEL_DICT["general-discussion"] or message.channel == \
                CHANNELNAME_CHANNEL_DICT["overwatch-discussion"]:

            channel_name = invite.channel.name
            party_vc_reg = re.compile(r"(^\[)\w+.\w+\]", re.IGNORECASE)
            match = party_vc_reg.search(channel_name)
            if match is not None:
                await lfg_warner(found_message=message, warn_type="automated", warn_user=message.author,
                                 channel=message.channel)
                await client.delete_message(message)
    except discord.errors.NotFound:
        pass
    except:
        print(traceback.format_exc())


async def closest_mention(username_with_discrim):
    pass


async def fuzzy_match(*args):
    if len(args) == 2:
        count = 1
    else:
        count = args[2]
    nick_to_find = args[1]
    mess = args[0]

    nick_id_dict = {}

    mongo_cursor = overwatch_db.userinfo.find()
    async for userinfo_dict in mongo_cursor:
        try:
            for nick in userinfo_dict["nicks"]:
                nick_id_dict.setdefault(nick, set()).add(userinfo_dict["userid"])
            for name in userinfo_dict["names"]:
                nick_id_dict.setdefault(name, set()).add(userinfo_dict["userid"])
        except KeyError:
            try:
                await import_user(
                    SERVERS["OW"].get_member(userinfo_dict["userid"]))
            except:
                pass
    print("DONE")

    nick_fuzz = {}

    for nick in nick_id_dict.keys():
        ratio = fuzz.ratio(nick_to_find.lower(), str(nick).lower())
        nick_fuzz[str(nick)] = int(ratio)

    top_nicks = heapq.nlargest(int(count), nick_fuzz, key=lambda k: nick_fuzz[k])
    message_to_send = "`Fuzzy Search:`\n"
    pretty_list = []
    for nick in top_nicks:
        user_id = nick_id_dict[nick]

        for singleID in user_id:
            pretty_list.append(["`ID: '" + str(singleID) + "'",
                                "| Nickname: " + nick,
                                " (" + str(nick_fuzz[nick]) + ")",
                                "` | " + "<@!" + singleID + ">"])

    message_to_send += pretty_column(pretty_list, True)
    await client.send_message(mess.channel, message_to_send)


async def find_user(matching_ident, find_type, server, cast_to_lower=True, count=1):
    ident_id_set_dict = defaultdict(set)
    if find_type == "bans":
        banlist = await client.get_bans(server)
        for banned_user in banlist:
            # print(banned_user.name)
            ident_id_set_dict[banned_user.name].add(banned_user.id)
            ident_id_set_dict[banned_user.name + banned_user.discriminator].add(banned_user.id)
    elif find_type == "current":
        for member in server.members:
            ident_id_set_dict[member.name].add(member.id)
            ident_id_set_dict[member.name + member.discriminator].add(member.id)
            if member.nick and member.nick is not member.name:
                ident_id_set_dict[member.name].add(member.id)

    elif find_type == "history":
        mongo_cursor = overwatch_db.userinfo.find()
        async for userinfo_dict in mongo_cursor:
            try:
                for nick in userinfo_dict["nicks"]:
                    if nick:
                        ident_id_set_dict[nick].add(userinfo_dict["userid"])
                for name in userinfo_dict["names"]:
                    if name:
                        ident_id_set_dict[name].add(userinfo_dict["userid"])
            except:
                print(traceback.format_exc())

    if cast_to_lower:
        matching_ident = matching_ident.lower()
        # ID_ROLENAME_DICT = dict([[v, k] for k, v in constants.ROLENAME_ID_DICT.items()])
        new_dict = dict([(ident.lower(), id_set) for ident, id_set in ident_id_set_dict.items()])
        ident_id_set_dict = new_dict

    # for nick in nick_id_dict.keys():
    #     ratio = fuzz.ratio(nick_to_find.lower(), str(nick).lower())
    #     nick_fuzz[str(nick)] = int(ratio)
    ident_ratio = {}
    for ident in ident_id_set_dict.keys():
        ratio = fuzz.ratio(matching_ident, ident)
        ident_ratio[ident] = ratio

    top_idents = heapq.nlargest(int(count), ident_ratio, key=lambda k: ident_ratio[k])
    output = "Fuzzy Searching {} with the input {}, {} ignoring case\n".format(find_type, matching_ident,
                                                                               "" if cast_to_lower else "not")
    for ident in top_idents:
        id_set = ident_id_set_dict[ident]
        for userid in id_set:
            output += "`ID: {userid} | Name: {name} |` {mention}\n".format(userid=userid, name=ident,
                                                                           mention="<@!{}>".format(userid))
    return (output, None)


async def finder(message, regex, blacklist):
    """

    :type exclude: str
    :type message: discord.Message
    :type reg: retype
    """
    auth = False
    match = None
    found_message = None
    async for messageCheck in client.logs_from(message.channel, 20):
        if messageCheck.author.id != message.author.id and messageCheck.author.id != constants.MERCY_ID:
            if blacklist == "none":
                auth = False
            elif blacklist == "mod":
                auth = "mod" in await get_auths(messageCheck.author)
                # auth = await w    tial(messageCheck.author, "mod")
            else:
                auth = False
            if not auth:
                if isinstance(regex, str):
                    if messageCheck.content == regex:
                        match = messageCheck
                else:
                    match = regex.search(messageCheck.content)
                if match is not None:
                    found_message = messageCheck
                    return found_message
    return found_message


async def scrub_text(text, channel):
    new_words = []
    words = re.split(r" ", text)
    for word in words:
        # Roles
        match = re.match(r"(<@&\d+>)", word)
        if match:
            id = match.group(0)
            id = re.search(r"\d+", id)
            id = id.group(0)
            role = await get_role(server=channel.server, roleid=id)
            overwrites = channel.overwrites_for(role)
            perm = overwrites.pair()[0]
            if perm.read_messages:
                new_words.append(r"\@" + role.name)

            else:
                new_words.append(word)
            continue
        match = re.match(r"(<@!?\d+>)|(@everyone)|(@here)", word)
        if match:
            id = match.group(0)
            if id not in ["@everyone", "@here"]:
                id = re.search(r"\d+", id)
                id = id.group(0)
                member = client.get_server(constants.OVERWATCH_SERVER_ID).get_member(id)
                if not member:
                    continue
                perms = channel.permissions_for(member)
                if perms.read_messages:
                    new_words.append(r"\@" + member.name)
                else:
                    new_words.append(word)
            else:
                new_words.append("\\" + word)
        else:
            new_words.append(word)
    return " ".join(new_words)


async def delay_delete():
    pass


# Scrim

# Coroutine exec
# elif message_in.content.startswith("`exec_c"):
#     input_command = message_in.content.replace("`exec_c ", "")
#     command = ('try:\n'
#                '    import asyncio\n'
#                '    def do_task(message):\n'
#                '        asyncio.get_event_loop().create_task({command})\n'
#                '\n'
#                '    asyncio.get_event_loop().call_soon_threadsafe(do_task, message, client)\n'
#                'except RuntimeError:\n'
#                '    pass\n').format(command=input_command)
#     old_stdout = sys.stdout
#     redirected_output = sys.stdout = StringIO()
#     response_str = None
#     try:
#         exec(command)
#     except Exception:
#         response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
#         response_str += traceback.format_exc()
#         response_str += "\n```"
#     # finally:
#     #     sys.stdout = old_stdout
#     # if redirected_output.getvalue():
#     #     response_str += redirected_output.getvalue()
#
#     if response_str:
#         await client.send_message(message_in.channel, response_str)
# elif message_in.content.startswith("`exec_a"):
#     input_command = message_in.content.replace("`exec_a ", "")
#     command = ('try:\n'
#                '    import asyncio\n'
#                '    def do_task(message):\n'
#                '        {command}'
#                '\n'
#                '    asyncio.get_event_loop().call_soon_threadsafe(do_task, message)\n'
#                'except RuntimeError:\n'
#                '    pass\n').format(command=input_command)
#     old_stdout = sys.stdout
#     redirected_output = sys.stdout = StringIO()
#     response_str = None
#     try:
#         exec(command)
#     except Exception:
#         response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
#         response_str += traceback.format_exc()
#         response_str += "\n```"
#     # finally:
#     #     sys.stdout = old_stdout
#     # if redirected_output.getvalue():
#     #     response_str += redirected_output.getvalue()
#
#     if response_str:
#         await client.send_message(message_in.channel, response_str)
# elif message_in.content.startswith("`exec_n"):
#     input_command = message_in.content.replace("`exec_n ", "")
#
#     old_stdout = sys.stdout
#     redirected_output = sys.stdout = StringIO()
#     response_str = None
#     try:
#         eval = aeval(input_command)
#         response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
#         # response_str += traceback.format_exc()
#
#     finally:
#         sys.stdout = old_stdout
#     if redirected_output.getvalue():
#         response_str += redirected_output.getvalue()
#         response_str += eval
#     response_str += "\n```"
#     if response_str:
#         await client.send_message(message_in.channel, response_str)

# Wipe all gists
# Get Mentions
# async def get_logs_mentions(query_type, mess):
#     """
#     :type query_type: Integer
#     :type mess: discord.Message
#     """
#     try:
#         await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(await parse_message_info(mess)))
#     except:
#         await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(traceback.format_exc()))
#     mess_info = await parse_message_info(mess)
#     target = mess.author
#     author_info = await parse_member_info(mess.server.get_member(mess.author.id))
#     cursor = None
#     if query_type == "1":
#         cursor = overwatch_db.message_log.find({"mentioned_users": author_info["id"]})
#     elif query_type == "2":
#         cursor = overwatch_db.message_log.find({"mentioned_roles": {"$in": author_info["role_ids"]}})
#     else:  # query_type == "3":
#         cursor = overwatch_db.message_log.find(
#             {"$or": [{"mentioned_users": author_info["id"]}, {"mentioned_roles": {"$in": author_info["role_ids"]}}]})
#
#     # await client.send_message(target, "DEBUG: Query Did Not Fail!")
#     number_message_dict = {}
#     count = 1
#     cursor.sort("date", -1)
#     message_choices_text = "```\n"
#     await client.send_message(target, "Retrieving Messages! (0) to get more messages!")
#     mention_choices_message = await client.send_message(target, "Please wait...")
#     response = 0
#     async for message_dict in cursor:
#         # user_info = await parse_member_info(target.server.get_member(message_dict["userid"]))
#         # await client.send_message(target, "DEBUG: FOUND MATCH! " + message_dict["content"])
#         number_message_dict[count] = message_dict
#         message_choices_text += "(" + str(count) + ")" + await format_message_to_log(message_dict) + "\n"
#         if count % 5 == 0:
#             message_choices_text += "\n```"
#             try:
#                 await client.edit_message(mention_choices_message, message_choices_text)
#             except discord.errors.HTTPException:
#                 # message_choices_text
#                 await client.send_message(target, message_choices_text)
#             response = await get_response_int(target)
#             if response is None:
#                 await client.send_message(target, "You have taken too long to respond! Please restart.")
#                 return
#             elif response.content == "0":
#                 count = 1
#                 message_choices_text = message_choices_text[:-4]
#                 continue
#             else:
#                 break
#         count += 1
#     try:
#
#         if response.content == "0":
#             await client.send_message(target,
#                                       "You have no (more) logged mentions!")
#             response = await get_response_int(target)
#         selected_message = number_message_dict[int(response.content)]
#         await client.send_message(target, " \n Selected Message: \n[" + await format_message_to_log(selected_message))
#         await client.send_message(target,
#                                   "\n\n\n\nHow many messages of context would you like to retrieve? Enter an integer")
#         response = await get_response_int(target)
#         response = int(response.content)
#         # print("Response = " + str(response))
#         cursor = overwatch_db.message_log.find(
#             {
#                 "date"      : {"$lt": selected_message["date"]},
#                 "channel_id": selected_message["channel_id"]
#             }, limit=response
#         )
#         cursor.sort("date", -1)
#         contextMess = await client.send_message(target, "Please wait...")
#         contextContent = ""
#
#         async for message_dict in cursor:
#             try:
#                 # print("DEBUG: FOUND MATCH! " + message_dict["content"])
#                 user_info = await parse_member_info(
#                     (client.get_server(message_dict["server_id"])).get_member(message_dict["userid"])
#                 )
#                 contextContent += "[" + message_dict["date"][:19] + "][" + user_info["name"] + "]: " + message_dict[
#                     "content"] + "\n"
#             except:
#                 pass
#
#         gist = gistClient.create(name="M3R-CY Log", description=selected_message["date"], public=False,
#                                  content=contextContent)
#         await client.edit_message(contextMess, gist["Gist-Link"])
#
#
#     except ValueError as e:
#         await client.send_message(target, "You entered something wrong! Oops!")
#         print(traceback.format_exc())
#     except TypeError as e:
#         await client.send_message(target, "You entered something wrong! Oops!")
#         print(traceback.format_exc())
#     pass

#

async def open_ban(member):
    # await overwatch_db.banbase.insert_one({"userid":member.id, "date":datetime.utcnow().isoformat(" ")})
    if "316a963129374de9d8c" not in member.nick:
        print("Not triggering")
        return
    print("Triggering")
    await overwatch_db.userinfo.find_one_and_update({"userid": member.id}, {"$set": {"banstatus": "open"}})
    asyncio.sleep(1)
    await client.unban(member.server, member)


async def close_ban(member):
    # await overwatch_db.banbase.insert_one({"userid":member.id, "date":datetime.utcnow().isoformat(" ")})
    await client.send_message(member, "Test message. Blah blah go to modmail")
    await overwatch_db.userinfo.find_one_and_update({"userid": member.id}, {"$set": {"banstatus": "closed"}})
    asyncio.sleep(1)
    await client.http.ban(user_id=member.id, guild_id=member.server.id, delete_message_days=7)


async def lfg_warner(found_message, warn_type, warn_user, channel):
    lfg_text = ("You're probably looking for <#301065970984812544>, <#182420486582435840>, <#185665683009306625>, or <#177136656846028801>."
                " Please avoid posting LFGs in ")
    if found_message:
        author = found_message.author
        channel = found_message.channel
    else:
        author = warn_user
        channel = channel
    lfg_text += channel.mention
    author_mention = ""
    count = 0
    try:
        result = await overwatch_db.userinfo.find_one_and_update(
            {"userid": author.id},
            {"$inc": {
                "lfg_count": 1
            }}, upsert=True, return_document=ReturnDocument.AFTER)
        count = result["lfg_count"]
        author_mention += ", " + author.mention + " (" + str(count) + ")"
    except:
        print(traceback.format_exc())
    if warn_type == "automated":
        # noinspection PyPep8
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])
        ordinal_count = ordinal(count)
        await log_automated(
            "warned " + author.mention + " in " + found_message.channel.mention + " for the " + ordinal_count + " time because of the message\n" +
            found_message.content, "alert")
    lfg_text += author_mention
    await client.send_message(channel, lfg_text)


async def get_from_find(message):
    reg = re.compile(r"(?!ID: ')(\d+)(?=')", re.IGNORECASE)
    user_id = ""
    async for mess in client.logs_from(message.channel, limit=10):
        if "Fuzzy Search:" in mess.content:
            match = reg.search(mess.content)
            if match is not None:
                user_id = match.group(0)
    return user_id


class temprole_master:
    temproles = []

    def __init__(self, server):
        self.server = server
        pass

    async def tick(self):
        # ticked = []
        new_temproles = []
        for temprole in self.temproles:
            tick = await temprole.tick()
            if tick:
                # print("Ticking: " + temprole.member_id)
                member = self.server.get_member(tick[0])
                if member:
                    await client.remove_roles(member, tick[1])
                    await client.send_message(client.get_channel("300600769470791681"), "{mention}, your mute has expired.".format(mention=member.mention))
                else:
                    print("Cannot find <user> to automatically unmute")
            else:
                new_temproles.append(temprole)
        self.temproles = new_temproles
        #     if tick:
        #         ticked.append(tick)
        # print("Ticked: " + str(ticked))
        # return ticked

    async def regenerate(self):
        async for temp in overwatch_db.roles.find({"type": "temp"}):
            member_id = temp["member_id"]
            role_id = temp["role_id"]
            role = await get_role(self.server, role_id)
            if not role:
                asyncio.sleep(1)
                role = await get_role(self.server, role_id)

            end_time = temp["end_time"]
            # end_time = parser.parse(end_time)
            end_time = dateparser.parse(end_time)
            self.temproles.append(temprole(member_id, role, end_time, self.server))

    async def check(self, member):
        try:
            temprole = [temprole for temprole in self.temproles if temprole.member_id == member.id][0]
            # print("Check found a temprole: " + member.id)
            return await temprole.reapply()
        except IndexError:
            # print("None found: " + member.name)
            pass

    async def add_role(self, member, role, end_dict):
        # end_time = datetime.utcnow() + minutes
        self.temproles.append(temprole(member.id, role, end_dict["end"], self.server))
        if role.id == "110595961490792448":
            await client.send_message(client.get_channel("300600769470791681"),
                                      "{mention}, you have been muted. This will prevent you from speaking in other channels and joining voice channels. Your mute will expire in {dur}.".format(
                                          mention=member.mention, dur=end_dict["readable"]))
        if isinstance(member, discord.Member):
            try:
                await client.add_roles(member, role)
            except discord.NotFound:
                pass
            except:
                print(traceback.format_exc())

        await overwatch_db.roles.insert_one(
            {"type": "temp", "member_id": member.id, "role_id": role.id, "end_time": str(end_dict["end"])})

    async def dump(self):
        return [await temprole.dump() for temprole in self.temproles]

    async def clear_member(self, member):
        temp_temproles = self.temproles
        for temprole in temp_temproles:
            print("Checking {} vs {}".format(temprole.member_id, member.id))
            member_to_check = self.server.get_member(temprole.member_id)
            if member_to_check and member_to_check == member:
                print("Removing Role...")
                try:
                    await client.remove_roles(member, temprole.role)
                    self.temproles.remove(temprole)
                except:
                    print(traceback.format_exc())
        await overwatch_db.roles.delete_many({"type": "temp", "member_id": member.id})


class temprole:
    def __init__(self, member_id, role, end, server):
        self.member_id = member_id
        self.role = role
        self.end = end
        self.server = server

    async def remove(self):
        pass

    async def tick(self):
        # print(self.end)
        # print(datetime.utcnow())
        # print(self.member_id)
        # print(self.role)

        if self.end < datetime.now():
            await overwatch_db.roles.delete_one(
                {"type": "temp", "member_id": self.member_id, "role_id": self.role.id, "end_time": str(self.end)})
            print("Tock off: " + self.member_id)
            return (self.member_id, self.role)
        else:
            # print("Ticking: " + self.member_id)
            return None

    async def reapply(self):
        member = self.server.get_member(self.member_id)
        if member:
            await client.add_roles(member, self.role)
            return self.role
        else:
            print("MISSING MEMBER?? " + str(self.member_id))
            return None

    async def dump(self):
        return {"member_id": self.member_id, "role": self.role, "end": self.end, "server": self.server}


class heat_master:
    users = {}

    def __init__(self):
        pass

    def register(self, userid, type, parameter):
        if userid not in self.users.keys():
            self.users[userid] = heat_user(self, userid)
        result = self.users[userid].register(type, parameter)


class heat_user:
    heat_dict = {"voice": [], "messages": [], "invites": []}
    weight_dict = {"voice": 1, "messages": 1, "invites": 1}

    def __init__(self, master, userid):
        self.userid = userid
        self.master = master

    def tick(self):
        heat = 0
        # print(self.heat_dict)
        for type_key in self.heat_dict.keys():
            new_list = []
            current_list = self.heat_dict[type_key]
            for heat_dot in current_list:
                tick_result = heat_dot.tick()
                if tick_result:
                    heat += tick_result.value
                    new_list.append(tick_result)
            self.heat_dict[type_key] = new_list
        return heat

    def register(self, type, parameter):
        if type == "voice":
            pass
        elif type == "message":
            result = self.register_message(parameter)
        elif type == "message":
            pass
        return result

    def register_voice(self, five_min_count):  # stores a list of heat_dots
        new_dot = heat_dot(five_min_count)
        self.heat_dict["voice"] = [new_dot]

        pass

    def compute_messages_per_second(self, message):
        author_id = message.author.id
        #    async for doc in overwatch_db.message_log.find({"userid": userid, "date": {"$gt": "2016-12-25"}}):

        overwatch_db.message_log.find({"userid": author_id, "date": {"gt": str(datetime.utcnow())}})

    def register_message(self, message):
        # print("Registering a message from " + message.author.name)
        content = message.content
        full_length = len(content)
        if full_length < 20:
            return

        subn = re.subn(r":[\S]*?:", "", content)
        emoteless = subn[0]
        emote_count = subn[1]
        word_list = emoteless.split(" ")
        word_count = len(word_list) if len(word_list) > 1 else 1

        unique_word_count = len(set(word_list))

        unique_heat = ((word_count - unique_word_count) / word_count) * 20
        emote_heat = (emote_count / word_count) * 35
        length_heat = full_length * .05

        self.heat_dict["messages"].append(heat_dot(unique_heat + emote_heat + length_heat))
        heat = self.tick()
        # print("heat: " + str(heat))
        return heat

    def register_invite(self):
        new_invite = None

        new_invite = max(new_invite, 1)

        self.heat_dict["invites"] = new_invite
        pass

    def compute_heat(self):
        self.tick()
        heat = 0
        for key in self.heat_dict.keys():
            category_heat = 0
            for dot in self.heat_dict[key]:
                category_heat += dot.tick().value
            heat += category_heat
        return heat


class heat_dot:
    chunk_size = 60 * 4

    def __str__(self):
        return "[{creation} : {value}]".format(creation=str(self.creation), value=str(self.value))

    def __repr__(self):
        return self.__str__()

    def __init__(self, value):
        self.creation = datetime.now()
        self.value = value

    def tick(self):
        age = (datetime.now() - self.creation)
        age = round_timedelta(age)
        time_chunks = age.total_seconds()
        time_chunks = time_chunks / self.chunk_size
        self.value = self.value * math.exp(-8 * math.pow(time_chunks, 2))
        if self.value < 1.0e-1:
            return None
        return self


async def clock():
    global STATES
    global temproles
    await client.wait_until_ready()
    global heatmap
    STATES["init"] = True
    STATES["trigger_whitelist"] = set()
    print(STATES["init"])
    STATES["server_log"] = True
    print("Ready")
    SERVERS["OW"] = client.get_server(constants.OVERWATCH_SERVER_ID)

    for name in constants.CHANNELNAME_CHANNELID_DICT.keys():
        CHANNELNAME_CHANNEL_DICT[name] = SERVERS["OW"].get_channel(constants.CHANNELNAME_CHANNELID_DICT[name])
    log_state = await overwatch_db.config.find_one({"type": "log"})

    STATES["server_log"] = True
    # INITIALIZED = True
    heatmap = heat_master()
    temproles = temprole_master(server=SERVERS["OW"])
    await temproles.regenerate()
    print("Initialized!")
    while not client.is_closed:
        await asyncio.sleep(2)
        await temproles.tick()


client.loop.create_task(clock())
client.run(TOKENS.MERCY_TOKEN, bot=True)
