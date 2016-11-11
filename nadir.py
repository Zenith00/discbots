import ast
import csv
import re
import sqlite3
import traceback
from datetime import timedelta, datetime
import random
import discord
import asyncio
from fuzzywuzzy import fuzz
import heapq
import motor.motor_asyncio
from pymongo import ReturnDocument
from simplegist.simplegist import Simplegist

mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
overwatch_db = mongo_client.overwatch
message_log_collection = overwatch_db.message_log
userinfo_collection = overwatch_db.userinfo

PATHS = {}

gistClient = Simplegist()

with open("paths.txt", "r") as f:
    # global PATHS
    pathList = f.read()
    # noinspection PyRedeclaration
    PATHS = ast.literal_eval(pathList)

OVERWATCH_SERVER_ID = "94882524378968064"
database = sqlite3.connect(PATHS["comms"] + "userIDlist.db")

messageBase = sqlite3.connect("E:\\Logs\\messages.db")

BOT_HAPPENINGS_ID = "245415914600661003"

MERCY_ID = "236341193842098177"
ZENITH_ID = "129706966460137472"

# noinspection PyPep8
CHANNELNAME_CHANNELID_DICT = {
    "overwatch-discussion"   : "109672661671505920",
    "modchat"                : "106091034852794368",
    "server-log"             : "152757147288076297",
    "voice-channel-output"   : "200185170249252865",
    "moderation-notes"       : "188949683589218304",
    "pc-lfg"                 : "182420486582435840",
    "esports-discussion"     : "233904315247362048",
    "content-creation"       : "95324409270636544",
    "support"                : "241964387609477120",
    "competitive-recruitment": "170983565146849280",
    "tournament-announcement": "184770081333444608",
    "trustedchat"            : "170185225526181890",
    "general-discussion"     : "94882524378968064",
    "lf-scrim"               : "177136656846028801",
    "console-lfg"            : "185665683009306625",
    "sombra-discussion"      : "244000157916463104",
    "fanart"                 : "168567769573490688",
    "competitive-discussion" : "107255001163788288",
    "lore-discussion"        : "180471683759472640",
    "announcements"          : "95632031966310400",
    "spam-channel"           : "209609220084072450",
    "jukebox"                : "176236425384034304",
    "rules-and-info"         : "174457179850539009",
    "warning-log"            : "170179130694828032",
    "bot-log"                : "147153976687591424"
}

ROLENAME_ROLE_DICT = {}
# noinspection PyPep8
ROLENAME_ID_DICT = {
    "REDDIT_MODERATOR_ROLE"    : "94887153133162496",
    "BLIZZARD_ROLE"            : "106536617967116288",
    "MUTED_ROLE"               : "110595961490792448",
    "MVP_ROLE"                 : "117291830810247170",
    "OMNIC_ROLE"               : "138132942542077952",
    "TRUSTED_ROLE"             : "169728613216813056",
    "ADMINISTRATOR_ROLE"       : "172949857164722176",
    "MODERATOR_ROLE"           : "172950000412655616",
    "DISCORD_STAFF_ROLE"       : "185217304533925888",
    "PSEUDO_ADMINISTRATOR_ROLE": "188858581276164096",
    "FOUNDER_ROLE"             : "197364237952221184",
    "REDDIT_OVERWATCH_ROLE"    : "204083728182411264",
    "VETERAN_ROLE"             : "216302320189833226",
    "OVERWATCH_AGENT_ROLE"     : "227935626954014720",
    "ESPORTS_SUB_ROLE"         : "230937138852659201",
    "BLIZZARD_SUB_ROLE"        : "231198164210810880",
    "DISCORD_SUB_ROLE"         : "231199148647383040",
    "DJ_ROLE"                  : "231852994780594176",
}

# noinspection PyTypeChecker
ID_ROLENAME_DICT = dict([[v, k] for k, v in ROLENAME_ID_DICT.items()])

NADIR_AUDIT_LOG_ID = "240320691868663809"

