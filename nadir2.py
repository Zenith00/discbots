import discord
import motor.motor_asyncio
import pymongo
from overwatch_api import OverwatchAPI
from unidecode import unidecode

from constants import *
from utils_text import *
from utils_parse import *
import heapq
import logging
import math
import random
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO

import discord
import motor.motor_asyncio
import pymongo
import wolframalpha
from asteval import Interpreter
from fuzzywuzzy import fuzz
from imgurpython import ImgurClient
from overwatch_api import OverwatchAPI
from pymongo import ReturnDocument
from simplegist.simplegist import Simplegist
import constants
import unicodedata
from utils_text import *
from utils_parse import *
from unidecode import unidecode
from TOKENS import *


client = discord.Client()
scrim = None
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
ready = False
OW_Channels = None
CHANNELS = {
    "overwatc_d": "109672661671505920",
    "general_d": "94882524378968064",
    "competitive_d": "107255001163788288",
    "lore_d": "180471683759472640",
    "console_lfg": "185665683009306625",
    "pc-lfg": "182420486582435840",

    "esports_d": "233904315247362048",

    "modchat": "106091034852794368",
    "server_log": "152757147288076297",
    "voice_channel_output": "200185170249252865",
    "mod_notes": "188949683589218304",
    "content-creation": "95324409270636544",
    "competitive_recruitment": "170983565146849280",
    "tournament_announcement": "184770081333444608",
    "trusted": "170185225526181890",
    "lf_scrim": "177136656846028801",

    "fanart": "168567769573490688",

    "announcements": "95632031966310400",
    "spam_channel": "209609220084072450",
    "jukebox": "176236425384034304",
    "rules_and_info": "174457179850539009",
    "warning_log": "170179130694828032",
    "bot_log": "147153976687591424",
    "nadir_audit_log": "240320691868663809",
    "alerts": "252976184344838144",
}

ow_db = mongo_client.overwatch


class ScrimTeam:
    def __init__(self, id, channel):
        self.members = []
        self.name = id
        self.vc = channel


class ScrimMaster:
    def __init__(self, scr1, scr2, txt, spec):
        self.team1 = scr1
        self.team2 = scr2
        # self.members = {}
        self.text = txt
        self.spectate = spec
        self.masters = []

    async def get_managers(self):
        managers = []
        manager_cursor = ow_db.scrim.find({"manager": 1})
        async for manager in manager_cursor:
            managers.append(manager["userid"])

        return managers

    async def end(self):
        await client.delete_channel(self.team1.vc)
        await client.delete_channel(self.team2.vc)
        await client.delete_channel(self.text)
        await client.delete_channel(self.spectate)

    async def assign(self, member, team):
        await self.deauth(member)
        return await self.auth(member, team)

    async def reset(self, message):
        cursor = ow_db.scrim.find({"active": True})
        async for person in cursor:
            await self.deauth(message.server.get_member(person["userid"]))
            # await ow_db.scrim.update_many({"active": True}, {"$set": {"team": "0"}})

    async def auth(self, member, team):
        print("Assigning {} to {}".format(member.id, team))

        if team == "0":
            await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"team": "0"}})
            return member.mention + " unassigned"
        if team == "1":
            target_team = self.team1
        else:  # team == "2":
            target_team = self.team2

        # self.members[member.id] = team
        await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"team": target_team.name}})

        target_team.members.append(member.id)
        user_overwrite_vc = discord.PermissionOverwrite(connect=True)
        await client.edit_channel_permissions(target_team.vc, member, user_overwrite_vc)
        return member.mention + " added to team " + target_team.name

    async def deauth(self, member):
        # try:
        #     target = self.members[member.id]
        # except KeyError:
        #     return "User is not in a team"
        target_member = await         ow_db.scrim.find_one({"userid": member.id})
        if not target_member:
            print("FAILED TO FIND {}".format(member.id))
            return
        target = target_member["team"]
        if target == "1":
            target_team = self.team1
        elif target == "2":
            target_team = self.team2
        else:
            return
        #
        # try:
        #     target_team.members.remove(member.id)
        # except:
        #     print(traceback.format_exc())
        #     print(target_team.members)
        # del self.members[member.id]

        await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"team": "0"}})
        await client.delete_channel_permissions(target_team.vc, member)
        return member.mention + " removed from team " + target_team.name

    async def add_user(self, member):
        userid = member.id
        await ow_db.scrim.update_one({"userid": userid},
                                     {"$set": {"team": "0", "active": True, "manager": 0}}, upsert=True)

    async def leave(self, member):
        userid = member.id
        await ow_db.scrim.update_one({"userid": userid},
                                     {"$set": {"team": "0", "active": False, "manager": 0}}, upsert=True)
        return "Removed " + member.mention + " from the active user pool"

    async def register(self, member, btag):
        sr = await get_sr(btag)
        if sr == "0":
            await client.send_message(member,
                                      "BTag not recognized. Please make sure that capitalization and spelling are both correct, and that you have placed on this account")
            sr = "unplaced"
        await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"rank": sr, "btag": btag, "active": True}})
        return sr

    async def refresh(self, member):
        user = await ow_db.scrim.find_one({"userid": member.id})
        await self.register(member, user["btag"])


