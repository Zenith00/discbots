import heapq
import logging
import math
import random
import textwrap
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

import discord
import motor.motor_asyncio
import pymongo
import wolframalpha
from asteval import Interpreter
# import fuzzywuzzy
from fuzzywuzzy import fuzz, process
from imgurpython import ImgurClient
from pymongo import ReturnDocument
from simplegist.simplegist import Simplegist
from unidecode import unidecode
# import Color
import constants
from TOKENS import *
from tag import Tagger
from discord import http as dischttp
import string
from utils_parse import *
from utils_text import *
from utils_text import shorten_link
import utils_image
from dateutil import parser
import dateparser

logging.basicConfig(level=logging.INFO)

# Clients

imgur = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
                    IMGUR_REFRESH_TOKEN)
WA_client = wolframalpha.Client(WA_ID)
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
overwatch_db = mongo_client.overwatch
message_log_collection = overwatch_db.message_log
userinfo_collection = overwatch_db.userinfo
auths_collection = overwatch_db.auths
trigger_str_collection = overwatch_db.trigger_str
mongo_client_static = pymongo.MongoClient()
aeval = Interpreter()
gistClient = Simplegist()
# scrim
scrim = None
client = discord.Client()

temproles = None
id_channel_dict = {}

ROLENAME_ROLE_DICT = {}

ID_ROLENAME_DICT = dict([[v, k] for k, v in constants.ROLENAME_ID_DICT.items()])
BLACKLISTED_CHANNELS = (
    constants.CHANNELNAME_CHANNELID_DICT["bot-log"], constants.CHANNELNAME_CHANNELID_DICT["server-log"],
    constants.CHANNELNAME_CHANNELID_DICT["voice-channel-output"])
SERVERS = {}
CHANNELNAME_CHANNEL_DICT = {}

VCInvite = None
VCMess = None

INITIALIZED = False

tagger = Tagger(client)

STATES = {}

class Streamer:
    def __init__(self, chann, thresh):
        self.channel = chann
        self.threshold = thresh
        self.counter = 0
        self.message = ""

    async def add(self, string):
        self.message += string + "\n"
        # print(ascii(self.message))
        print(str(self.counter) + " " + str(self.threshold))
        if self.counter >= self.threshold:
            await client.send_message(self.channel, self.message)
            self.counter = 0
            self.message = ""
        else:
            self.counter += 1

class ScrimTeam:
    def __init__(self, id, channel):
        self.members = []
        self.name = id
        self.vc = channel