client = discord.Client()

BLACKLISTED_CHANNELS = (CHANNELNAME_CHANNELID_DICT["bot-log"], CHANNELNAME_CHANNELID_DICT["server-log"],
                        CHANNELNAME_CHANNELID_DICT["voice-channel-output"])

linkReg = reg = re.compile(r"(http(s?)://discord.gg/(\w+))", re.IGNORECASE)

lfgReg = re.compile(
    (r"(lf(G|\d))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF(((NA)|(EU))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|"
     "(http(s?)://discord.gg/)|(xbox)|(ps4)"), re.IGNORECASE)

VCInvite = None
VCMess = None
INITIALIZED = False


# noinspection PyPep8
async def parse_message_info(mess) -> dict:
    """
    :type mess: discord.Message
    """
    userid = mess.author.id
    messageContent = await ascii_string(mess.content)
    messageLength = len(messageContent)
    mentioned_users = []
    mentioned_channels = []
    mentioned_roles = []
    for x in mess.mentions:
        mentioned_users.append(str(x.id))
    for x in mess.channel_mentions:
        mentioned_channels.append(str(x.id))
    for x in mess.role_mentions:
        mentioned_roles.append(str(x.id))
    # str_mentioned_users = str(mentioned_users)[1:-1]
    # str_mentioned_channels = str(mentioned_channels)[1:-1]
    # str_mentioned_roles = str(mentioned_roles)[1:-1]
    info_dict = {
        "userid"            : userid,
        "content"           : messageContent,
        "length"            : messageLength,
        "date"              : mess.timestamp.isoformat(" "),
        "mentioned_users"   : mentioned_users,
        "mentioned_channels": mentioned_channels,
        "mentioned_roles"   : mentioned_roles,
        "channel_id"        : mess.channel.id,
        "server_id"         : mess.server.id,
        "mess_id"           : mess.id
    }
    return info_dict


async def parse_user_info(user) -> dict:
    """

    :type user: discord.User
    """
    info_dict = {
        "name"       : user.name,
        "id"         : user.id,
        "is_bot"     : user.bot,
        "avatar_url" : user.avatar_url,
        "mention_str": user.mention,
        "created_at" : user.created_at.isoformat(" "),

    }
    return info_dict


async def parse_member_info(member) -> dict:
    """
    :type member: discord.Member
    """
    info_dict = await parse_user_info(member)
    if member.nick is None:
        userNick = member.name
    else:
        userNick = member.nick

    userNick = await ascii_string(userNick)
    userNick = userNick.lower()

    roleIDs = []
    roleNames = []
    # print(member.roles)
    for x in member.roles:
        roleIDs.append(x.id)
        # print(roleIDs)
        roleNames.append(x.name)
        # print(roleNames)

    info_dict["role_ids"] = roleIDs
    info_dict["role_names"] = roleNames
    info_dict["color"] = member.color
    info_dict["nick"] = userNick
    info_dict["joined_at"] = member.joined_at.isoformat(" ")
    return info_dict


async def mongo_add_message_to_log(mess):
    messInfo = await parse_message_info(mess)
    result = await message_log_collection.insert_one(messInfo)


async def get_mentions(mess):
    target = mess.author

    await client.send_message(target, "Automated Mention Log Fetcher Starting Up!")
    await client.send_message(target, "Please respond with the number in the parentheses (X)")
    await client.send_message(target,
                              "Would you like to query personal mentions (1), admin/mod mentions (2), or both (3)?")

    response_mess = await get_response_int(target)
    if response_mess is not None:
        await get_logs_mentions(response_mess.content, mess)
    else:
        await client.send_message(target, "You have taken too long to respond! Please restart.")