@client.event
async def on_ready():
    global ready
    global OW_Channels
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    ready = True
    OW_Channels = ChannelPlex(OVERWATCH_SERVER_ID)


@client.event
async def on_message(message_in):
    if not ready:
        return
    if message_in.author == client.user:
        return

    if message_in.server is None:
        if scrim:
            if regex_test(reg_str=r"^\D.{2,12}#\d{4}$", string=message_in.content):
                await scrim.register(message_in.author, message_in.content)

        else:
            await client.send_message(await client.get_user_info(message_in.ZENITH_ID),
                                      "[{}]: {}".format(message_in.author.name, message_in.content))
        return

    if message_in.channel in [OW_Channels.bot_log, OW_Channels.server_log, OW_Channels.voice_channel_output]: return

    trigger = "`"
    if message_in.content.startswith(trigger):
        command = message_in.content[len(trigger):]
        
        if command.startswith("scrim"): await scrim_manage(message_in)
        


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

    command = message.content.replace("`scrim ", "")
    command_list = command.split(" ")

    if "mod" in auths:
        if not scrim and command_list[0] == "start":
            await scrim_start(message)
        if command_list[0] == "manager":
            command_list = await mention_to_id(command_list)
            if command_list[1] == "list":
                managers = await scrim.get_managers()
                manager_list = [["Name", "ID"]]
                for manager_id in managers:
                    member = message.server.get_member(manager_id)
                    manager_list.append([member.name, member.id])
                text = await pretty_column(manager_list, True)
                await pretty_send(message.channel, text)


            else:
                await ow_db.scrim.find_one_and_update({"userid": command_list[1]},
                                                             {"$bit": {"manager": {"xor": 1}}})
        if command_list[0] == "end":
            await ow_db.scrim.update_many({}, {"$set": {"active": False, "team": "0"}})
            await scrim_end()
    if scrim:
        try:
            managers = await scrim.get_managers()
            if command_list[0] == "commands":
                list = [
                    ["Command", "Description"],
                    ["Public", ""],
                    ["`scrim list", "Lists each active participant in the scrim sorted by SR"],
                    ["`scrim teams", "Lists each active participant sorted by team and SR"],
                    ["`scrim join", "Starts the registration process. Have your battletag ready"],
                    ["`scrim leave", "Leaves the scrim and removes you from the active participants list"],
                    ["", ""],
                    ["Manager", ""],
                    ["`scrim reset", "Unassigns all active members from their teams"],
                    ["`scrim end", ""],
                    ["`scrim move <@mention> <team>", "Assigns a member to a team. Ex: `scrim move @Zenith#7998 1"],
                    ["`scrim remove <@mention>", "Removes a member from the active participant pool"],
                    ["`scrim autobalance", "Automatically sorts placed members into teams"],
                    ["`scrim ping", "Pings every member assigned to a team"],
                ]
                text = await pretty_column(list, True)
                await pretty_send(message.channel, text)

            if command_list[0] == "list":
                cursor = ow_db.scrim.find({"active": True, "rank": {"$exists": True}})

                cursor.sort("rank", pymongo.DESCENDING)

                userlist = [["Name", "ID", "Manager", "SR", "Team"]]
                async for user in cursor:
                    user_entry = []
                    try:
                        user_entry.append(unidecode(message.server.get_member(user["userid"]).name))
                    except:
                        user_entry.append("MISSING")

                    user_entry.append(user["userid"])
                    if user["manager"] == 1:
                        user_entry.append("True")
                    else:
                        user_entry.append("False")
                    user_entry.append(user["rank"])
                    team = user["team"]
                    if team == "0":
                        user_entry.append("Unassigned")
                    else:
                        user_entry.append("Team " + team)
                    userlist.append(user_entry)

                text = await multi_block(userlist, True)
                for item in text:
                    await pretty_send(message.channel, item)
            if command_list[0] == "teams":
                cursor = ow_db.scrim.find({"active": True, "rank": {"$exists": True}})

                cursor.sort("rank", pymongo.DESCENDING)

                # userlist = [["Name", "ID", "Manager", "SR"]]
                unassigned = [["Unassigned", "", "", ""], ["Name", "ID", "Manager", "SR"]]
                team1 = [["Team 1", "", "", ""], ["Name", "ID", "Manager", "SR"]]
                team2 = [["Team 2", "", "", ""], ["Name", "ID", "Manager", "SR"]]
                async for user in cursor:
                    team = user["team"]

                    if team == "0":
                        target_team = unassigned
                    elif team == "1":
                        target_team = team1
                    elif team == "2":
                        target_team = team2
                    else:
                        print("fail - check teams")
                        return

                    user_entry = []
                    user_entry.append(unidecode(message.server.get_member(user["userid"]).name))
                    user_entry.append(user["userid"])
                    if user["manager"] == 1:
                        user_entry.append("True")
                    else:
                        user_entry.append("False")
                    user_entry.append(user["rank"])
                    try:
                        target_team.append(user_entry)
                    except:
                        print(user)
                text = await multi_column([unassigned, team1, team2], True)
                # text = await pretty_column(userlist, True)
                for item in text:
                    await pretty_send(message.channel, item)
            if command_list[0] == "join":
                # await scrim.add_user(message.author.id)
                result = await scrim_join(message.author)
                print("brasdadastuh")
                await client.send_message(message.channel,
                                          message.author.mention + " has joined the scrim as {} (SR {})\nTo Join, use\n`scrim join".format(result[0], result[1]))
                print("brtuh")
            if command_list[0] == "leave":
                await scrim.leave(message.author)

            if message.author.id in managers:
                # if command_list[0] == "init":
                #     await ow_db.scrim.create_index([("userid", pymongo.DESCENDING)], unique=True)
                if command_list[0] == "reset":
                    await scrim.reset(message)

                if command_list[0] == "ping":

                    cursor = ow_db.scrim.find({"team": "1", "active": True})
                    userlist = []
                    async for user in cursor:
                        userlist.append("<@!" + user["userid"] + ">")

                    await client.send_message(message.channel, "Team 1:\n" + " ".join(userlist))
                    cursor = ow_db.scrim.find({"team": "2", "active": True})
                    userlist = []
                    async for user in cursor:
                        userlist.append("<@!" + user["userid"] + ">")

                    await client.send_message(message.channel, "Team 2:\n" + " ".join(userlist))

                if command_list[0] == "remove":
                    command_list = await mention_to_id(command_list)
                    target = message.server.get_member(command_list[1])
                    result = await scrim.leave(target)
                    await client.send_message(message.channel, result)

                if command_list[0] == "move":
                    target_member = message.mentions[0]
                    response = await scrim.assign(target_member, command_list[2])
                    await client.send_message(message.channel, response)
                    # await scrim.deauth(target_member)
                    # await scrim.auth(target_member, command_list[2])
                if command_list[0] == "autobalance":

                    cursor = ow_db.scrim.find(
                        {"active": True, "rank": {"$ne": "unplaced"}, "team": {"$eq": "0"}},
                        projection=["userid", "rank"])
                    cursor.sort("rank", -1)
                    members = await cursor.to_list(None)

                    print(members)
                    counter = 0
                    spaggheti_counter = 1
                    for user in members:
                        print("Processing... {}".format(user["userid"]))
                        if spaggheti_counter == 5:
                            spaggheti_counter = 1
                        if counter == 0:
                            await scrim.assign(message.server.get_member(user["userid"]), "2")
                            counter +=1
                            continue
                        elif counter == len(members) - 1:
                            await scrim.assign(message.server.get_member(user["userid"]), "2")
                            continue
                        elif spaggheti_counter == 1:
                            await scrim.assign(message.server.get_member(user["userid"]), "1")
                        elif spaggheti_counter == 2:
                            await scrim.assign(message.server.get_member(user["userid"]), "1")
                        elif spaggheti_counter == 3:
                            await scrim.assign(message.server.get_member(user["userid"]), "2")
                        else:
                            await scrim.assign(message.server.get_member(user["userid"]), "2")
                        spaggheti_counter += 1
                        print("Count = {}".format(counter))
                        counter += 1
                    await client.send_message(message.channel, "Autobalancing completed. Please remember to assign unplaced members manually")
                if command_list[0] == "forceactive":
                    await ow_db.scrim.update_many({"rank": {"$exists": True}}, {"$set": {"active": True}}, )
        except IndexError:
            await client.send_message(message.channel, "Syntax error")
    pass


