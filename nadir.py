import ast
import heapq
import logging
import math
import random
import re
import sqlite3
import sys
import traceback
from datetime import datetime
import time
from io import StringIO

import pymongo
from asteval import Interpreter

from pyshorteners import Shortener
import discord
import motor.motor_asyncio
from fuzzywuzzy import fuzz
from imgurpython import ImgurClient
import pymongo
from pymongo import ReturnDocument
from simplegist.simplegist import Simplegist
import wolframalpha
import constants
from utils_file import delete_lines
from utils_parse import *
import urllib.request

ENABLED = True
logging.basicConfig(level=logging.INFO)

client = discord.Client()

imgur = ImgurClient("5e1b2fcfcf0f36e", "d919f14c31fa97819b1e9c82e2be40aef8bd9682", constants.ACCESS_TOKEN,
                    constants.REFRESH_TOKEN)
WA_ID = "W7TP9T-A9QJ2QGLJQ"
WA_client = wolframalpha.Client(WA_ID)
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
overwatch_db = mongo_client.overwatch
message_log_collection = overwatch_db.message_log
userinfo_collection = overwatch_db.userinfo

auths_collection = overwatch_db.auths
trigger_str_collection = overwatch_db.trigger_str

aeval = Interpreter()

id_channel_dict = {}

STREAM = None
gistClient = Simplegist()
# with open("paths.txt", "r") as f:
#     # global PATHS
#     pathList = f.read()
#     # noinspection PyRedeclaration
#     PATHS = ast.literal_eval(pathList)

BOT_HAPPENINGS_ID = "245415914600661003"

# noinspection PyPep8

ROLENAME_ROLE_DICT = {}
# noinspection PyPep8

# noinspection PyTypeChecker
ID_ROLENAME_DICT = dict([[v, k] for k, v in constants.ROLENAME_ID_DICT.items()])

BLACKLISTED_CHANNELS = (
    constants.CHANNELNAME_CHANNELID_DICT["bot-log"], constants.CHANNELNAME_CHANNELID_DICT["server-log"],
    constants.CHANNELNAME_CHANNELID_DICT["voice-channel-output"])

VCInvite = None
VCMess = None
INITIALIZED = False


async def get_redirected_url(url):
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    request = opener.open(url)
    return request.url


# noinspection PyPep8


async def get_mentions(mess, auth):
    target = mess.author

    await client.send_message(target, "Automated Mention Log Fetcher Starting Up!")
    await client.send_message(target, "Please respond with the number in the parentheses (X)")
    if auth == "mod":
        await client.send_message(target,
                                  "Would you like to query personal mentions (1), admin/mod mentions (2), or both (3)?")

        response_mess = await get_response_int(target)
        if response_mess is not None:
            await get_logs_mentions(response_mess.content, mess)
        else:
            await client.send_message(target, "You have taken too long to respond! Please restart.")
    else:
        await get_logs_mentions("1", mess)


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


async def get_response(message):
    def check(msg):
        if message.server == msg.server and msg.author.id == message.author.id and message.channel == msg.channel:
            return True
        return False

    return await client.wait_for_message(timeout=30, check=check)


async def initialize():
    global INITIALIZED
    global STREAM

    for role in client.get_server(constants.OVERWATCH_SERVER_ID).roles:
        if role.id in ID_ROLENAME_DICT.keys():
            ROLENAME_ROLE_DICT[ID_ROLENAME_DICT[role.id]] = role
    channel_dict = {}
    for channel in client.get_server(constants.OVERWATCH_SERVER_ID).channels:
        if channel.type == discord.ChannelType.text:
            channel_dict[await ascii_string(channel.name)] = channel.id
    STREAM = client.get_channel("255970182881738762")

    INITIALIZED = True