async def get_response_int(target) -> discord.Message:
    """

    :type target: discord.User
    """

    def check(msg):
        if msg.server is None and msg.author.id == target.id:
            try:
                int(msg.content)
                return True
            except ValueError:
                return False

    return await client.wait_for_message(timeout=30, author=target, check=check)


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
    elif query_type == "3":
        cursor = overwatch_db.message_log.find({"$or": [
            {"mentioned_users": author_info["id"]},
            {"mentioned_roles": {"$in": author_info["role_ids"]}}
        ]})
    cursor.sort("date", -1)
    # await client.send_message(target, "DEBUG: Query Did Not Fail!")
    number_message_dict = {}
    count = 1
    message_choices_text = "```\n"
    await client.send_message(target, "Retrieving Messages! (0) to get more messages!")
    mention_choices_message = await client.send_message(target, "Please wait...")
    response = 0
    async for message_dict in cursor:
        user_info = await parse_member_info(target.server.get_member(message_dict["userid"]))
        # await client.send_message(target, "DEBUG: FOUND MATCH! " + message_dict["content"])
        number_message_dict[count] = message_dict
        message_choices_text += "(" + str(count) + ") [" + message_dict["date"][:19] + "][" + user_info["nick"] + "]:" + \
                                message_dict["content"] + "\n"
        if count % 5 == 0:
            message_choices_text += "\n```"
            await client.edit_message(mention_choices_message, message_choices_text)
            response = await get_response_int(target)
            if response is None:
                await client.send_message(target, "You have taken too long to respond! Please restart.")
                return
            elif response.content == "0":
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
        await client.send_message(target,
                                  " \n Selected Message: \n[" + selected_message["date"][:20] + "]: " +
                                  selected_message[
                                      "content"])

        await client.send_message(target,
                                  "\n\n\n\nHow many messages of context would you like to retrieve? Enter an integer")
        response = await get_response_int(target)
        response = int(response.content)
        # print("Response = " + str(response))
        cursor = overwatch_db.message_log.find(
            {
                "date"      : {"$lt": selected_message["date"]},
                "channel_id": selected_message["channel_id"]
            }, limit=response
        )
        cursor.sort("date", -1)
        contextMess = await client.send_message(target, "Please wait...")
        contextContent = ""

        async for message_dict in cursor:
            # print("DEBUG: FOUND MATCH! " + message_dict["content"])
            user_info = await parse_member_info(
                (client.get_server(message_dict["server_id"])).get_member(message_dict["userid"])
            )
            contextContent += "[" + message_dict["date"][:19] + "][" + user_info["name"] + "]: " + message_dict[
                "content"] + "\n"

        gist = gistClient.create(name="M3R-CY Log", description=selected_message["date"], public=True,
                                 content=contextContent)
        await client.edit_message(contextMess, gist["Gist-Link"])


    except ValueError as e:
        await client.send_message(target, "You entered something wrong! Oops!")
        print(traceback.format_exc())
    except TypeError as e:
        await client.send_message(target, "You entered something wrong! Oops!")
        print(traceback.format_exc())
    pass


async def initialize(mess):
    global INITIALIZED
    for role in client.get_server(OVERWATCH_SERVER_ID).roles:
        if role.id in ID_ROLENAME_DICT.keys():
            ROLENAME_ROLE_DICT[ID_ROLENAME_DICT[role.id]] = role
    channel_dict = {}
    for channel in client.get_server(OVERWATCH_SERVER_ID).channels:
        if channel.type == discord.ChannelType.text:
            channel_dict[await ascii_string(channel.name)] = channel.id
    INITIALIZED = True


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


@client.event
async def on_member_join(member):
    # await add_to_nick_id_list(member)
    await add_to_user_list(member)
    database.commit()
    return


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
    database.commit()


async def ascii_string(toascii):
    """
    :type toascii: str
    """

    return toascii.encode('ascii', 'ignore').decode("utf-8")