class ScrimMaster:
    def __init__(self, scr1, scr2, txt, spec, output):
        self.output = output
        self.team1 = scr1
        self.team2 = scr2
        self.text = txt
        self.spectate = spec
        self.masters = []

    async def get_managers(self):
        managers = []
        manager_cursor = overwatch_db.scrim.find({"manager": 1})
        async for manager in manager_cursor:
            managers.append(manager["userid"])

        return managers

    async def end(self):
        await client.delete_channel(self.team1.vc)
        await client.delete_channel(self.team2.vc)
        await client.delete_channel(self.text)
        await client.delete_channel(self.spectate)
        await overwatch_db.scrim.update_many({}, {"$set": {"active": False, "pos": 0, "status": ""}})

    async def assign(self, member, team):
        await self.deauth(member)
        return await self.auth(member, team)

    async def reset(self):
        cursor = overwatch_db.scrim.find({"active": True})
        server = self.output.server
        async for person in cursor:
            await self.deauth(server.get_member(person["userid"]))
        await overwatch_db.scrim.update_many({"status": "playing"}, {"$set": {"active": False}})

    async def auth(self, member, team):
        print("Assigning {} to {}".format(member.id, team))
        if team == "1":
            target_team = self.team1
        elif team == "2":  # team == "2":
            target_team = self.team2
        else:
            return
        # self.members[member.id] = team
        await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"team": target_team.name}})

        target_team.members.append(member.id)
        user_overwrite_vc = discord.PermissionOverwrite(connect=True)
        await client.edit_channel_permissions(target_team.vc, member, user_overwrite_vc)
        return member.mention + " added to team " + target_team.name

    async def deauth(self, member):
        if not member:
            return
        target_member = await overwatch_db.scrim.find_one({"userid": member.id})
        if not target_member:
            print("FAILED TO FIND {}".format(member.id))
            return
        if "team" not in target_member.keys():
            return
        target = target_member["team"]
        if target == "1":
            target_team = self.team1
        elif target == "2":
            target_team = self.team2
        else:
            return
        await client.delete_channel_permissions(target_team.vc, member)

    async def force_register(self, message):
        command_list = message.content.split(" ")
        print(command_list)
        print("Registering")
        await overwatch_db.scrim.update_one({"userid": command_list[5]},
                                            {"$set": {"rank"  : command_list[3].lower(), "btag": command_list[2],
                                                      "region": command_list[4], "active": True}}, upsert=True)
        await scrim.add_user(self.output.server.get_member(command_list[5]))

    async def register(self, message):
        command_list = message.content.split(" ")
        await overwatch_db.scrim.update_one({"userid": message.author.id},
                                            {"$set": {"rank"  : command_list[1].lower(), "btag": command_list[0],
                                                      "region": command_list[2], "active": True}}, upsert=True)
        await scrim.add_user(message.author)

    async def serve_scrim_prompt(self, member):
        user = await overwatch_db.scrim.find_one({"userid": member.id, "btag": {"$exists": True}})
        if user:
            confirmation = "Joining scrim as [{region}] {btag} with an SR of {sr}".format(region=user["region"],
                                                                                          btag=user["btag"],
                                                                                          sr=user["rank"])
            await client.send_message(member, confirmation)
            await scrim.add_user(member)
        else:
            await client.send_message(member,
                                      "Please enter your battletag, highest SR, and region (EU, NA, KR) in the format:\nBattleTag#0000 2500 EU\n or Battletag#00000 unplaced NA")

    async def add_user(self, member):
        size = 12
        # base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.DESCENDING)])
        await self.compress()
        cursor = overwatch_db.scrim.find({"active": True})
        count = await cursor.count()
        print(count)

        await overwatch_db.scrim.update_one({"userid": member.id},
                                            {"$set": {"active": True, "pos": count, "status": "pending",
                                                      "team"  : ""}})

        new_joined = await overwatch_db.scrim.find_one({"userid": member.id})
        cursor = overwatch_db.scrim.find({"active": True})
        count = await cursor.count()
        print(count)
        update = "[{region}] {btag} ({mention}) has joined the scrim with an SR of {sr} ({count}/{size})".format(
            region=new_joined["region"], btag=new_joined["btag"], mention=member.mention, sr=new_joined["rank"],
            count=count, size=size)
        await client.send_message(self.output, update)

    async def start(self):
        await self.compress()

        overwatch_db.scrim.update_many({"active": True}, {"$set": {"team": "pending"}})
        # await self.reset()
        size = 12
        cursor = overwatch_db.scrim.find({"active": True})
        count = await cursor.count()
        if count < size:
            await client.send_message(self.output,
                                      "Not enough players: ({count}/{size})".format(count=count, size=size))
            return
        else:
            base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.ASCENDING)])
            if not base:
                print("BLAHAHAHAH")
                return
            if base["pos"] != 1:
                print(str(base["pos"]) + " " + base["btag"])
                start = 1 - base["pos"]
                await overwatch_db.scrim.update_many({"active": True}, {"$inc": {"pos": start}})

            await client.send_message(self.output, "Starting...")
            await overwatch_db.scrim.update_many({"active": True, "pos": {"$lt": size + 1}},
                                                 {"$set": {"status": "playing"}})
            await self.autobalance()
            await self.output_teams()
            await overwatch_db.scrim.update_many({"status": "playing"}, {"active": False, "pos": ""})
            base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.ASCENDING)])
            if not base:
                print("BLAHAHAHAH")
                return
            if base["pos"] != 1:
                start = 1 - base["pos"]
                await overwatch_db.scrim.update_many({"active": True}, {"$inc": {"pos": start}})

    async def leave(self, member):
        userid = member.id
        await overwatch_db.scrim.update_one({"userid": userid},
                                            {"$set": {"team": "0", "active": False, "manager": 0, "status": "",}})
        return "Removed " + member.mention + " from the active user pool"

    # async def register(self, member, btag, sr, region):
    #
    #     await overwatch_db.scrim.update_one({"userid": member.id},
    #                                         {"$set": {"rank": sr, "btag": btag, "region": region, "active": True}},
    #                                         upsert=True)

    async def refresh(self, member):
        user = await overwatch_db.scrim.find_one({"userid": member.id})
        await self.register(member, user["btag"])

    async def autobalance(self):
        server = self.output.server

        cursor = overwatch_db.scrim.find(
            {"active": True, "status": "playing"},
            projection=["userid", "rank"])

        cursor.sort("rank", -1)
        members = await cursor.to_list(None)
        print(members)
        counter = 0
        for user in members:
            if counter == 4:
                counter = 0
            if counter == 0 or counter == 3:
                await scrim.assign(server.get_member(user["userid"]), "1")

            elif counter == 1 or counter == 2:
                await scrim.assign(server.get_member(user["userid"]), "2")
            counter += 1
        await client.send_message(self.output, "Autobalancing completed")

    async def compress(self):
        count = 1
        cursor = overwatch_db.scrim.find({"active": True})
        cursor.sort("pos", pymongo.ASCENDING)
        async for item in cursor:
            print(item)
            print(count)
            result = await overwatch_db.scrim.update_one({"userid": item["userid"]}, {"$set": {"pos": count}})
            print(result.raw_result)
            count += 1

    async def output_teams_list(self):
        cursor = overwatch_db.scrim.find({"active": True})

        cursor.sort("pos", pymongo.ASCENDING)

        userlist = [["Name", "Battletag", "SR", "Position"]]
        async for user in cursor:
            print(user)
            user_entry = []
            try:
                user_entry.append(unidecode(self.output.server.get_member(user["userid"]).name))
            except:
                user_entry.append("MISSING")

            user_entry.append(user["btag"])
            user_entry.append(user["rank"])
            user_entry.append(str(user["pos"]))
            userlist.append(user_entry)
        await send(self.output, userlist, "rows")

    async def output_teams(self):
        cursor = overwatch_db.scrim.find({"active": True, "status": "playing"})
        team1 = [["Team 1", "", "", ""], ["Name", "Battletag", "SR", "ID"]]
        team2 = [["Team 2", "", "", ""], ["Name", "Battletag", "SR", "ID"]]
        async for user in cursor:
            team = user["team"]

            if team == "1":
                target_team = team1
            elif team == "2":
                target_team = team2
            else:
                print("fail - check teams")
                return

            user_entry = []

            user_entry.append(unidecode(self.output.server.get_member(user["userid"]).name))
            user_entry.append(user["btag"])
            user_entry.append(user["rank"])
            user_entry.append(user["userid"])
            try:
                target_team.append(user_entry)
            except:
                print(user)
        for item in [team1, team2]:
            await send(destination=self.output, text=item, send_type="rows")

async def get_redirected_url(url):
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    request = opener.open(url)
    return request.url

@client.event
async def on_member_remove(member):
    if member.server.id == constants.OVERWATCH_SERVER_ID:
        await import_to_user_set(member=member, set_name="server_leaves", entry=datetime.utcnow().isoformat(" "))
        await log_action("leave", {"mention": member.mention, "id": member.id})

@client.event
async def on_member_ban(member):
    if member.server.id == constants.OVERWATCH_SERVER_ID:
        await import_to_user_set(member=member, set_name="bans", entry=datetime.utcnow().isoformat(" "))
        spam_ch = client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["spam-channel"])
        # await client.send_message(spam_ch, "Ban detected, user id = " + member.id)
        await log_action("ban", {"member": member})

@client.event
async def on_member_unban(server, member):
    if server.id == constants.OVERWATCH_SERVER_ID:
        # print("unban detected")
        await import_to_user_set(member=member, set_name="unbans", entry=datetime.utcnow().isoformat(" "))
        # await client.send_message(CHANNELNAME_CHANNEL_DICT["spam-channel"], "Unban detected, user id = " + member.id)
        await log_action("unban", {"mention": "<@!{id}>".format(id=member.id), "id": member.id})

        # await log_automated("registered a user unban: \n```" + str(await export_user(member.id)) + "```")

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    global INITIALIZED
    global STATES
    global temproles
    SERVERS["OW"] = client.get_server(constants.OVERWATCH_SERVER_ID)
    for role in SERVERS["OW"].roles:
        if role.id in ID_ROLENAME_DICT.keys():
            ROLENAME_ROLE_DICT[ID_ROLENAME_DICT[role.id]] = role
    for name in constants.CHANNELNAME_CHANNELID_DICT.keys():
        CHANNELNAME_CHANNEL_DICT[name] = SERVERS["OW"].get_channel(constants.CHANNELNAME_CHANNELID_DICT[name])
    log_state = await overwatch_db.config.find_one({"type": "log"})
    STATES["server_log"] = log_state["server_log"]
    INITIALIZED = True
    temproles = temprole_master(server=SERVERS["OW"])
    await temproles.regenerate()