@client.event
async def on_member_remove(member):
    await add_to_user_set(member=member, set_name="server_leaves", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_member_ban(member):
    await add_to_user_set(member=member, set_name="bans", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_member_unban(member):
    await add_to_user_set(member=member, set_name="unbans", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


@client.event
async def on_member_join(member):
    # await add_to_nick_id_list(member)
    await add_to_user_list(member)
    return


# noinspection PyUnusedLocal
@client.event
async def on_voice_state_update(before, after):
    """
    :type after: discord.Member
    :type before: discord.Member
    """
    global VCInvite
    global VCMess
    if VCInvite is not None and VCMess is not None:
        if after is VCMess.author:
            await client.delete_messages([VCInvite, VCMess])
            VCInvite = None
            VCMess = None


# noinspection PyShadowingNames
@client.event
async def on_member_update(before, after):
    """

    :type after: discord.Member
    :type before: discord.Member
    """
    if before.nick is not after.nick:
        # await add_to_nick_id_list(after)
        if after.nick is not None:
            await add_to_user_list(after)


async def ascii_string(toascii):
    """
    :type toascii: str
    """

    return toascii.encode('ascii', 'ignore').decode("utf-8")


async def get_role(mess, userid):
    for x in mess.server.roles:
        if x.id == userid:
            return x


async def authorize_user(command_list):
    print(command_list)
    user_id = command_list[0]
    auth_type = command_list[1]

    # if auth_type == "get_art":
    #     utils_persist.set("art_auths", user_id)
    #     # with open(PATHS["comms"] + "art_credentials.txt", "a") as cred_list:
    #     #     cred_list.write(str(user_id) + "\n")
    # if auth_type == "hots":
    #     utils_persist.set("hots_auths", user_id)
    #     # with open(PATHS["comms"] + "hots_credentials.txt", "a") as cred_list:
    #     #     cred_list.write(str(user_id) + "\n")
    # if auth_type == "lfg":
    #     utils_persist.set("lfg_auths", user_id)
    #     # with open(PATHS["comms"] + "lfg_credentials.txt", "a") as cred_list:
    #     #     cred_list.write(str(user_id) + "\n")


# async def credential(member, level):
#     """
#
#     :type level: str
#     :type member: discord.Member
#     """
#
#     author_info = await parse_member_info(member)
#     role_whitelist = any(x in [constants.ROLENAME_ID_DICT["TRUSTED_ROLE"], constants.ROLENAME_ID_DICT["MVP_ROLE"]]
#                          for x in author_info["role_ids"])
#     mod_whitelist = member.server_permissions.manage_roles  and not any(x in "138132942542077952" for x in author_info["role_ids"])
#     zenith = member.id == constants.ZENITH_ID
#     # print("auth: " + level)
#     if level == "mod":
#         return mod_whitelist or zenith
#     elif level == "zenith":
#         return zenith
#     elif level == "trusted":
#         return mod_whitelist or role_whitelist or zenith
#     elif level == "lfg":
#         with open(PATHS["comms"] + "lfg_credentials.txt", "r") as cred_list:
#             creds = cred_list.readlines()
#             return (author_info["id"] + "\n") in creds or role_whitelist or mod_whitelist
#     elif level == "hots":
#         with open(PATHS["comms"] + "hots_credentials.txt", "r") as cred_list:
#             creds = cred_list.readlines()
#             return (author_info["id"] + "\n") in creds or role_whitelist or mod_whitelist
#     elif level == "get_art":
#
#         with open(PATHS["comms"] + "art_credentials.txt", "r") as cred_list:
#             creds = cred_list.readlines()
#
#             return (author_info["id"] + "\n") in creds or role_whitelist or mod_whitelist


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


async def clear_nicknames():
    await userinfo_collection.update_many({}, {"$unset": {"nicks": ""}})


async def remind_me(command_list, message):
    try:
        time = int(aeval(command_list[1]))
        await asyncio.sleep(time)
        await client.send_message(message.channel, "Reminding " + message.author.mention + " after " + str(
            time) + " seconds:\n" + command_list[0])
    except:
        print(traceback.format_exc())


async def wolfram(message):
    command = message.content.replace("`wa ", "")
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
    for num in range(0, numpods - 1):
        pod = podlist[num]
        options += "[" + str(num) + "] " + pod["@title"] + "\n"
        print("NUM = " + str(pod["@numsubpods"]))
        for sub_num in range(0,int(pod["@numsubpods"])):
            subpod = pod["subpod"]
            if subpod["@title"] != "":
                options += "    [" + str(num) + "." + str(sub_num) + "] " + subpod["@title"] + "\n"
        keydict[num] = pod
    await client.send_message(message.channel, options)
    response = await get_response(message)
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
            img = await shorten_link(img)
            text += img + "\n"
        await client.send_message(message.channel, text)

    except:
        print(traceback.format_exc())

    pass


@client.event
async def on_message(message):
    global VCMess
    global VCInvite
    global PATHS
    global ENABLED
    if not ENABLED:
        return
    if message.author.id == client.user.id:
        return

    if message.server is None:
        await client.send_message(await client.get_user_info(constants.ZENITH_ID),
                                  "[" + message.author.name + "]: " + message.content)
        return
    if message.channel.id in BLACKLISTED_CHANNELS:
        return
    if not INITIALIZED and message.server.id == constants.OVERWATCH_SERVER_ID:
        await initialize()
    else:
        # print("message received")
        # if message.content.startswith("`help"):
        #     command = message.content.replace("`help ", "")
        #     command_list = command.split(" ")
        #     await command_info(*[message, command_list])
        if message.channel.id not in BLACKLISTED_CHANNELS and message.server.id == constants.OVERWATCH_SERVER_ID:
            await mongo_add_message_to_log(message)

        auths = await get_auths(message.author)
        if "bot" in auths:
            return
        if "zenith" in auths or message.author.id == "203455531162009600":
            if message.content.startswith("`wa"):
                await wolfram(message)
        if "zenith" in auths:

            if message.content.startswith("`wipemessages"):
                await message_log_collection.delete_many({})
                await message_log_collection.create_index(("message_id", pymongo.DESCENDING), unique=True)
            if message.content.startswith("`superlog"):
                server = message.server
                await client.delete_message(message)
                for channel in server.channels:
                    try:
                        count = 0
                        async for retrieved_message in client.logs_from(channel, limit=1000000000000):
                            if count % 100 == 0:
                                print("Message got " + str(count))
                            try:
                                await mongo_add_message_to_log(retrieved_message)
                            except pymongo.errors.DuplicateKeyError:
                                print("duplicate")
                            count += 1
                    except:
                        print(traceback.format_exc())
            # Clear Mongo Nick List
            if message.content.startswith("`clearnicks"):
                await clear_nicknames()
            elif message.content.startswith("`remindme"):
                command = message.content.replace("`remindme ", "")
                command_list = command.split(" | ", 1)
                remind_me(command_list, message)
            # XKCD now
            elif message.content.startswith("`timenow"):
                redirected = await get_redirected_url("http://imgs.xkcd.com/comics/now.png")
                await client.send_message(message.channel, redirected)
                await client.delete_message(message)
            # Coroutine exec
            elif message.content.startswith("`exec_c"):
                input_command = message.content.replace("`exec_c ", "")
                command = ('try:\n'
                           '    import asyncio\n'
                           '    def do_task(message):\n'
                           '        asyncio.get_event_loop().create_task({command})\n'
                           '\n'
                           '    asyncio.get_event_loop().call_soon_threadsafe(do_task, message, client)\n'
                           'except RuntimeError:\n'
                           '    pass\n').format(command=input_command)
                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                response_str = None
                try:
                    exec(command)
                except Exception:
                    response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
                    response_str += traceback.format_exc()
                    response_str += "\n```"
                # finally:
                #     sys.stdout = old_stdout
                # if redirected_output.getvalue():
                #     response_str += redirected_output.getvalue()

                if response_str:
                    await client.send_message(message.channel, response_str)
            elif message.content.startswith("`exec_a"):
                input_command = message.content.replace("`exec_a ", "")
                command = ('try:\n'
                           '    import asyncio\n'
                           '    def do_task(message):\n'
                           '        {command}'
                           '\n'
                           '    asyncio.get_event_loop().call_soon_threadsafe(do_task, message)\n'
                           'except RuntimeError:\n'
                           '    pass\n').format(command=input_command)
                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                response_str = None
                try:
                    exec(command)
                except Exception:
                    response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
                    response_str += traceback.format_exc()
                    response_str += "\n```"
                # finally:
                #     sys.stdout = old_stdout
                # if redirected_output.getvalue():
                #     response_str += redirected_output.getvalue()

                if response_str:
                    await client.send_message(message.channel, response_str)
            elif message.content.startswith("`exec_n"):
                input_command = message.content.replace("`exec_n ", "")

                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                response_str = None
                try:
                    eval = aeval(input_command)
                    response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
                    # response_str += traceback.format_exc()

                finally:
                    sys.stdout = old_stdout
                if redirected_output.getvalue():
                    response_str += redirected_output.getvalue()
                    response_str += eval
                response_str += "\n```"
                if response_str:
                    await client.send_message(message.channel, response_str)
            # Wipe all gists
            elif message.content.startswith("`wipegists"):
                gist = gistClient.profile().list(30)
                for x in gist:
                    gistClient.profile().delete(id=x)
            # Have the bot say a command
            elif message.content.startswith("`say"):
                command = message.content.replace("`say ", "")
                command_list = command.split(" | ")
                await client.delete_message(message)
                if len(command_list) == 1:
                    await client.send_message(message.channel, command_list[0])
                else:
                    await client.send_message(message.channel_mentions[0], command_list[1])
            # Give a user perms
            elif "`auth" in message.content:
                command = message.content.replace("`auth ", "")
                command_list = command.split(" ")
                await client.delete_message(message)
                try:
                    await authorize_user(command_list)
                except:
                    print(traceback.format_exc())
            # NADIR PURGE
            elif "`clear" in message.content and message.server.id == "236343416177295360":
                await client.purge_from(message.channel)
            # Re-add all users to nickname database
            elif "`rebuildnicks" in message.content:
                memberlist = []
                for member in message.server.members:
                    memberlist.append(member)
                for member in memberlist:
                    try:
                        print(member.name)
                        await add_to_user_list(member)
                    except:
                        pass
            if message.content.startswith("`fixnicks"):
                cursor = userinfo_collection.find(
                    {"nicks": {"$exists": "false"}})
                id_list = {}
                async for nickless_user_info in cursor:
                    # print(nickless_user_info)
                    id_list[str(nickless_user_info["_id"])] = nickless_user_info["names"]
                    name = nickless_user_info["names"]
                    print(ascii(str(name)) + "    " + ascii(str(nickless_user_info["_id"])))
                print(ascii(id_list))
                print("\n\n\n\n\n")
                for x in id_list.keys():
                    try:
                        print(x + " is x")
                        result = await userinfo_collection.update_one(
                            {"_id": x},
                            {"$addToSet": {"nicks": {"$each": id_list[x]}}}, upsert=True
                        )
                        print(result.raw_result)
                    except:
                        print(traceback.format_exc())
            # Purge messages
            elif message.content.startswith("`purge"):
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
                                          "PURGING:\n" + str(await parse_message_info(message)))

                command = message.content.replace("`purge ", "")
                command_list = command.split(" ")
                number_to_remove = int(command_list[1])
                await client.delete_message(message)
                async for message in client.logs_from(message.channel):
                    print(number_to_remove)
                    print(command_list[0] + " " + command_list[1])
                    if message.author.id == command_list[0] and number_to_remove > 0:
                        await client.delete_message(message)
                        number_to_remove -= 1
                    else:
                        return
        # if (message.author.id == "180041371544059905" or message.author.id == constants.ZENITH_ID) and message.content == "`start9":
        #     stop = time.time() + 10
        #     while time.time() < stop:
        #         msg = await client.wait_for_message(channel= message.channel, timeout=.1)
        #         if msg:
        #             await client.delete_message(msg)
        if "mod" in auths:
            # if message.content.startswith("`fixperms"):
            #     await initialize()
            #     black_voice_perms = discord.PermissionOverwrite()
            #     black_voice_perms.connect = False
            #     black_voice_perms.speak = False
            #     black_voice_perms.mute_members = False
            #     black_voice_perms.deafen_members = False
            #     black_voice_perms.move_members = False
            #     black_voice_perms.use_voice_activation = False
            #
            #     for channel in message.server.channels:
            #         if channel.type == discord.ChannelType.voice:
            #             await client.edit_channel_permissions(channel, ROLENAME_ROLE_DICT["MUTED_ROLE"],
            #                                                   overwrite=black_voice_perms)
            #             print("running")
            if message.content.startswith("`fixmsg"):
                await overwatch_db.message_log2.create_index([("message_id", pymongo.DESCENDING)], unique=True)
                cursor = overwatch_db.message_log.find()
                async for x in cursor:
                    try:
                        await overwatch_db.message_log2.insert_one(x)
                        print("added_one")
                    except:
                        print("duplicate")
                        pass
                # await overwatch_db.drop_collection("message_log")
                print("inserted new")
                await overwatch_db.message_log2.rename("message_log", dropTarget="message_log")
                await mongo_client.fsync()
                print("done")

            if message.content.startswith("`moveafk"):
                command = message.content.replace("`moveafk ", "")
                command_list = await mention_to_id([command])
                target = message.server.get_member(command_list[0])
                afk = message.server.get_channel("94939166399270912")
                # print(afk.name)
                await client.move_member(target, afk)
            # Generate Join Link
            if "`join" == message.content[0:5]:
                command = message.content.replace("`join ", "")
                command_list = command.split(" ")
                VCMess = message
                instainvite = await get_vc_link(message)
                if instainvite:
                    VCInvite = await client.send_message(message.channel, instainvite)
                else:
                    await client.send_message(message.channel, "User not in a visible voice channel")
            # Fuzzy Nick Find
            if "`find" == message.content[0:5]:
                command = message.content[6:]
                command = command.lower()
                command = command.split("|", 2)
                await fuzzy_match(message, *command)
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
                                          "Fuzzysearch called by " + message.author.name + " on " + message.author.name)

            # Get previous nicknames
            if message.content.startswith("`getnicks"):
                command = message.content.strip("`getnicks ")
                nicklist = await get_previous_nicks(message.server.get_member(command))
                await client.send_message(message.channel, str(nicklist)[1:-1])
                pass
                # Reboot
            if "`reboot" == message.content and message.author.id == constants.ZENITH_ID:
                await client.send_message(message.channel, "Rebooting, " + message.author.mention)
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "Shut down by " + message.author.name)
                await client.logout()
            # Kill bot
            # if "`kill" == message.content:
            #     with open(PATHS["comms"] + "bootstate.txt", "w") as f:
            #         f.write("killed")
            #     await client.logout()
            # Get user logs
            if message.content.startswith("`userlogs"):
                command = message.content.replace("`userlogs ", "")
                command_list = command.split(" ")
                command_list = await mention_to_id(command_list)
                member = await client.get_user_info(command_list[0])
                logs = await get_user_logs(member, int(command_list[1]))
                gist = gistClient.create(name="User Log", description=member.name + "'s Logs", public=False,
                                         content="\n".join(logs))
                await client.send_message(message.channel, gist["Gist-Link"])
                await log_action_to_nadir(message=message, action_type="userlogs", target=member)
                # await client.edit_message(contextMess, gist["Gist-Link"])

            if message.content.startswith("`tag"):
                # command = message.content.replace("`blacklist ","")
                await tag_str(message)
        if "trusted" in auths:
            # User info
            if message.content.startswith("`ui"):
                try:
                    command_list = message.content.split(" ", 1)[1:]
                    command_list = await mention_to_id(command_list)
                    userid = command_list[0]
                except IndexError:
                    userid = message.author.id
                user_dict = await get_user_info(userid)
                if user_dict is not None:
                    formatted = [list(map(str, x)) for x in user_dict.items()]
                    text = await pretty_column(formatted, True)
                    # split = text.replace("\n", "|")
                    # split = split.replace(" ", "+")
                    # google_chart = "http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|12|h|FFFFFF|_|" + split
                    # await client.send_message(message.channel,google_chart)
                    text = re.sub(r'\s+$', '', text, 0, re.M)
                    await client.send_message(message.channel, "```\nFound:\n" + text.strip() + "```")
                    # for x in split:
                    # await client.send_message(message.channel,"`" + x + "`")
                    # await asyncio.sleep(20)
                    # await client.delete_message(ui_mess)
                else:
                    await client.send_message(message.channel, "User not found")
                return
            # Mention retrieval
            if "`getmentions" == message.content:
                if "mod" in auths:
                    await get_mentions(message, "mod")
                else:
                    await get_mentions(message, "trusted")
                return
            if message.content == "`ping":
                print("tester")
                await ping(message)
        if "warn" in auths:
            if message.content.startswith("`lfg"):
                found_message = None
                warn_user = None
                author = None
                if len(message.mentions) == 0:
                    found_message = await finder(message=message, regex=constants.LFG_REGEX, blacklist="mod")
                else:
                    warn_user = message.mentions[0]
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
                                          "`lfg called by " + message.author.name)
                await lfg_warner(found_message=found_message, warn_type="targeted", warn_user=warn_user,
                                 channel=message.channel)
                await client.delete_message(message)
        if "warn" in auths:
            if message.content.startswith("`hots"):
                hots_message = "Please keep Heroes of the Storm party-ups to <#247769594155106304>"
                author = await find_author(message=message, regex=constants.HOTS_REGEX, blacklist="mod")
                if author is not None:
                    hots_message += ", " + author.mention
                await client.send_message(message.channel, hots_message)
                await log_action_to_nadir(message=message, action_type="hots", target=author)
                await client.delete_message(message)
        # if "art" in auths:
        #     if message.content == "`getart" and False:
        #         await client.delete_message(message)
        #         art_channel = client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["fanart"])
        #         rand_art = []
        #         count = 8
        #         with open(PATHS["comms"] + "auto_art_list.txt", "r+") as art_list:
        #             if len(art_list.readlines()) <= count:
        #                 link_list = [x.link for x in imgur.get_album_images("umuvY")]
        #                 random.shuffle(link_list)
        #                 for link in link_list:
        #                     art_list.write(link + "\n")
        #         with open(PATHS["comms"] + "auto_art_list.txt", "r") as art_list:
        #             for x in range(1, count):
        #                 line = art_list.readline()
        #                 rand_art.append(line)
        #         await delete_lines(PATHS["comms"] + "auto_art_list.txt", count)
        #         for artlink in rand_art:
        #             await client.send_message(art_channel, artlink)
        #     if message.content.startswith("`flagart"):
        #         command = message.content.replace("`flagart ", "")
        #         imgur_id_reg = re.compile("(?<=http://i.imgur.com/)(\w+)", re.IGNORECASE)
        #         match = imgur_id_reg.search(command)
        #         if "zenith" in auths:
        #             if match is not None:
        #                 imgur_id = match.group(0)
        #                 imgur.delete_image(imgur_id)
        #                 log_action_to_nadir(message, "flagart", target=imgur_id)
        #         found_message = await finder(message, command, "none")
        #         if message is not None:
        #             await client.delete_message(found_message)

        if "mod" not in auths:
            # EXTRA-SERVER INVITE CHECKER
            if "chaos vanguard" in message.content.lower():
                await log_automated("logged a message containing Chaos Vanguard in " + message.channel.name + ":\n[" +
                                    message.author.name + "]: " + message.content)
                # await client.delete_message(message)
                skycoder_mess = await client.send_message(
                    client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["spam-channel"]),
                    "~an " + message.author.mention +
                    " AUTOMATED: Posted a message containing chaos vanguard: " + message.content)
            if message.channel.id not in BLACKLISTED_CHANNELS:
                match = constants.LINK_REGEX.search(message.content)
                if match is not None:
                    await invite_checker(message, match)
                    # LFG -> Audit
                    # if message.channel.id == constants.CHANNELNAME_CHANNELID_DICT["general-discussion"]:
                    #     match = constants.LINK_REGEX.search(message.content)
                    #     if match is not None:
                    #         await client.send_message(client.get_channel(constants.NADIR_AUDIT_LOG_ID), message.content)
                    #         await invite_checker(message, match)