#
# async def increment_lfgd(author):
#     toExecute = "UPDATE useridlist SET lfgd = lfgd + 1 WHERE userid = (?)"
#     vars = (author.id,)
#     try:
#         database.execute(toExecute, vars)
#         database.commit()
#
#         cursor = database.cursor()
#         toExecute = "SELECT lfgd FROM useridlist WHERE userid = (?)"
#
#         cursor.execute(toExecute, vars)
#         database.commit()
#         return cursor.fetchone()
#     except:
#         print(traceback.format_exc())  # noinspection PyBroadException,PyPep8Naming
#

async def increment_lfgd_mongo(author):
    """

    :type author: discord.Member
    """
    result = await userinfo_collection.find_one_and_update(
        {"userid": author.id},
        {"$inc": {
            "lfg_count": 1
        }}, upsert=True, return_document=ReturnDocument.AFTER),
    print(result)
    return result[0]["lfg_count"]


async def add_to_user_list(member):
    """

    :type member: discord.Member
    """
    user_info = await parse_member_info(member)
    print("asdding")
    result = await userinfo_collection.update_one(
        {"userid": member.id},
        {
            "$addToSet": {"nicks"       : user_info["nick"],
                          "names"       : user_info["name"],
                          "avatar_urls" : user_info["avatar_url"],
                          "server_joins": user_info["joined_at"]},
            "$set"     : {"mention_str": user_info["mention_str"],
                          "created_at" : user_info["created_at"]},

        }
        , upsert=True
    )
    print(result.raw_result)
    pass


#
# async def add_to_nick_id_list(member):
#     userID = member.id
#     userName = await ascii_string(member.name)
#     if member.nick is None:
#         userNick = member.name
#     else:
#         userNick = member.nick
#
#     userNick = await ascii_string(userNick)
#     userNick = userNick.lower()
#
#     count = "SELECT lfgd FROM useridlist WHERE userid = (?)"
#     vars = (userID,)
#
#     cursor = database.cursor()
#     try:
#         cursor.execute(count, vars)
#         old_lfgd = cursor.fetchone()
#     except:
#         print(traceback.format_exc())
#
#     if old_lfgd is None:
#         old_lfgd = 0
#     else:
#         old_lfgd = int(old_lfgd[0])
#     try:
#         toExecute = "INSERT OR REPLACE INTO useridlist VALUES (?, ?, ?, ?)"
#         values = (userID, userNick, userName, old_lfgd)
#         database.execute(toExecute, values)
#     except:
#         print(traceback.format_exc())
#

async def get_role(mess, id):
    for x in mess.server.roles:
        if x.id == id:
            return x

async def authorize_user(command_list):
    print(command_list)
    user_id = command_list[0]
    type = command_list[1]
    if type == "get_art":
        with open(PATHS["comms"] + "art_credentials.txt", "a") as cred_list:
            cred_list.write(str(user_id) + "\n")
async def credential(member, level):
    """

    :type level: str
    :type member: discord.Member
    """

    author_info = await parse_member_info(member)
    role_whitelist = any(x in [ROLENAME_ID_DICT["TRUSTED_ROLE"], ROLENAME_ID_DICT["MVP_ROLE"]]
                         for x in author_info["role_ids"])
    mod_whitelist = member.server_permissions.manage_roles
    if level == "mod":
        return mod_whitelist
    elif level == "zenith":
        return member.id == ZENITH_ID
    elif level == "trusted":
        return mod_whitelist or role_whitelist
    elif level == "art":
        with open(PATHS["comms"] + "art_credentials.txt", "r") as cred_list:
            cred_list.readlines()
            return author_info["id"] in cred_list