@client.event
async def on_member_join(member):
    # await add_to_nick_id_list(member)
    if member.server.id == constants.OVERWATCH_SERVER_ID:
        await import_user(member)
        current_date = datetime.utcnow()
        age = abs(current_date - member.created_at)
        await log_action("join", {"mention": member.mention, "id": member.id, "age": str(age)[:-7]})
        if INITIALIZED:
            role = await temproles.check(member)
            if role:
                await log_automated("reapplied {role} to {mention}".format(role=role.name if role.mentionable else role.mention, mention=member.mention),
                                    type="autorole")
# noinspection PyUnusedLocal
@client.event
async def on_voice_state_update(before, after):
    """
    :type after: discord.Member
    :type before: discord.Member
    """
    global VCInvite
    global VCMess
    if before.server.id == constants.OVERWATCH_SERVER_ID:

        if VCInvite is not None and VCMess is not None:
            if after is VCMess.author:
                await client.delete_messages([VCInvite, VCMess])
                VCInvite = None
                VCMess = None
        if before.voice.voice_channel != after.voice.voice_channel:
            await log_action("voice_update", {"before": before, "after": after, "id": before.id})

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
        if not INITIALIZED:
            return

        if len(before.roles) != len(after.roles):
            await log_action("role_change", {"member": after, "old_roles": before.roles[1:], "new_roles": after.roles[1:]})

@client.event
async def on_message_edit(before, after):
    if before.server.id == constants.OVERWATCH_SERVER_ID:

        auths = await get_auths(after.author)
        if "mod" not in auths:
            # EXTRA-SERVER INVITE CHECKER
            await parse_triggers(after)
            # if after.channel.id not in BLACKLISTED_CHANNELS:
            #     match = constants.INVITE_REGEX.search(after.content)
            #     if match is not None:
            #         await invite_checker(after, match)
        await log_action("edit",
                         {"channel": before.channel.mention, "mention": before.author.mention, "id": before.author.id,
                          "before" : before.content, "after": after.content})

@client.event
async def on_message_delete(message):
    if message.server.id == constants.OVERWATCH_SERVER_ID:
        await log_action("delete",
                         {"channel": message.channel.mention, "mention": message.author.mention, "id": message.author.id,
                          "content": message.content})

@client.event
async def on_message(message_in):
    global VCMess
    global VCInvite
    global PATHS
    global ENABLED
    global INITIALIZED

    if not INITIALIZED:
        return
    if message_in.author.id == client.user.id:
        return
    await temproles.tick()
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
        print("Firing command [{command}] from {author}".format(command=segmented_command[0],
                                                                author=message_in.author.name))
        await perform_command(command=command, params=params, message_in=message_in)

    if message_in.server.id == constants.OVERWATCH_SERVER_ID:
        if message_in.content.startswith("`scrim start"):
            await scrim_start(message_in)
            return
        # if message_in.channel.id not in BLACKLISTED_CHANNELS and message_in.server.id == constants.OVERWATCH_SERVER_ID:
        await import_message(message_in)

        if "mod" not in auths:
            await parse_triggers(message_in)
            # if message_in.channel.id not in BLACKLISTED_CHANNELS:
            #     match = constants.INVITE_REGEX.search(message_in.content)
            #     if match is not None:
            #         await invite_checker(message_in, match)

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
    # unspaggheti
    warn_auths = await overwatch_db.auths.find_one({"type": "warn"})
    if warn_auths:
        try:
            auth_list = warn_auths["ids"]
            if member.id in auth_list:
                auths |= {"warn"}
        except (KeyError, TypeError):
            pass
    if member.server.id == "236343416177295360":
        if "261550254418034688" in [role.id for role in member.roles]:
            auths |= {"host"}
    return auths