async def find_author(message, regex, blacklist):
    author = None
    if len(message.mentions) > 0:
        author = message.mentions[0]
    else:
        found_mess = await finder(message, regex, blacklist)
        if found_mess is not None:
            author = found_mess.author
    return author


#
# @client.event
# async def on_message(mess):
#     """
#     Called on client message reception
#     :type mess: discord.Message
#     """
#     global VCMess
#     global VCInvite
#     global PATHS
#     global ENABLED
#     if not ENABLED:
#         return
#     # Not a PM
#     if mess.server is None:
#         await client.send_message(client.get_user(constants.ZENITH_ID), "[" + mess.author.name + "]: " + mess.content)
#     if mess.server is not None:
#         if not INITIALIZED and mess.server.id == constants.OVERWATCH_SERVER_ID:
#             await initialize()
#
#         if mess.channel.id not in BLACKLISTED_CHANNELS:
#             await mongo_add_message_to_log(mess)
#
#         if mess.content == "`getart":
#             if await credential(mess.author, "get_art"):
#                 await client.delete_message(mess)
#                 art_channel = client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["fanart"])
#                 rand_art = []
#                 count = 8
#                 with open(PATHS["comms"] + "auto_art_list.txt", "r+") as art_list:
#                     if len(art_list.readlines()) <= count:
#                         link_list = [x.link for x in imgur.get_album_images("umuvY")]
#                         random.shuffle(link_list)
#                         for link in link_list:
#                             art_list.write(link + "\n")
#                 with open(PATHS["comms"] + "auto_art_list.txt", "r") as art_list:
#                     for x in range(1, count):
#                         line = art_list.readline()
#                         rand_art.append(line)
#                 await delete_lines(PATHS["comms"] + "auto_art_list.txt", count)
#
#                 for artlink in rand_art:
#                     await client.send_message(art_channel, artlink)
#         if mess.content.startswith("`flagart"):
#             command = mess.content.replace("`flagart ", "")
#             imgur_id_reg = re.compile("(?<=http://i.imgur.com/)(\w+)", re.IGNORECASE)
#             match = imgur_id_reg.search(command)
#             if await credential(mess.author, "zenith"):
#                 if match is not None:
#                     imgur_id = match.group(0)
#                     imgur.delete_image(imgur_id)
#
#             message = await finder(mess, command, "none")
#             print(message.content)
#             if message is not None:
#                 await client.delete_message(message)
#         # AUTHOR-ONLY
#         if await credential(mess.author, "zenith"):
#             if mess.content.startswith("`clearnicks"):
#                 result = await userinfo_collection.update_many(
#                     {},
#                     {"$unset": {"nicks": ""}}
#                 )
#                 return
#             if mess.content.startswith("`remindme"):
#                 command = mess.content.replace("`remindme ", "")
#                 command_list = command.split(" | ", 1)
#                 print(command_list)
#                 try:
#                     time = int(aeval(command_list[1]))
#                     # time = int(command[0])
#                     await asyncio.sleep(time)
#                     await client.send_message(mess.channel, "Reminding " + mess.author.mention + " after " + str(
#                         time) + " seconds:\n" + command_list[0])
#                 except:
#                     print(traceback.format_exc())
#
#             if mess.content.startswith("`timenow"):
#                 redirected = await get_redirected_url("http://imgs.xkcd.com/comics/now.png")
#                 await client.send_message(mess.channel, redirected)
#                 await client.delete_message(mess)
#             if mess.content.startswith("`aex"):
#                 print("EXECUTING")
#                 input_command = mess.content.replace("`aex ", "")
#                 command = ('try:\n'
#                            '    import asyncio\n'
#                            '    def do_task(message):\n'
#                            '        asyncio.get_event_loop().create_task({command})\n'
#                            '\n'
#                            '    asyncio.get_event_loop().call_soon_threadsafe(do_task, mess)\n'
#                            'except RuntimeError:\n'
#                            '    pass\n').format(command=input_command)
#
#                 old_stdout = sys.stdout
#                 redirected_output = sys.stdout = StringIO()
#                 response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
#                 try:
#                     exec(command)
#                 except Exception:
#                     response_str += traceback.format_exc()
#                 finally:
#                     sys.stdout = old_stdout
#                 if redirected_output.getvalue():
#                     response_str += redirected_output.getvalue()
#                 response_str += "\n```"
#                 await client.send_message(mess.channel, response_str)
#             if mess.content.startswith("`wipegists"):
#                 gist = gistClient.profile().list(30)
#                 for x in gist:
#                     gistClient.profile().delete(id=x)
#
#             if mess.content.startswith("`say"):
#                 command = mess.content.replace("`say ", "")
#                 command_list = command.split(" | ")
#                 channel = mess.channel
#                 channel_mentions = mess.channel_mentions
#                 await client.delete_message(mess)
#                 if len(command_list) == 1:
#                     await client.send_message(channel, command_list[0])
#                 else:
#                     await client.send_message(channel_mentions[0], command_list[1])
#             if "`auth" in mess.content:
#                 command = mess.content.replace("`auth ", "")
#                 command_list = command.split(" ")
#                 await client.delete_message(mess)
#                 try:
#                     await authorize_user(command_list)
#                 except:
#                     print(traceback.format_exc())
#             # NADIR PURGE
#             if "`clear" in mess.content and mess.server.id == "236343416177295360":
#                 await client.purge_from(mess.channel)
#             if "`rebuildnicks" in mess.content:
#                 memberlist = []
#                 for member in mess.server.members:
#                     memberlist.append(member)
#                 for member in memberlist:
#                     try:
#                         print(member.name)
#                         await add_to_user_list(member)
#                     except:
#                         pass
#             if mess.content.startswith("`purge"):
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
#                                           "PURGING:\n" + str(await parse_message_info(mess)))
#
#                 command = mess.content.replace("`purge ", "")
#                 command_list = command.split(" ")
#                 number_to_remove = int(command_list[1])
#                 await client.delete_message(mess)
#                 async for message in client.logs_from(mess.channel):
#                     print(number_to_remove)
#                     print(command_list[0] + " " + command_list[1])
#                     if message.author.id == command_list[0] and number_to_remove > 0:
#                         await client.delete_message(message)
#                         number_to_remove -= 1
#                     else:
#                         return
#         # BLACK-LIST MODS
#         if mess.author.id != constants.MERCY_ID and not await credential(mess.author, "trusted"):
#             # EXTRA-SERVER INVITE CHECKER
#             if mess.channel.id not in BLACKLISTED_CHANNELS:
#                 match = constants.LINK_REGEX.search(mess.content)
#                 if match is not None:
#                     await invite_checker(mess, match)
#             # LFG -> Audit
#             if mess.channel.id == constants.CHANNELNAME_CHANNELID_DICT["general-discussion"]:
#                 match = constants.LFG_REGEX.search(mess.content)
#                 if match is not None:
#                     await client.send_message(client.get_channel(constants.NADIR_AUDIT_LOG_ID), mess.content)
#                     # match = linkReg.search(mess.content)
#                     # if match is not None:
#                     #     print("FOUND ONE")
#                     #     await invite_checker(mess, match)
#
#         if mess.content.startswith("`hots") and mess.author.id != constants.MERCY_ID and await credential(mess.author,
#                                                                                                           "hots"):
#             hots_message = "Please keep Heroes of the Storm party-ups to <#247769594155106304>"
#             author = None
#             if len(mess.mentions) > 0:
#                 author = mess.mentions[0]
#             else:
#                 HOTS_REGEX = re.compile(r"(heroes of the storm)|(storm)|(heros)|(hots)|(heroes)|(genji)|(oni)",
#                                         re.IGNORECASE)
#                 found_mess = await finder(mess, HOTS_REGEX, "mod")
#                 if found_mess is not None:
#                     author = found_mess.author
#             if author is not None:
#                 hots_message += ", " + author.mention
#             hots_warn = await client.send_message(mess.channel, hots_message)
#             await client.delete_message(mess)
#             # await asyncio.sleep(10)
#             # await client.delete_message(hots_warn)
#         # WHITE-LIST TRUSTED
#
#         if mess.author.id != constants.MERCY_ID and await credential(mess.author, "trusted"):
#
#             # Gets banned userinfo dict
#             if "`ui" in mess.content:
#                 try:
#                     command_list = mess.content.split(" ", 1)[1:]
#                     command_list = await mention_to_id(command_list)
#                     command = command_list[0]
#                 except IndexError:
#                     command = mess.author.id
#                 user_dict = await get_user_info(command)
#                 if user_dict is not None:
#                     formatted = [list(map(str, x)) for x in user_dict.items()]
#                     await client.send_message(mess.channel,
#                                               "```Found:\n" + await pretty_column(formatted, True) + "\n```")
#                 else:
#                     await client.send_message(mess.channel, "User not found")
#                 return
#
#             # Get Mentions
#             if "`getmentions" == mess.content:
#                 await get_mentions(mess)
#                 return
#                 # Call LFG autowarn
#         if mess.author.id != constants.MERCY_ID and await credential(mess.author, "lfg"):
#             if '`lfg' == mess.content[0:4]:
#                 found_mess = None
#                 author = None
#                 if len(mess.mentions) > 0:
#                     author = mess.mentions[0]
#                 else:
#                     found_mess = await finder(mess, constants.LFG_REGEX, "mod")
#                     if found_mess is not None:
#                         print("Found a message!")
#                         print(found_mess.content + " " + found_mess.author.name)
#                         author = found_mess.author
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "`lfg called by " + mess.author.name)
#
#                 await client.delete_message(mess)
#                 await lfg_warner(found_message=found_mess, warn_type="targeted", warn_user=author, channel=mess.channel)
#                 # Ping bot
#         if "`ping" == mess.content or mess.content == "<@!236341193842098177>":
#             await ping(mess)
#
#         if mess.author.id != constants.MERCY_ID and await credential(mess.author, "mod"):
#             # Generate Join Link
#             if "`join" == mess.content[0:5]:
#                 VCMess = mess
#                 instainvite = await get_vc_link(mess)
#                 VCInvite = await client.send_message(mess.channel, instainvite)
#             # Fuzzy Nick Find
#             if "`find" == mess.content[0:5]:
#                 command = mess.content[6:]
#                 command = command.lower()
#                 command = command.split("|", 2)
#                 await fuzzy_match(mess, *command)
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
#                                           "Fuzzysearch called by " + mess.author.name + " on " + mess.author.name)
#
#             # Get previous nicknames
#             if mess.content.startswith("`getnicks"):
#                 command = mess.content.strip("`getnicks ")
#                 nicklist = await get_previous_nicks(mess.server.get_member(command))
#                 await client.send_message(mess.channel, str(nicklist)[1:-1])
#                 pass
#             # Kill Bot
#             if "`reboot" == mess.content:
#                 await client.send_message(mess.channel, "Rebooting, " + mess.author.mention)
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "Shut down by " + mess.author.name)
#                 await client.logout()
#             if "`kill" == mess.content:
#                 with open(PATHS["comms"] + "bootstate.txt", "w") as f:
#                     f.write("killed")
#                 client.logout()
#             # Get user logs
#             if mess.content.startswith("`userlogs"):
#                 command = mess.content.replace("`userlogs ", "")
#                 command_list = command.split(" ")
#                 command_list = await mention_to_id(command_list)
#                 member = mess.server.get_member(command_list[0])
#                 logs = await get_user_logs(member, int(command_list[1]))
#                 gist = gistClient.create(name="User Log", description=member.name + "'s Logs", public=False,
#                                          content="\n".join(logs))
#                 await client.send_message(mess.channel, gist["Gist-Link"])
#                 await log_action_to_nadir(message=mess, action_type="userlogs", *(member))
#                 # await client.edit_message(contextMess, gist["Gist-Link"])