@client.event
async def on_message(mess):
    """
    Called on client message reception
    :type mess: discord.Message
    """
    global VCMess
    global VCInvite
    global PATHS

    # Not a PM
    if mess.server is not None:
        if not INITIALIZED and mess.server.id == OVERWATCH_SERVER_ID:
            await initialize(mess)

        author_info = await parse_member_info(mess.author)

        if mess.channel.id not in BLACKLISTED_CHANNELS:
            await mongo_add_message_to_log(mess)

        # AUTHOR-ONLY
        if await credential(mess.author, "art") or await credential(mess.author, "trusted"):
            # art_channel = client.get_channel(CHANNELNAME_CHANNELID_DICT["fanart"])
            art_channel = client.get_channel("238380537251627008")
            with open(PATHS["comms"] + "artlist.txt") as art_list:
                files = art_list.readlines()
                rand_art = random.sample(files, 10)
                for artlink in rand_art:
                    await client.send_message(art_channel, artlink)
            rand_art = random.sample(files, 15)
        if await credential(mess.author, "zenith"):
            if "`auth" in mess.content:
                command = mess.content.replace("`auth ","")
                command_list = command.split(" ")
                await client.delete_message(mess)
                try:
                    await authorize_user(command_list)
                except:
                    print(traceback.format_exc())
            # NADIR PURGE
            if "`clear" in mess.content and mess.server.id == "236343416177295360":
                await client.purge_from(mess.channel)
            if "`rebuildnicks" in mess.content:
                for member in mess.server.members:
                    try:
                        await add_to_user_list(member)
                    except:
                        pass
            if mess.content.startswith("`purge"):
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(await parse_message_info(mess)))
                command = mess.content.replace("`purge ","")
                command_list = command.split(" ")
                number_to_remove = int(command_list[1])
                await client.delete_message(mess)
                async for message in client.logs_from(mess.channel):
                    print(number_to_remove)
                    print(command_list[0] + " " + command_list[1])
                    if message.author.id == command_list[0] and number_to_remove > 0:
                        await client.delete_message(message)
                        number_to_remove -= 1
                    else:
                        return
        # BLACK-LIST MODS
        if mess.author.id != MERCY_ID and not await credential(mess.author, "trusted"):
            # EXTRA-SERVER INVITE CHECKER
            if mess.channel.id not in BLACKLISTED_CHANNELS:
                match = reg.search(mess.content)
                if match is not None:
                    await invite_checker(mess, match)
            # LFG -> Audit
            if mess.channel.id == CHANNELNAME_CHANNELID_DICT["general-discussion"]:
                match = lfgReg.search(mess.content)
                if match is not None:
                    await client.send_message(client.get_channel(NADIR_AUDIT_LOG_ID), mess.content)

        # WHITE-LIST TRUSTED

        if mess.author.id != MERCY_ID and await credential(mess.author, "trusted"):
            if mess.content.startswith("`help"):
                command = mess.content.replace("`help","")
                command_list = [mess]

                command_list.extend(command.split(" "))
                print(command_list)

                await command_info(*command_list)
            # Gets banned userinfo dict
            if "`ui" in mess.content:
                try:
                    command = mess.content.split(" ", 1)[1]
                except IndexError:
                    command = mess.author.id

                user_dict = await get_user_info(mess.server.get_member(command))
                formatted = [list(map(str, x)) for x in user_dict.items()]
                await client.send_message(mess.channel,
                                          "```Found:\n" + await pretty_column(formatted, True) + "\n```")
                return

            # Get Mentions
            if "`getmentions" == mess.content:
                await get_mentions(mess)
                return
            # Call LFG autowarn
            if '`lfg' == mess.content[0:4]:
                lfgText = ("You're probably looking for <#182420486582435840> or <#185665683009306625>."
                           " Please avoid posting LFGs in ")
                channelString = mess.channel.mention
                lfgText += channelString
                await client.delete_message(mess)
                authorMention = ""
                if len(mess.mentions) > 0:
                    try:
                        author = mess.mentions[0]
                        authorMention = ", " + author.mention
                        count = await increment_lfgd_mongo(author)
                        authorMention += " (" + str(count) + ")"
                    except:
                        print(traceback.format_exc())

                else:
                    async for messageCheck in client.logs_from(mess.channel, 8):
                        if messageCheck.author.id != MERCY_ID:  # and not mess.author.server_permissions.manage_roles:
                            match = lfgReg.search(messageCheck.content)
                            if match is not None:
                                authorMention = ", " + messageCheck.author.mention
                                count = await increment_lfgd_mongo(messageCheck.author)
                                authorMention += " (" + str(count) + ")"
                                break
                        else:
                            authorMention = ""
                lfgText += authorMention
                await client.send_message(mess.channel, lfgText)
            # Kill Bot
            if mess.author.server_permissions.manage_roles:
                if "`kill" in mess.content:
                    await client.send_message(mess.channel, "Shut down by " + mess.author.name)
                    await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "Shut down by " + mess.author.name)
                    await client.logout()
            # Generate Join Link
            if "`join" == mess.content[0:5]:
                VCMess = mess
                instainvite = await get_vc_link(mess)
                VCInvite = await client.send_message(mess.channel, instainvite)
            # Ping bot
            if "`ping" == mess.content: await ping(mess)
            # Fuzzy Nick Find
            if "`find" == mess.content[0:5]:
                command = mess.content[6:]
                command = command.lower()
                command = command.split("|", 2)
                await fuzzy_match(mess, *command)
            # Get previous nicknames
            if mess.content.startswith("`getnicks"):
                command = mess.content.strip("`getnicks ")
                nicklist = await get_previous_nicks(mess.server.get_member(command))
                await client.send_message(mess.channel, str(nicklist)[1:-1])
                pass