async def perform_command(command, params, message_in):
    if params:
        params = await mention_to_id(params.split(" "))
    output = []
    auths = await get_auths(message_in.author)

    send_type = None
    called = False
    if message_in.server.id == "266279338305912832" or "zenith" in auths:
        if command == "big":
            text = str(" ".join(params))
            big_text = ""
            for character in text:
                if character == " ":
                    big_text += "     "
                else:
                    big_text += " :regional_indicator_{c}:".format(c=character)
            output.append((big_text, None))

    if command == "scrim":
        await scrim_manage(message_in)

    if command in ["names", "firstjoins", "mostactive", "channeldist", "superlog", "rebuildnicks", "wa", "reboot", "rebuild", "ui", "ping", "lfg",
                   "serverlog", "timenow", "say", "raw", "getroles", "moveafk", "help", "join", "tag", "tagreg", "userlog", "channeldist", "unmute",
                   "channelinfo"]:
        called = True
    print("Firing...")
    if "zenith" in auths:
        if command == "oauth":
            print(discord.utils.oauth_url(AUTH_TOKEN))
        if command == "names":
            count = 0
            text = ""
            for member in message_in.server.members:
                if count >= int(params[0]):
                    break
                else:
                    count += 1
                text += member.name + "\n"
            output.append((text, None))
        if command == "purge":
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
        if command == "firstjoins":
            joins = {}
            print("Running firstjoins")
            cursor = overwatch_db.message_log.find({})

            cursor.sort("date", 1)
            async for mess in cursor:
                print("mess")
                if mess["userid"] not in joins.keys():
                    joins[mess["userid"]] = mess["date"]

            print("done")
            for key in joins.keys():
                print(key)
                await overwatch_db.userinfo.update_one({"userid": key}, {"$unset": {"server_joins": ""}})
                await overwatch_db.userinfo.update_one({"userid": key}, {"$addToSet": {"server_joins": joins[key]}})

        if command == "mostactive":
            output.append(await generate_activity_hist(message_in))

        elif command == "channelsdist":
            output.append(await generate_user_channel_activity_hist(message_in, params[0]))
        elif command == "superlog":
            await rebuild_logs(message_in)
        elif command == "rebuildnicks":
            await rebuild_nicks(message_in)
        elif command == "wa":
            await wolfram(message_in)
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

    if "trusted" in auths:
        if command == "ui":
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

        if command == "get_role_members":
            pass
        elif command == "serverlog":
            result = await overwatch_db.config.find_one({"type": "log"})
            if not params:
                await client.send_message(message_in.channel, "Server log is currently {state}".format(state="on" if result["server_log"] else "off"))
            else:
                new_state = parse_bool(params[0])
                await overwatch_db.config.update_one({"type": "log"}, {"$set": {"server_log": new_state}}, upsert=True)
                STATES["server_log"] = new_state
                await client.send_message(message_in.channel, "Setting server log to {state}".format(state="on" if result["server_log"] else "off"))

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
            output.append(await output_join_link(message_in.server.get_member(params[0])))
        elif command == "find":
            await output_find_user(message_in)
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
        elif command == "unban":
            user_id = params[0]
            user = await client.get_user_info(user_id)
            await client.unban(message_in.server, user)
            output.append(("Unbanned: {mention}".format(mention="<@!" + user_id + ">"), None))

        elif command == "temprole":
            global temproles
            if params[0] in ["add", "+"]:
                member = message_in.server.get_member(params[1])
                parsed_dur = False
                role_name = ""
                dur = None
                for param in params[2:]:
                    if not parsed_dur:
                        try:
                            dur = int(param)
                            parsed_dur = True
                        except ValueError:
                            role_name += param + " "
                    else:
                        reason = param
                role = await get_role_from_name(message_in.server, role_name)
                if not role:
                    await client.send_message(message_in.channel, "Role not recognized")
                    return
                if not dur:
                    await client.send_message(message_in.channel, "Duration not recognized")
                    return
                else:
                    dur = timedelta(minutes=dur)
                    dur = datetime.now() - dur
                await temproles.add_role(member, role, dur)
                text = "Adding role {rolename} to {mention} [{id}] for {dur}".format(rolename=role.mention, mention=member.mention, id=member.id,
                                                                                             dur=dur)
                text = await scrub_text(text, message_in.channel)
                output.append((text, None))
            if params[0] == "tick":
                await temproles.tick()
        elif command == "mute":
            role = await get_role(message_in.server, "110595961490792448")
            member = message_in.server.get_member(params[0])
            if len(params) == 2:
                try:
                    dur = int(params[1])
                    if dur == 600:
                        dur = 10
                    elif dur == 3600:
                        dur = 60
                    dur = timedelta(minutes=dur)
                    dur = datetime.now() + dur
                    # dur = dur
                except ValueError:
                    dur = await parse_date(date_text="in " + " ".join(params[1:]))
            else:
                dur = await parse_date(date_text="in " + " ".join(params[1:]))
            print(dur)

            if dur != 0 and not dur:
                await client.send_message(message_in.channel, "Duration not recognized")
                return
            if not member:
                await client.send_message(message_in.channel, "Member not recognized")
                return
            # dur = datetime.now() + dur
            duration = dur - datetime.now()
            # micros = dur.microsecond
            complete = 1000000
            duration = duration + timedelta(microseconds=499999)
            duration = duration // 1000000 * 1000000

            output.append(("Muting {mention} [{id}] for {dur}".format(mention=member.mention, id=member.id, dur=duration), None))
            await temproles.add_role(member=member, role=role, minutes=dur)
    if "trusted" not in auths:
        return
    if called:
        await client.delete_message(message_in)
    if output:
        for item in output:
            await send(destination=message_in.channel, text=item[0], send_type=item[1])

async def unmute(member):
    await client.server_voice_state(member, mute=False)

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
    invite = await client.create_invite(vc, max_uses=1, max_age=6)
    if invite:
        return (invite.url, None)
    else:
        return "User not in a visible voice channel"

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
        status = "Not part of the server"
    embed.add_field(name="Status", value=status, inline=False)
    if avatar_link:
        embed.set_thumbnail(url=avatar_link)
        color = utils_image.average_color_url(avatar_link)
        embed.add_field(name="Avatar", value=avatar_link.replace(".webp", ".png"), inline=False)
        hex_int = int(color, 16)
        embed.colour = discord.Colour(hex_int)
        embed.set_thumbnail(url=shorten_link(target_member.avatar_url))
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
    voice = random.choice(constants.VOICE_LINES)
    sent = await client.send_message(channel, voice)
    await client.edit_message(sent,
                              voice + " (" + str(
                                  (sent.timestamp - timestamp).total_seconds() * 500) + " ms) " +
                              message.author.mention)

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
    if role[1] > 85:
        return rolename_role_dict[role[0]]
    else:
        return None

# Tagging
async def add_tag(string, note, action, categories):
    await trigger_str_collection.update_one({"string": string}, {
        "$addtoset": {"actions"   : action,
                      "note"      : note,
                      "categories": {"$each": categories}}})

async def tag_str(trigger, message, regex):
    if not regex:
        trigger = re.escape(trigger)

    # if trigger_str_collection.find_one({"trigger": string}):
    #     await tag_update(message)
    #     return

    # if string == "reset":
    #     await trigger_str_collection.remove({})
    #     await trigger_str_collection.create_index([("trigger", pymongo.DESCENDING)], unique=True)
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
            await trigger_str_collection.insert_one(
                {"trigger": trigger, "action": action_list[0], "duration": action_list[1], "note": action_list[2]})



            #
            # else:
            #     await client.edit_message(interact, "Syntax not recognized. Please restart")
            #     return
            #     # result = await trigger_str_collection.insert_one(database_entry)
            #     # print(result)

async def parse_triggers(message) -> list:
    response_docs = []
    content = message.content
    # trigger_cursor = trigger_str_collection.find()
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
        invite = await client.get_invite(inv_link)
        if invite.server.id == message.server.id:
            if message.channel.id in [constants.CHANNELNAME_CHANNELID_DICT["general-discussion"], constants.CHANNELNAME_CHANNELID_DICT["overwatch-discussion"]]:
                party = re.search(r"(^\[)\w+.\w+\]", invite.channel.name, flags=re.IGNORECASE)
                if party:
                    response_docs.append({"action": "delete", "note": "Please keep LFGs to <#182420486582435840> <#185665683009306625>"})
        else:
            response_docs.append({"action": "external_invite", "invite": invite, "note": "Please don't link other discord servers here"})

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
                    "deleted {author}'s message from {channel} ```Invite to {server_name}``` because: {note}".format(author=message.author.mention,
                                                                                                                     channel=message.channel.mention,
                                                                                                                     server_name=doc["invite"].server.name,
                                                                                                                     note=doc["note"]), "deletion")
                await log_automated(
                    "deleted an external invite to " + str(doc["invite"].url) + " from " + message.author.mention + " in " + message.channel.mention, "alert")
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
    if message_list:
        gist = gistClient.create(name="User Log", description=(await client.get_user_info(userid)).name + "'s Logs",
                                 public=False,
                                 content="\n".join(message_list))
        return (gist["Gist-Link"], None)
    else:
        return ("No logs found", None)