async def log_action_to_nadir(message, action_type, target):
    text = "a"
    if action_type == "userlogs" or action_type == "hots":
        text = "Userlogs called by " + message.author.name + " on " + target.name
    elif action_type == "reboot":
        text = "Rebooted by " + message.author.name
    elif action_type == "flagart":
        text = "Art flagged " + target
    await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), text)


# noinspection PyBroadException
async def invite_checker(message, regex_match):
    """

    :type regex_match: re.match
    :type message: discord.Message
    """
    try:
        print("matchgrp = " + str(regex_match.group(1)))
        invite = await client.get_invite(str(regex_match.group(1)))
        if invite.server.id != constants.OVERWATCH_SERVER_ID:
            channel = message.channel
            # await client.send_message(mess.channel, serverID + " " + OVERWATCH_ID)
            warn = await client.send_message(message.channel,
                                             "Please don't link other discord servers here " +
                                             message.author.mention + "\n" +
                                             message.server.get_member(constants.ZENITH_ID).mention)
            await client.delete_message(message)

            await log_automated("deleted an external invite: " + str(
                invite.url) + " from " + message.author.mention + " in " + message.channel.mention)
            skycoder_mess = await client.send_message(
                client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["spam-channel"]),
                "~an " + message.author.mention +
                " AUTOMATED: Posted a link to another server")
            await client.send_message(skycoder_mess.channel, "~rn " + message.author.mention)
        elif message.channel.id == constants.CHANNELNAME_CHANNELID_DICT["general-discussion"]:

            channel_name = invite.channel.name
            party_vc_reg = re.compile(r"(^\[)\w+.\w+\]", re.IGNORECASE)
            match = party_vc_reg.search(channel_name)
            if match is not None:
                print("channelname = " + message.channel.name)
                await lfg_warner(found_message=message, warn_type="automated", warn_user=message.author,
                                 channel=message.channel)
                await client.delete_message(message)
    except discord.errors.NotFound:
        pass
    except:
        print(traceback.format_exc())