async def invite_checker(mess, regex_match):
    """

    :type regex_match: re.match
    :type mess: discord.Message
    """
    try:
        invite = await client.get_invite(regex_match.group(1))
        serverID = invite.server.id

        if serverID != OVERWATCH_SERVER_ID:
            channel = mess.channel
            # await client.send_message(mess.channel, serverID + " " + OVERWATCH_ID)
            warn = await client.send_message(mess.channel,
                                             "Please don't link other discord servers here " +
                                             mess.author.mention + "\n" +
                                             mess.server.get_member(ZENITH_ID).mention)
            await client.delete_message(mess)

            await log_automated("deleted an external invite: " + str(invite.url) + " from " + mess.author.mention)
            await client.send_message(client.get_channel(CHANNELNAME_CHANNELID_DICT["spam-channel"]),
                                      "~an " + mess.author.mention +
                                      " AUTOMATED: Posted a link to another server")
    except discord.errors.NotFound:
        pass
    except:
        print(traceback.format_exc())


# noinspection PyPep8Naming
async def get_vc_link(mess):
    """

    :type mess: discord.Message
    """
    if len(mess.mentions) > 0:
        mentionedUser = mess.mentions[0]
    else:
        userID = mess.content[6:]
        mentionedUser = mess.server.get_member(userID)
    vc = mentionedUser.voice.voice_channel
    instaInvite = await client.create_invite(vc, max_uses=1, max_age=6)
    return instaInvite.url


async def log_automated(description):
    action = ("At " + str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")) + ", I automatically "
              + str(description) + "\n" + "`kill to disable me")
    await client.send_message(client.get_channel(CHANNELNAME_CHANNELID_DICT["spam-channel"]), action)


async def command_info(*args):
    info_list = []
    if len(args) == 2:
        info_list = [
            ["Command ", "Description ", "Usage"],
            ["<Trusted>,", " ", " "],
            ["`ui", "Retrieves user info", "`ui *<userid>"],
            ["`getmentions", "Mention retrieval", "`getmentions"],
            ["`lfg", "Automated lfg logger and copypasta warning", "`lfg \*<mention> \*<userid>"],
            ["`ping", "Gets a random mercy voice-line and bot ping", "`ping"],
            [" ", " ", " "],

        ]
        if await credential(args[0].author, "mod"):
            info_list.append(["<Moderator>", " ", " "])
            info_list.append(["`kill", "[Disconnects bot]", "`kill"])
            info_list.append(["`join", "[Gets an invite for a user's current VC]", "`join <userid>"])
            info_list.append(["`find", "[Finds users that have had similar nicknames]", "`find <nick>|<count>"])
            info_list.append(["`getnicks", "[Gets the previous nicknames of a user]", "`getnicks <id>"])
    await client.send_message(args[0].channel, "```prolog\n" + await pretty_column(info_list, True) + "```")