async def scrim_new(member):
    await client.send_message(member, "What is your battletag?")

    def check(msg):
        if regex_test(reg_str=r"^\D.{2,12}#\d{4,6}$", string=msg.content):
            return True
        return False

    message = await client.wait_for_message(author=member, check=check, timeout=3 )
    btag = message.content
    confirmation = "Joining scrim as " + btag
    await client.send_message(member, confirmation)
    return


async def scrim_join(member):
    await scrim.add_user(member)
    user = await ow_db.scrim.find_one({"userid": member.id, "btag": {"$exists": True}})
    if user:
        confirmation = "Joining scrim as " + user["btag"] + "… PM me a battletag to override"
        await client.send_message(member, confirmation)
        await scrim.refresh(member)
    else:
        await scrim_new(member)

    return (user["btag"], user["rank"])


async def scrim_start(message):
    global scrim
    server = message.server
    mod_role = ROLENAME_ROLE_DICT["MODERATOR_ROLE"]
    mod_role = await get_role(client.get_server("236343416177295360"), "260186671641919490")
    super_manager_role = await get_role(client.get_server("236343416177295360"), "261331682546810880")

    vc_overwrite_everyone = discord.PermissionOverwrite(connect=False, speak=True)
    vc_overwrite_mod = discord.PermissionOverwrite(connect=True)
    vc_overwrite_super_manager = discord.PermissionOverwrite(connect=True)

    text_overwrite_everyone = discord.PermissionOverwrite(read_messages=False)
    text_overwrite_mod = discord.PermissionOverwrite(read_messages=True)
    super_manager_perms_text = discord.PermissionOverwrite(read_messages=True)

    vc_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=vc_overwrite_everyone)
    vc_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=vc_overwrite_mod)
    vc_permission_super_manager = discord.ChannelPermissions(target=super_manager_role,
                                                             overwrite=vc_overwrite_super_manager)

    text_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=text_overwrite_everyone)

    # text_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=text_overwrite_mod)
    #
    # admin_text = discord.ChannelPermissions(target=ROLENAME_ROLE_DICT["ADMINISTRATOR_ROLE"], overwrite=admin_perms_text)

    scrim1_vc = await client.create_channel(server, "[Scrim] Team 1", vc_permission_everyone, vc_permission_mod,
                                            vc_permission_super_manager,
                                            type=discord.ChannelType.voice)
    scrim2_vc = await client.create_channel(server, "[Scrim] Team 2", vc_permission_everyone, vc_permission_mod,
                                            vc_permission_super_manager,
                                            type=discord.ChannelType.voice)
    scrim1 = ScrimTeam("1", scrim1_vc)
    scrim2 = ScrimTeam("2", scrim2_vc)

    scrim_spectate = await client.create_channel(server, "[Scrim] Spectate", type=discord.ChannelType.voice)

    scrim_text = await client.create_channel(server, "Scrim", text_permission_everyone, type=discord.ChannelType.text)

    scrim = ScrimMaster(scr1=scrim1, scr2=scrim2, txt=scrim_text, spec=scrim_spectate)
    mod_list = await get_moderators(message.server)
    for mod in mod_list:
        await ow_db.scrim.update_one({"userid": mod.id}, {"$set": {"manager": 1}}, upsert=True)

    print(await scrim.get_managers())

    await client.move_channel(scrim.spectate, 1)
    await client.move_channel(scrim.team1.vc, 2)
    await client.move_channel(scrim.team2.vc, 3)

    pass