async def output_first_messages(userid, message_in):
    member = message_in.server.get_member(userid)
    cursor = overwatch_db.message_log.find({"userid": member.id}, limit=50)
    cursor.sort("date", 1)
    message_list = []
    async for message_dict in cursor:
        message_list.append(await format_message_to_log(message_dict))

    logs = message_list
    gist = gistClient.create(name="First Messages", description=member.name + "'s First Messages",
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

async def generate_user_channel_activity_hist(message_in, userid):
    hist = defaultdict(int)
    async for doc in message_log_collection.find({"userid": userid}):
        hist[doc["channel_id"]] += len(doc["content"].split(" "))
    named_hist = {}
    hist = dict(hist)
    for key in hist.keys():

        try:
            named_hist[constants.CHANNELID_CHANNELNAME_DICT[key]] = hist[key]
        except:
            try:
                name = message_in.server.get_channel(key).name
                named_hist[name] = hist[key]
            except:
                name = key
                named_hist[name] = hist[key]

    sort = sorted(named_hist.items(), key=lambda x: x[1])
    hist = "\n".join("%s,%s" % tup for tup in sort)

    gist = gistClient.create(name="Channelhist",
                             description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                             public=False,
                             content=hist)
    return (gist["Gist-Link"], None)

async def generate_activity_hist(message):
    if message.content.startswith("`mostactive"):
        print("STARTING")
        activity = defaultdict(int)
        count = 0
        async for mess in message_log_collection.find({"date": {"$gt": "2016-11-18"}}):
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
    except:
        try:
            await import_user(SERVERS["OW"].get_member(message_dict["userid"]))
            cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
            name = cursor["names"][-1]

        except:
            name = message_dict["userid"]

    content = message_dict["content"].replace("```", "")
    try:
        channel_name = constants.CHANNELID_CHANNELNAME_DICT[str(message_dict["channel_id"])]
    except KeyError:
        channel_name = "Unknown"
    return "[" + message_dict["date"][:19] + "][" + channel_name + "][" + name + "]:" + \
           content

async def output_channel_dist(channel, days):
    activity = defaultdict(int)
    count = 0
    date = datetime.utcnow() - timedelta(days=int(days))
    date = date.isoformat(" ")
    print(date)
    async for mess in message_log_collection.find({"date": {"$gt": date}, "channel_id": channel.id}):
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

async def log_automated(description: object, type) -> None:
    action = ("At " + str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")) + ", I automatically " + str(description))
    if type == "alert":
        target = constants.CHANNELNAME_CHANNELID_DICT["alerts"]
    elif type == "deletion" or type == "autorole":
        target = constants.CHANNELNAME_CHANNELID_DICT["bot-log"]

    else:
        target = constants.CHANNELNAME_CHANNELID_DICT["spam-channel"]
    await client.send_message(client.get_channel(target), action)

async def log_action(action, detail):
    bot_log = client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["bot-log"])
    server_log = client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["server-log"])
    voice_log = client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["voice-channel-output"])
    # server_log = client.get_channel("152757147288076297")
    time = datetime.utcnow().isoformat(" ")
    time = time[5:19]
    time = time[6:19] + " " + time[0:5]
    if any(key in ["before", "after", "content", "mention"] for key in detail.keys()):
        for key in detail.keys():
            if key == "before" and isinstance(detail["before"], str):
                target = "before"
            elif key == "after" and isinstance(detail["before"], str):
                target = "after"
            elif key == "content":
                target = "content"
            elif key == "mention":
                target = "mention"
            else:
                continue
            new = []
            for word in re.split(r"\s", detail[target]):
                if regex_test(
                        r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)",
                        word):
                    word = "<" + word + ">"
                new.append(word)
            detail[target] = " ".join(new)
            if action not in ["leave", "ban"]:
                detail[target] = await scrub_text(detail[target], server_log)

    #
    # if "content" in detail.keys():
    #     new_words = []
    #     words = re.split(r"\s", detail["content"])
    #     for word in words:
    #         match = re.match(r"(<@!?\d+>)|(@everyone)|(@here)", word)
    #         if match:
    #             id = match.group(0)
    #             if id not in ["@everyone", "@here"]:
    #                 id = re.search(r"\d+", id)
    #                 id = id.group(0)
    #                 member = client.get_server(constants.OVERWATCH_SERVER_ID).get_member(id)
    #                 perms = server_log.permissions_for(member)
    #                 if perms.read_messages:
    #                     new_words.append(r"\@" + member.name)
    #                 else:
    #                     new_words.append(word)
    #             else:
    #                 new_words.append("\\" + word)
    #         else:
    #             new_words.append(word)
    #
    #     detail["content"] = " ".join(new_words)
    #
    # if "before" in detail.keys():
    #     new_words = []
    #     words = re.split(r"\s", detail["before"])
    #     for word in words:
    #         match = re.match(r"(<@!?\d+>)|(@everyone)|(@here)", word)
    #         if match:
    #             id = match.group(0)
    #             if id not in ["@everyone", "@here"]:
    #                 id = re.search(r"\d+", id)
    #                 id = id.group(0)
    #                 member = client.get_server(constants.OVERWATCH_SERVER_ID).get_member(id)
    #                 perms = server_log.permissions_for(member)
    #                 if perms.read_messages:
    #                     new_words.append(r"\@" + member.name)
    #                 else:
    #                     new_words.append(word)
    #             else:
    #                 new_words.append("\\" + word)
    #         else:
    #             new_words.append(word)
    #     detail["before"] = " ".join(new_words)
    # if "after" in detail.keys():
    #     new_words = []
    #     words = re.split(r"\s", detail["after"])
    #     for word in words:
    #         match = re.match(r"(<@!?\d+>)|(@everyone)|(@here)", word)
    #         if match:
    #             id = match.group(0)
    #
    #             if id not in ["@everyone", "@here"]:
    #                 id = re.search(r"\d+", id)
    #                 id = id.group(0)
    #                 member = client.get_server(constants.OVERWATCH_SERVER_ID).get_member(id)
    #                 perms = server_log.permissions_for(member)
    #                 if perms.read_messages:
    #                     new_words.append(r"\@" + member.name)
    #                 else:
    #                     new_words.append(word)
    #             else:
    #                 new_words.append("\\" + word)
    #         else:
    #             new_words.append(word)
    #     detail["after"] = " ".join(new_words)
    # if "mention" in detail.keys():
    #     id = re.search(r"\d+", detail["mention"])
    #     id = id.group(0)
    #     if id == "129706966460137472":
    #         return
    #     member = client.get_server(constants.OVERWATCH_SERVER_ID).get_member(id)
    #     if member:
    #         perms = server_log.permissions_for(member)
    #         if perms and perms.read_messages:
    #             detail["mention"] = member.name

    time = "`" + time + "`"

    if action == "delete":
        message = "{time} :wastebasket: [DELETE] [{channel}] [{mention}] [{id}]:\n{content}".format(time=time, channel=detail["channel"],
                                                                                                    mention=detail["mention"],
                                                                                                    id=detail["id"],
                                                                                                    content=detail[
                                                                                                        "content"])
        target_channel = server_log
        await overwatch_db.server_log.insert_one(
            {"date"   : datetime.utcnow().isoformat(" "), "action": action, "channel": detail["channel"], "mention": detail["mention"], "id": detail["id"],
             "content": detail["content"]})
    elif action == "edit":
        message = "{time} :pencil: [EDIT] [{channel}] [{mention}] [{id}]:\n`-BEFORE:` {before} \n`+ AFTER:` {after}".format(
            time=time, channel=detail["channel"], mention=detail["mention"], id=detail["id"], before=detail["before"],
            after=detail["after"])
        target_channel = server_log
        await overwatch_db.server_log.insert_one(
            {"date"  : datetime.utcnow().isoformat(" "), "action": action, "channel": detail["channel"], "mention": detail["mention"], "id": detail["id"],
             "before": detail["before"], "after": detail["after"]})

    elif action == "join":
        message = "{time} :inbox_tray: [JOIN] [{mention}] [{id}]. Account Age: {age}".format(time=time,
                                                                                             mention=detail["mention"],
                                                                                             id=detail["id"],
                                                                                             age=detail["age"])
        target_channel = server_log
        await overwatch_db.server_log.insert_one({"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"], "age": detail["age"]})
    elif action == "leave":
        message = "{time} :outbox_tray: [LEAVE] [{mention}] [{id}]".format(time=time, mention=detail["mention"],
                                                                           id=detail["id"])
        target_channel = server_log
        await overwatch_db.server_log.insert_one({"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"]})

    elif action == "ban":
        message = "{time} :no_entry_sign: [BAN] [{mention}] [{id}] Name: {name} {nick}".format(time=time, mention=detail["member"].mention,
                                                                                               id=detail["member"].id,
                                                                                               name=detail["member"].name + "#" + detail[
                                                                                                   "member"].discriminator, nick=
                                                                                               detail["member"].nick if detail["member"].nick else "")
        target_channel = server_log
        await overwatch_db.server_log.insert_one({"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["member"].id, "mention": detail["member"].mention})

    elif action == "unban":
        message = "{time} :white_check_mark:  [UNBAN] [{mention}] [{id}]".format(time=time, mention="<@!" + detail["id"] + ">",
                                                                                 id=detail["id"])

        target_channel = server_log
        await overwatch_db.server_log.insert_one({"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"], "mention": detail["mention"]})
    elif action == "role_change":
        # print("TRIGGERING ROLE CHANGE")
        target_channel = server_log

        member = detail["member"]
        old_roles = detail["old_roles"]
        new_roles = detail["new_roles"]
        # old_role_ids = [role.id for role in old_roles]
        new_role_ids = " ".join([role.id for role in new_roles])
        await overwatch_db.userinfo.update_one({"userid": member.id}, {"$set": {"roles": new_role_ids}})
        before = " ".join([role.mention for role in old_roles])
        after = " ".join([role.mention for role in new_roles])
        mention = member.mention
        mention = await scrub_text(mention, target_channel)

        message = "{time} :pencil: [ROLECHANGE] [{mention}] [{id}]:\n`-BEFORE:` {before} \n`+ AFTER:` {after}".format(time=time, mention=mention,
                                                                                                                      id=member.id, before=before, after=after)
        message = await scrub_text(message, target_channel)
    elif action == "voice_update":
        before = detail["before"]
        voice_state = before.voice
        if not voice_state.voice_channel:
            before = "Joined Voice"
        else:
            before = voice_state.voice_channel.name
        after = detail["after"]
        voice_state = after.voice
        if not voice_state.voice_channel:
            after = ":Left Voice:"
        else:
            after = voice_state.voice_channel.name

        now = datetime.utcnow()
        threshold = timedelta(minutes=5)
        ago = now - threshold
        date_text = ago.isoformat(" ")

        movecount = await (overwatch_db.server_log.find({"action": action, "id": detail["id"], "date": {"$gt": date_text}}).count())

        if movecount < 5:
            emoji = ":white_check_mark:"
        elif movecount < 10:
            emoji = ":grey_question:"
        elif movecount < 15:
            emoji = ":warning:"
        elif movecount < 20:
            emoji = ":exclamation:"
        else:  # movecount < 25:
            emoji = ":bangbang:"
        target_channel = voice_log
        if voice_state.voice_channel:
            in_room = str(len(voice_state.voice_channel.voice_members))
            room_cap = str(voice_state.voice_channel.user_limit)
        else:
            in_room = "0"
            room_cap = "0"
        message = "{emoji} {date} {mention} : `{before}` → `{after}` [{usercount}/{userlimit}] ({count})".format(emoji=emoji, date=time,
                                                                                                                 mention="<@!" + detail["id"] + ">",
                                                                                                                 before=before, after=after, usercount=in_room,
                                                                                                                 userlimit=room_cap, count=movecount)

        await overwatch_db.server_log.insert_one({"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"]})


    else:
        print("fail")
        return
    message = await scrub_text(message, voice_log)
    if STATES["server_log"]:
        await client.send_message(target_channel, message)