# noinspection PyPep8Naming
async def get_vc_link(mess):
    """

    :type mess: discord.Message
    """
    command = mess.content.replace("`join", "")
    if command[0:1] == " ": command = command[1:]
    print(command)
    if len(command) == 0:
        userID = await get_from_find(mess)
        print("userid = " + userID)
    else:
        # print("command list = " + str(command_list))
        command_list = await mention_to_id([command])
        userID = command_list[0]
    print("TYPE = " + userID)
    mentionedUser = mess.server.get_member(userID)
    try:
        vc = mentionedUser.voice.voice_channel
        instaInvite = await client.create_invite(vc, max_uses=1, max_age=6)
        return instaInvite.url
    except AttributeError:
        return None


async def mention_to_id(command_list):
    """

    :type command: list
    """
    new_command = []
    reg = re.compile(r"<@(!?)\d*>", re.IGNORECASE)
    for item in command_list:
        match = reg.search(item)
        if match is None:
            print("no match found")
            new_command.append(item)
        else:
            idmatch = re.compile(r"\d")
            id_chars = "".join(idmatch.findall(item))
            print("id chars")
            print(id_chars)
            new_command.append(id_chars)
    print(new_command)
    return new_command


async def log_automated(description: object) -> None:
    action = ("At " + str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")) + ", I automatically " +
              str(description) + "\n" + "`kill to disable me")
    await client.send_message(client.get_channel(constants.CHANNELNAME_CHANNELID_DICT["alerts"]), action)
    # await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), action)