async def get_sr(tag):
    ow = OverwatchAPI("")
    tag = tag.replace("#", "-")
    eu_result = ow.get_profile(platform="pc", region="eu", battle_tag=tag)
    na_result = ow.get_profile(platform="pc", region="us", battle_tag=tag)
    print(eu_result)
    print(na_result)
    try:
        eu_rank = eu_result["data"]["competitive"]["rank"]
    except:
        eu_rank = "0"
    try:
        na_rank = na_result["data"]["competitive"]["rank"]
    except:
        na_rank = "0"

    if int(eu_rank) < 1000:
        eu_rank = "0" + eu_rank
    if int(na_rank) < 1000:
        na_rank = "0" + na_rank

    # if na_rank == 0 and eu_rank == 0:
    #     return "Unplaced"
    return max([eu_rank, na_rank])


async def get_auths(member):
    """

    :type member: discord.Member
    """
    author_info = await parse_member_info(member)
    role_whitelist = any(x in [constants.ROLENAME_ID_DICT["TRUSTED_ROLE"], constants.ROLENAME_ID_DICT["MVP_ROLE"]]
                         for x in author_info["role_ids"])
    mod_whitelist = member.server_permissions.manage_roles and not any(
        x in "138132942542077952" for x in author_info["role_ids"])
    auths = set()
    if member.id == constants.ZENITH_ID:
        auths |= {"zenith"}
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"mod"}
    if mod_whitelist:
        auths |= {"mod"}
        auths |= {"warn"}
        auths |= {"trusted"}
    if role_whitelist:
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"lfg"}
    if any(x in "138132942542077952" for x in author_info["role_ids"]):
        auths |= {"bot"}
    # unspaggheti
    warn_auths = await overwatch_db.auths.find_one({"type": "warn"})
    if warn_auths:
        try:
            auth_list = warn_auths["ids"]
            if member.id in auth_list:
                auths |= {"warn"}
        except (KeyError, TypeError):
            print("ids not found")
            pass
    return auths


async def get_moderators(server):
    users = []
    for role in server.roles:
        if role.permissions.manage_roles:
            members = await get_role_members(role)
            users.extend(members)
    return users

async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members

async def get_roles(message):
    message_list = []
    role_list = []
    role_list.append(["Name", "ID", "Position", "Color", "Hoisted", "Mentionable"])
    widths = None
    for role in message.server.role_hierarchy:
        old_list = role_list
        new_entry = [role.name, str(role.id), str(role.position), str(role.colour.to_tuple()), str(role.hoist),
                     str(role.mentionable)]
        role_list.append(new_entry)
        print(len(str(await pretty_column(role_list, True))))
        if len(str(await pretty_column(role_list, True))) >= 1000:
            message_list.append(old_list[:-1])
            role_list = [new_entry]
    message_list.append(role_list)
    # print(message_list)
    multi = await multi_column(message_list, True)
    # print(multi)
    for mess in multi:
        await pretty_send(message.channel, mess)


async def send(channel, text):


class ChannelPlex:
    def __init__(self, server):
        self.server = client.get_server(server)

    def __getattr__(self, item):
        channel = client.get_channel(CHANNELS[item])
        self.__setattr__(item, channel)
        return channel

class RolePlex:
    def __init__(self, server):