# Database
# Database Query
async def import_message(mess):
    messInfo = await parse_message_info(mess)
    try:
        await message_log_collection.insert_one(messInfo)
    except:
        pass
        # messText = await format_message_to_log(messInfo)
        # await message_to_stream(messInfo)
        # await client.send_message(STREAM, await message_to_stream(messInfo))

async def import_to_user_set(member, set_name, entry):
    await userinfo_collection.update_one(
        {"userid": member.id},
        {
            "$addToSet": {set_name: entry}
        }
    )

async def import_user(member):
    """

    :type member: discord.Member
    """
    user_info = await parse_member_info(member)
    result = await userinfo_collection.update_one(
        {"userid": member.id},
        {
            "$addToSet": {"nicks": {
                "$each": [user_info["nick"], user_info["name"], user_info["name"] + "#" + str(user_info["discrim"])]},
                "names"          : user_info["name"],
                "avatar_urls"    : user_info["avatar_url"],
                "server_joins"   : user_info["joined_at"]},
            "$set"     : {"mention_str": user_info["mention_str"],
                          "created_at" : user_info["created_at"]},

        }
        , upsert=True
    )
    pass

async def export_user(member_id):
    """

    :type member: discord.Member
    """
    userinfo = await userinfo_collection.find_one(
        {"userid": member_id}, projection={"_id": False, "mention_str": False}
    )
    if not userinfo:
        return None
    list = userinfo["avatar_urls"]
    if len(list) > 0 and len(list[0]) > 0:
        try:
            shortened_list = []
            for link in list:
                shortened_list.append(await shorten_link(link))
            userinfo["avatar_urls"] = shortened_list
        except:
            pass
    return userinfo