#
# async def command_info(*args):
#     info_list = []
#     if len(args) == 2:
#         info_list = [
#             ["Command ", "Description ", "Usage"],
#             ["<Trusted>,", " ", " "],
#             ["`ui", "Retrieves user info", "`ui *<user>"],
#             ["`getmentions", "Mention retrieval", "`getmentions"],
#             ["`lfg", "Automated lfg logger and copypasta warning", "`lfg *<user>"],
#             ["`ping", "Gets a random mercy voice-line and bot ping", "`ping"],
#             ["`userlogs", "Gets logs from a user", "`userlogs <user> <count>"],
#             [" ", " ", " "],
#
#         ]
#         if await credential(args[0].author, "mod"):
#             info_list.append(["<Moderator>", " ", " "])
#             info_list.append(["`kill", "Disconnects bot", "`kill"])
#             info_list.append(["`join", "Gets an invite for a user's current VC", "`join <user>"])
#             info_list.append(["`find", "Finds users that have had similar nicknames", "`find <nick>|<count>"])
#             info_list.append(["`getnicks", "Gets the previous nicknames of a user", "`getnicks <id>"])
#     await client.send_message(args[0].channel, "```prolog\n" + await pretty_column(info_list, True) + "```")


async def ping(message):
    # lag = (datetime.utcnow() - message).timestamp.total_seconds() * 1000) + " ms")
    """
    :type message: discord.Message
    """

    timestamp = message.timestamp
    channel = message.channel

    await client.delete_message(message)
    voice = random.choice(constants.VOICE_LINES)
    sent = await client.send_message(channel, voice)
    await client.edit_message(sent,
                              voice + " (" + str(
                                  (sent.timestamp - timestamp).total_seconds() * 500) + " ms) " +
                              message.author.mention)