async def ping(message):
    # lag = (datetime.utcnow() - message).timestamp.total_seconds() * 1000) + " ms")
    """
    :type message: discord.Message
    """
    voiceLines = (
        "Did someone call a doctor?",
        "Right beside you.",
        "I've got you.",
        "Where does it hurt?",
        "Patching you up.",
        "Let's get you back out there.",
        "Heilstrahl aktiviert.",
        "Healing stream engaged.",
        "I'm taking care of you.",
        "Ich kümmere mich um dich.",
        "Mercy im Bereitschaftsdienst.",
        "You're coming with me.",
        "Powered up.",
        "Schaden verstärkt.",
        "Ich bin da.",
        "I'm here.",
        "Right beside you.",
        "Support has arrived.",
        "Mercy on call.",
        "I'll be watching over you.",
        "A speedy recovery.",
        "Back to square one.",
        "Now, where am I needed?",
        "Back in the fight.",
        "Valkyrie online.",
        "Die Wunder der modernen Medizin.",
        "The wonders of modern medicine!",
        "A clean bill of health.",
        "Good as new.",
        "Immer unterbricht mich jemand bei der Arbeit.")
    timestamp = message.timestamp
    channel = message.channel
    await client.delete_message(message)
    voice = random.choice(voiceLines)
    sent = await client.send_message(channel, voice)
    await client.edit_message(sent,
                              voice + " (" + str(
                                  (sent.timestamp - timestamp).total_seconds() * 500) + " ms) " +
                              message.author.mention)



async def get_previous_nicks(member) -> list:
    """

    :type member: discord.Member
    """
    userinfo_dict = await userinfo_collection.find_one({"userid": member.id})
    return list(userinfo_dict["nicks"])


async def fuzzy_match(*args):
    if len(args) == 2:
        count = 1
    else:
        count = args[2]
    nickToFind = args[1]
    mess = args[0]

    # cursor = database.cursor()
    # cursor.execute('SELECT userid,nickname FROM useridlist')
    # nickIdList = cursor.fetchall()
    nickIdDict = {}

    mongo_cursor = userinfo_collection.find()
    async for userinfo_dict in mongo_cursor:
        for nick in userinfo_dict["nicks"]:
            nickIdDict.setdefault(nick, []).append(userinfo_dict["userid"])
            # nickIdDict.setdefault(nick, []).append(id)

    # for id, nick in nickIdList:
    #     nickIdDict.setdefault(nick, []).append(id)

    # noinspection PyUnusedLocal
    nickFuzz = {}

    for nick in nickIdDict.keys():
        ratio = fuzz.ratio(nickToFind, str(nick))
        nickFuzz[str(nick)] = int(ratio)

    topNicks = heapq.nlargest(int(count), nickFuzz, key=lambda k: nickFuzz[k])

    for nick in topNicks:
        userID = nickIdDict[nick]
        messageToSend = "```\n"
        prettyList = []
        for singleID in userID:
            prettyList.append(["ID: '" + str(singleID) + "'",
                               "| Nickname: " + nick,
                               " (" + str(nickFuzz[nick]) + ")"])

        messageToSend += await pretty_column(prettyList, True)
        messageToSend += "```"
        await client.send_message(mess.channel, messageToSend)


async def manually_reset():
    pass


async def get_user_info(member):
    """

    :type member: discord.Member
    """
    mongo_cursor = await userinfo_collection.find_one(
        {"userid": member.id}
    )
    return mongo_cursor


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
    print(output)
    return output


# client.loop.create_task(stream())
client.run("MjM2MzQxMTkzODQyMDk4MTc3.CvBk5w.gr9Uv5OnhXLL3I14jFmn0IcesUE", bot=True)