# Utils
async def send(destination, text, send_type):
    if isinstance(destination, str):
        destination = await client.get_channel(destination)

    if send_type == "rows":
        message_list = multi_block(text, True)
        for message in message_list:
            await client.send_message(destination, "```" + message + "```")
        return
    if send_type == "list":
        text = str(text)[1:-1]

    text = str(text)
    text = text.replace("\n", "<NL<")
    lines = textwrap.wrap(text, 2000, break_long_words=False)

    for line in lines:
        if len(line) > 2000:
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
    """

    :type regex_match: re.match
    :type message: discord.Message
    """
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

async def fuzzy_match(*args):
    if len(args) == 2:
        count = 1
    else:
        count = args[2]
    nick_to_find = args[1]
    mess = args[0]

    nick_id_dict = {}

    mongo_cursor = userinfo_collection.find()
    async for userinfo_dict in mongo_cursor:
        try:
            for nick in userinfo_dict["nicks"]:
                # print(userinfo_dict["nicks"])
                nick_id_dict.setdefault(nick, []).append(userinfo_dict["userid"])
                # nickIdDict.setdefault(nick, []).append(id)
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
                # auth = await credential(messageCheck.author, "mod")
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

async def scrub_invite(text):
    new_words = []
    words = re.split(r"\s", text)
    for word in words:
        # Roles
        match = re.match(r"(<@&\d+>)", word)
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

async def parse_date(date_text):

    res = dateparser.parse(date_text)
    return res
# Scrim
async def scrim_end():
    global scrim
    await scrim.end()
    scrim = None

async def scrim_reset():
    global scrim

    for pair in scrim.team1.vc.overwrites:
        await client.delete_channel_permissions(scrim.team1.vc, pair[0])
    for pair in scrim.team2.vc.overwrites:
        await client.delete_channel_permissions(scrim.team2.vc, pair[0])

async def scrim_manage(message):
    auths = await get_auths(message.author)

    command = message.content.replace("..scrim ", "")
    command_list = command.split(" ")

    if "mod" in auths or "host" in auths:
        if not scrim and command_list[0] == "start":
            await scrim_start(message)
            # if command_list[0] == "manager":
            #     command_list = await mention_to_id(command_list)
            #     if command_list[1] == "list":
            #         managers = await scrim.get_managers()
            #         manager_list = [["Name", "ID"]]
            #         for manager_id in managers:
            #             member = message.server.get_member(manager_id)
            #             manager_list.append([member.name, member.id])
            #         await send(destination=message.channel, text=manager_list, send_type="rows")


            # else:
            #     await overwatch_db.scrim.find_one_and_update({"userid": command_list[1]},
            #                                                  {"$bit": {"manager": {"xor": 1}}})
        if command_list[0] == "end":
            await overwatch_db.scrim.update_many({}, {"$set": {"active": False, "pos": 0}})
            await scrim_end()
        if command_list[0] == "next":
            await scrim.start()
        if command_list[0] == "add":
            await scrim.force_register(message)
    if scrim:
        try:
            # managers = await scrim.get_managers()
            # if command_list[0] == "commands":
            #     list = [
            #         ["Command", "Description"],
            #         ["Public", ""],
            #         ["`scrim list", "Lists each active participant in the scrim sorted by SR"],
            #         ["`scrim teams", "Lists each active participant sorted by team and SR"],
            #         ["`scrim join", "Starts the registration process. Have your battletag ready"],
            #         ["`scrim leave", "Leaves the scrim and removes you from the active participants list"],
            #         ["", ""],
            #         ["Manager", ""],
            #         ["`scrim reset", "Unassigns all active members from their teams"],
            #         ["`scrim end", ""],
            #         ["`scrim move <@mention> <team>", "Assigns a member to a team. Ex: `scrim move @Zenith#7998 1"],
            #         ["`scrim remove <@mention>", "Removes a member from the active participant pool"],
            #         ["`scrim autobalance", "Automatically sorts placed members into teams"],
            #         ["`scrim ping", "Pings every member assigned to a team"],
            #     ]
            #     await send(destination=message.channel, text=list, send_type="rows")
            #     # text = pretty_column(list, True)
            #     # await pretty_send(message.channel, text)


            if command_list[0] == "help":
                list = [["Command", "Details", "Role"],
                        ["..scrim join", "Joins the scrim. Bot will PM you", "Everyone"],
                        ["..scrim list", "Lists the members in the queue", "Everyone"],
                        ["..scrim start", "Starts up the scrimbot.", "Host+"],
                        ["..scrim end", "Ends the scrim and cleans up", "Host+"],
                        ["..scrim next", "Pulls the next 12 players and forms teams", "Host+"]
                        ]
                await send(destination=scrim.output, text=list, send_type="rows")
            if command_list[0] == "list":
                await scrim.output_teams_list()
                await client.delete_message(message)

            if command_list[0] == "join":
                # await scrim.add_user(message.author)
                await scrim.serve_scrim_prompt(message.author)
                await client.delete_message(message)

            if command_list[0] == "leave":
                await scrim.leave(message.author)


        except IndexError:
            await client.send_message(message.channel, "Syntax error")
    pass