async def fuzzy_match(*args):
    if len(args) == 2:
        count = 1
    else:
        count = args[2]
    nick_to_find = args[1]
    mess = args[0]

    # cursor = database.cursor()
    # cursor.execute('SELECT userid,nickname FROM useridlist')
    # nickIdList = cursor.fetchall()
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
                await add_to_user_list(
                    client.get_server(constants.OVERWATCH_SERVER_ID).get_member(userinfo_dict["userid"]))
            except:
                pass
    print("DONE")

    # for id, nick in nickIdList:
    #     nickIdDict.setdefault(nick, []).append(id)

    # noinspection PyUnusedLocal
    nick_fuzz = {}

    for nick in nick_id_dict.keys():
        ratio = fuzz.ratio(nick_to_find, str(nick))
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

    message_to_send += await pretty_column(pretty_list, True)
    await client.send_message(mess.channel, message_to_send)


async def pretty_column(list_of_rows, left_just):
    """
    :type list_of_rows: list
    :type left_just: bool
    """
    widths = [max(map(len, col)) for col in zip(*list_of_rows)]
    output = ""
    if left_just:
        for row in list_of_rows:
            output += ("  ".join((val.ljust(width) for val, width in zip(row, widths)))) + "\n"
    else:
        for row in list_of_rows:
            output += ("  ".join((val.rjust(width) for val, width in zip(row, widths)))) + "\n"
    # print(output)
    return output


async def get_from_find(message):
    reg = re.compile(r"(?!ID: ')(\d+)(?=')", re.IGNORECASE)
    user_id = ""
    async for mess in client.logs_from(message.channel, limit=10):
        if "Fuzzy Search:" in mess.content:
            match = reg.search(mess.content)
            if match is not None:
                user_id = match.group(0)
    return user_id


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


    # noinspection PyBroadException


# (found_message=found_message, warn_type="targeted", warn_user=warn_user
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
        count = await increment_lfgd_mongo(author)
        author_mention += ", " + author.mention + " (" + str(count) + ")"
    except:
        print(traceback.format_exc())

    if warn_type == "automated":
        print("AUTOMATED")
        # noinspection PyPep8
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])
        ordinal_count = ordinal(count)
        await log_automated(
            "warned " + author.mention + " in " + found_message.channel.mention + " for the " + ordinal_count + " time because of the message\n" +
            found_message.content)

    lfg_text += author_mention
    await client.send_message(channel, lfg_text)


async def get_user_logs(member, count):
    """

    :type count: int
    :type member: discord.Member
    """
    query_dict = {"userid": member.id}
    cursor = overwatch_db.message_log.find(query_dict, limit=count)
    cursor.sort("date", -1)
    message_list = []
    async for message_dict in cursor:
        message_list.append(await message_to_log(message_dict))
    return message_list


async def message_to_log(message_dict):
    cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
    try:
        name = cursor["names"][-1]
    except:
        try:
            add_to_user_list((client.get_server(message_dict["server_id"])).get_member(message_dict["userid"]))
            cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
            name = cursor["names"][-1]

        except:
            name = cursor["userid"]

            return


    content = message_dict["content"].replace("```", "")
    try:
        channel_name = constants.CHANNELID_CHANNELNAME_DICT[str(message_dict["channel_id"])]
    except KeyError:
        channel_name = "Unknown"
    return "[" + message_dict["date"][:19] + "][" + channel_name + "][" + name + "]:" + \
           content


async def get_logs_mentions_2(query_type, message):
    await log_action_to_nadir(message, "logs", message.author)
    author_info = await parse_member_info(message.server.get_member(message.author.id))
    target = message.author
    if query_type == "1":
        cursor = overwatch_db.message_log.find({"mentioned_users": author_info["id"]})
    elif query_type == "2":
        cursor = overwatch_db.message_log.find({"mentioned_roles": {"$in": author_info["role_ids"]}})
    else:  # query_type == "3":
        cursor = overwatch_db.message_log.find(
            {"$or": [{"mentioned_users": author_info["id"]}, {"mentioned_roles": {"$in": author_info["role_ids"]}}]})


async def tag_str(message):
    string = message.content
    interact = await client.send_message(message.channel, "Blacklisting string: \n `" + string + "`\n" +
                                         "What action should I take? (kick, delete, mute <duration>")
    action_response = (await client.wait_for_message(author=message.author, channel=message.channel)).content
    if action_response in ["kick", "delete", "mute"]:
        database_entry = {"trigger_str": string, "action": action_response}
    else:
        await client.edit_message(interact, "Syntax not recognized. Please restart")
        return
    result = await trigger_str_collection.insert_one(database_entry)