async def scrim_start(message):
    global scrim
    server = message.server
    # mod_role = ROLENAME_ROLE_DICT["MODERATOR_ROLE"]
    mod_role = await get_role(client.get_server("236343416177295360"), "260186671641919490")
    # super_manager_role = await get_role(client.get_server("236343416177295360"), "261331682546810880")

    vc_overwrite_everyone = discord.PermissionOverwrite(connect=False, speak=True)
    vc_overwrite_mod = discord.PermissionOverwrite(connect=True)
    vc_overwrite_super_manager = discord.PermissionOverwrite(connect=True)

    text_overwrite_everyone = discord.PermissionOverwrite(read_messages=False)
    # text_overwrite_mod = discord.PermissionOverwrite(read_messages=True)
    # super_manager_perms_text = discord.PermissionOverwrite(read_messages=True)

    vc_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=vc_overwrite_everyone)
    vc_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=vc_overwrite_mod)
    # vc_permission_super_manager = discord.ChannelPermissions(target=super_manager_role, overwrite=vc_overwrite_super_manager)

    text_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=text_overwrite_everyone)

    # text_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=text_overwrite_mod)
    #
    # admin_text = discord.ChannelPermissions(target=ROLENAME_ROLE_DICT["ADMINISTRATOR_ROLE"], overwrite=admin_perms_text)

    scrim1_vc = await client.create_channel(server, "[Scrim] Team 1", vc_permission_everyone, vc_permission_mod,
                                            type=discord.ChannelType.voice)
    scrim2_vc = await client.create_channel(server, "[Scrim] Team 2", vc_permission_everyone, vc_permission_mod,
                                            type=discord.ChannelType.voice)
    scrim1 = ScrimTeam("1", scrim1_vc)
    scrim2 = ScrimTeam("2", scrim2_vc)

    scrim_spectate = await client.create_channel(server, "[Scrim] Spectate", type=discord.ChannelType.voice)

    scrim_text = await client.create_channel(server, "Scrim", text_permission_everyone, type=discord.ChannelType.text)

    scrim = ScrimMaster(scr1=scrim1, scr2=scrim2, txt=scrim_text, spec=scrim_spectate, output=message.channel)
    # mod_list = await get_moderators(message.server)
    # for mod in mod_list:
    #     await overwatch_db.scrim.update_one({"userid": mod.id}, {"$set": {"manager": 1}}, upsert=True)

    time = datetime.utcnow().isoformat(" ")
    # pin_marker = await client.send_message(client.get_channel("262494034252005377"), "Highlights from " + time[5:10])
    # await client.pin_message(pin_marker)
    await client.move_channel(scrim.spectate, 1)
    await client.move_channel(scrim.team1.vc, 2)
    await client.move_channel(scrim.team2.vc, 3)

    pass

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

async def get_response_int(target) -> discord.Message:
    """

    :type target: discord.User
    """

    def check(msg):
        if msg.server == None and msg.author.id == target.id:
            try:
                int(msg.content)
                return True
            except ValueError:
                return False

    return await client.wait_for_message(timeout=30, author=target, check=check)

# async def get_mentions(mess, auth):
#     target = mess.author
#
#     await client.send_message(target, "Automated Mention Log Fetcher Starting Up!")
#     await client.send_message(target, "Please respond with the number in the parentheses (X)")
#     if auth == "mod":
#         await client.send_message(target,
#                                   "Would you like to query personal mentions (1), admin/mod mentions (2), or both (3)?")
#
#         response_mess = await get_response_int(target)
#         if response_mess is not None:
#             await get_logs_mentions(response_mess.content, mess)
#         else:
#             await client.send_message(target, "You have taken too long to respond! Please restart.")
#     else:
#         await get_logs_mentions("1", mess)

# Projects
async def wolfram(message):
    command = message.content.replace("..wa ", "")
    res = WA_client.query(command)
    try:
        podlist = res["pod"]
        print(ascii(res))
    except:
        print(ascii(res))
        print("LOLFAIL")
        return
    numpods = int(res["@numpods"])
    keydict = {}
    options = ""
    print("numpods = " + str(numpods))
    print(res["@numpods"])
    try:
        for num in range(0, numpods - 1):
            pod = podlist[num]
            options += "[" + str(num) + "] " + pod["@title"] + "\n"
            print("NUM = " + str(pod["@numsubpods"]))
            for sub_num in range(0, int(pod["@numsubpods"])):
                subpod = pod["subpod"]
                if subpod["@title"] != "":
                    options += "    [" + str(num) + "." + str(sub_num) + "] " + subpod["@title"] + "\n"
            keydict[num] = pod
        options = await client.send_message(message.channel, options)
    except:
        pass

    def check(msg):
        if message.server == msg.server and msg.author.id == message.author.id and message.channel == msg.channel:
            if re.match(r"^\d*$", msg.content):
                return True
        return False

    response = await client.wait_for_message(timeout=15, check=check)
    try:
        response = int(response.content)
        pod = podlist[response]
        subpods = []
        text = ""
        if pod["@numsubpods"] == "1":
            subpods.append(pod["subpod"])

        else:
            for x in pod["subpod"]:
                subpods.append(x)

        for subpod in subpods:
            img = (subpod["img"])["@src"]
            img = shorten_link(img)
            text += img + "\n"
        await client.send_message(message.channel, text)

    except:
        print(traceback.format_exc())
    await client.delete_message(options)

async def lfg_warner(found_message, warn_type, warn_user, channel):
    """

    :param channel: discord.Channel
    :param warn_user: discord.Member
    :param found_message: discord.Message
    :type warn_type: str
    """

    lfg_text = ("You're probably looking for <#182420486582435840> or <#185665683009306625>."
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
        result = await userinfo_collection.find_one_and_update(
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

pass

async def message_to_stream(mess_dict):
    string = ""
    string += "`<" + mess_dict["date"][:-7] + ">` "
    string += "**[" + constants.CHANNELID_CHANNELNAME_DICT[str(mess_dict["channel_id"])] + "]** "

    item = await export_user(mess_dict["userid"])
    string += "[" + item["nicks"][-1] + "]: "

    string += ":small_blue_diamond:" + mess_dict["content"]

    # await stream.add(string=string)
    return string

async def get_from_find(message):
    reg = re.compile(r"(?!ID: ')(\d+)(?=')", re.IGNORECASE)
    user_id = ""
    async for mess in client.logs_from(message.channel, limit=10):
        if "Fuzzy Search:" in mess.content:
            match = reg.search(mess.content)
            if match is not None:
                user_id = match.group(0)
    return user_id

async def temp_apply_role(member, role, duration):
    pass

async def apply_role(member, role):
    pass

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
                await client.remove_roles(member, tick[1])
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
            print("None found: " + member.name)

    async def add_role(self, member, role, minutes):
        # end_time = datetime.utcnow() + minutes
        end_time = minutes
        self.temproles.append(temprole(member.id, role, end_time, self.server))
        await client.add_roles(member, role)

        await overwatch_db.roles.insert_one(
            {"type": "temp", "member_id": member.id, "role_id": role.id, "end_time": str(end_time)})

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
        if self.end < datetime.utcnow():
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

client.run(AUTH_TOKEN, bot=True)