async def process_tags(message):
    tag_list = await trigger_str_collection.find(query={}, projection="trigger_str").to_list()
    action = None
    for tag in tag_list:
        if tag in message.content:
            tag_doc = trigger_str_collection.find_one({"trigger_str": tag})
            action = tag_doc["action"]
            break
    if action:
        pass


async def get_logs_mentions(query_type, mess):
    """
    :type query_type: Integer
    :type mess: discord.Message
    """
    try:
        await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(await parse_message_info(mess)))
    except:
        await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(traceback.format_exc()))
    mess_info = await parse_message_info(mess)
    target = mess.author
    author_info = await parse_member_info(mess.server.get_member(mess.author.id))
    cursor = None
    if query_type == "1":
        cursor = overwatch_db.message_log.find({"mentioned_users": author_info["id"]})
    elif query_type == "2":
        cursor = overwatch_db.message_log.find({"mentioned_roles": {"$in": author_info["role_ids"]}})
    else:  # query_type == "3":
        cursor = overwatch_db.message_log.find(
            {"$or": [{"mentioned_users": author_info["id"]}, {"mentioned_roles": {"$in": author_info["role_ids"]}}]})

    # await client.send_message(target, "DEBUG: Query Did Not Fail!")
    number_message_dict = {}
    count = 1
    cursor.sort("date", -1)
    message_choices_text = "```\n"
    await client.send_message(target, "Retrieving Messages! (0) to get more messages!")
    mention_choices_message = await client.send_message(target, "Please wait...")
    response = 0
    async for message_dict in cursor:
        # user_info = await parse_member_info(target.server.get_member(message_dict["userid"]))
        # await client.send_message(target, "DEBUG: FOUND MATCH! " + message_dict["content"])
        number_message_dict[count] = message_dict
        message_choices_text += "(" + str(count) + ")" + await message_to_log(message_dict) + "\n"
        if count % 5 == 0:
            message_choices_text += "\n```"
            try:
                await client.edit_message(mention_choices_message, message_choices_text)
            except discord.errors.HTTPException:
                message_choices_text
                await client.send_message(target, message_choices_text)
            response = await get_response_int(target)
            if response is None:
                await client.send_message(target, "You have taken too long to respond! Please restart.")
                return
            elif response.content == "0":
                count = 1
                message_choices_text = message_choices_text[:-4]
                continue
            else:
                break
        count += 1
    try:

        if response.content == "0":
            await client.send_message(target,
                                      "You have no (more) logged mentions!")
            response = await get_response_int(target)
        selected_message = number_message_dict[int(response.content)]
        await client.send_message(target, " \n Selected Message: \n[" + await message_to_log(selected_message))
        await client.send_message(target,
                                  "\n\n\n\nHow many messages of context would you like to retrieve? Enter an integer")
        response = await get_response_int(target)
        response = int(response.content)
        # print("Response = " + str(response))
        cursor = overwatch_db.message_log.find(
            {
                "date": {"$lt": selected_message["date"]},
                "channel_id": selected_message["channel_id"]
            }, limit=response
        )
        cursor.sort("date", -1)
        contextMess = await client.send_message(target, "Please wait...")
        contextContent = ""

        async for message_dict in cursor:
            try:
                # print("DEBUG: FOUND MATCH! " + message_dict["content"])
                user_info = await parse_member_info(
                    (client.get_server(message_dict["server_id"])).get_member(message_dict["userid"])
                )
                contextContent += "[" + message_dict["date"][:19] + "][" + user_info["name"] + "]: " + message_dict[
                    "content"] + "\n"
            except:
                pass

        gist = gistClient.create(name="M3R-CY Log", description=selected_message["date"], public=False,
                                 content=contextContent)
        await client.edit_message(contextMess, gist["Gist-Link"])


    except ValueError as e:
        await client.send_message(target, "You entered something wrong! Oops!")
        print(traceback.format_exc())
    except TypeError as e:
        await client.send_message(target, "You entered something wrong! Oops!")
        print(traceback.format_exc())
    pass


async def mongo_add_message_to_log(mess):
    messInfo = await parse_message_info(mess)
    result = await message_log_collection.insert_one(messInfo)
    messText = await message_to_log(messInfo)
    # await client.send_message(STREAM, messText[21:])


async def increment_lfgd_mongo(author):
    """

    :type author: discord.Member
    """
    result = await userinfo_collection.find_one_and_update(
        {"userid": author.id},
        {"$inc": {
            "lfg_count": 1
        }}, upsert=True, return_document=ReturnDocument.AFTER),
    return result[0]["lfg_count"]


async def add_to_user_set(member, set_name, entry):
    """

    :type entry: str
    :param set_name: str
    :type member: discord.Member
    """
    user_info = await parse_member_info(member)
    result = await userinfo_collection.update_one(
        {"userid": user_info["id"]},
        {
            "$addToSet": {set_name: entry}
        }
    )


async def add_to_user_list(member):
    """

    :type member: discord.Member
    """
    user_info = await parse_member_info(member)
    result = await userinfo_collection.update_one(
        {"userid": member.id},
        {
            "$addToSet": {"nicks": {"$each": [user_info["nick"], user_info["name"]]},
                          "names": user_info["name"],
                          "avatar_urls": user_info["avatar_url"],
                          "server_joins": user_info["joined_at"]},
            "$set": {"mention_str": user_info["mention_str"],
                     "created_at": user_info["created_at"]},

        }
        , upsert=True
    )
    print(result.raw_result)
    pass


async def get_previous_nicks(member) -> list:
    """
paste
    :type member: discord.Member
    """
    userinfo_dict = await userinfo_collection.find_one({"userid": member.id})
    return list(userinfo_dict["nicks"])


async def shorten_link(link) -> str:
    return Shortener('Tinyurl').short(link)


async def get_user_info(member_id):
    """

    :type member: discord.Member
    """
    mongo_cursor = await userinfo_collection.find_one(
        {"userid": member_id}, projection={"_id": False, "mention_str": False}
    )
    if not mongo_cursor:
        return None
    list = mongo_cursor["avatar_urls"]
    if len(list) > 0 and len(list[0]) > 0:
        shortened_list = []
        for link in list:
            shortened_list.append(await shorten_link(link))
        mongo_cursor["avatar_urls"] = shortened_list
    return mongo_cursor


# with open(PATHS["comms"] + "bootstate.txt", "r") as f:
#     line = f.readline().strip()
#     if line == "killed":
#         ENABLED = False
# client.loop.create_task(stream())

client.run("MjM2MzQxMTkzODQyMDk4MTc3.CvBk5w.gr9Uv5OnhXLL3I14jFmn0IcesUE", bot=True)
