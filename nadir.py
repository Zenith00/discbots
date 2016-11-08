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

mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
overwatch_db = mongo_client.overwatch
message_log_collection = overwatch_db.message_log

PATHS = {}

with open("paths.txt", "r") as f:
    # global PATHS
    pathList = f.read()
    # noinspection PyRedeclaration
    PATHS = ast.literal_eval(pathList)

ADMIN_ID = "172949857164722176"
MOD_ID = "172950000412655616"
OVERWATCH_ID = "94882524378968064"
database = sqlite3.connect(PATHS["comms"] + "userIDlist.db")

messageBase = sqlite3.connect("E:\\Logs\\messages.db")

MERCY_ID = 236341193842098177
ZENITH_ID = 129706966460137472

MOD_CHAT_ID = 106091034852794368
TRUSTED_CHAT_ID = 170185225526181890
GENERAL_DISCUSSION_ID = 94882524378968064
SPAM_CHANNEL_ID = 209609220084072450

REDDIT_MODERATOR_ROLE = 94887153133162496
BLIZZARD_ROLE = 106536617967116288
MUTED_ROLE = 110595961490792448
MVP_ROLE = 117291830810247170
OMNIC_ROLE = 138132942542077952
TRUSTED_ROLE = 169728613216813056
ADMINISTRATOR_ROLE = 172949857164722176
MODERATOR_ROLE = 172950000412655616
DISCORD_STAFF_ROLE = 185217304533925888
PSEUDO_ADMINISTRATOR_ROLE = 188858581276164096
FOUNDER_ROLE = 197364237952221184
REDDIT_OVERWATCH_ROLE = 204083728182411264
VETERAN_ROLE = 216302320189833226
OVERWATCH_AGENT_ROLE = 227935626954014720
ESPORTS_SUB_ROLE = 230937138852659201
BLIZZARD_SUB_ROLE = 231198164210810880
DISCORD_SUB_ROLE = 231199148647383040
DJ_ROLE = 231852994780594176

NADIR_AUDIT_LOG_ID = "240320691868663809"
global before

client = discord.Client()

linkReg = reg = re.compile(
    r"(http(s?)://discord.gg/(\w+))",
    re.IGNORECASE)

lfgReg = re.compile(
    r"((lf(G|\d)))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF((((NA)|(EU)))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|(http(s?)://discord.gg/)|(xbox)|(ps4)",
    re.IGNORECASE)

VCInvite = None
VCMess = None


async def parse_message_info(mess):
    userid = mess.author.id
    messageContent = await ascii_string(mess.content)
    messageLength = len(messageContent)
    dateSent = mess.timestamp
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
        "mentioned_roles"   : mentioned_roles
    }
    return info_dict


async def mongo_add_message_to_log(mess):
    messInfo = await parse_message_info(mess)
    # str_mentioned_users = str(messInfo["mentioned_users"])[1:-1]
    # str_mentioned_channels = str(messInfo["mentioned_channels"])[1:-1]
    # str_mentioned_roles = str(messInfo["mentioned_roles"])[1:-1]
    mongo_dict = {
        "userid"            : messInfo["userid"],
        "content"           : messInfo["content"],
        "length"            : messInfo["length"],
        "date"              : messInfo["date"],
        "mentioned_users"   : messInfo["mentioned_users"],
        "mentioned_channels": messInfo["mentioned_channels"],
        "mentioned_roles"   : messInfo["mentioned_roles"],
    }
    result = await message_log_collection.insert_one(mongo_dict)


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


@client.event
async def on_member_join(member):
    await add_to_nickIdList(member)
    database.commit()
    return


@client.event
async def on_voice_state_update(before, after):
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
    if before.nick is not after.nick:
        # print("NEW NICKNAME FOUND: " + str(after.nick))
        await add_to_nickIdList(after)
    database.commit()


async def ascii_string(toascii):
    return toascii.encode('ascii', 'ignore').decode("utf-8")


async def increment_lfgd(author):
    toExecute = "UPDATE useridlist SET lfgd = lfgd + 1 WHERE userid = (?)"
    vars = (author.id,)
    try:
        database.execute(toExecute, vars)
        database.commit()

        cursor = database.cursor()
        toExecute = "SELECT lfgd FROM useridlist WHERE userid = (?)"

        cursor.execute(toExecute, vars)
        database.commit()
        return cursor.fetchone()
    except:
        print(traceback.format_exc())  # noinspection PyBroadException,PyPep8Naming


async def add_to_nickIdList(member):
    userID = member.id
    userName = await ascii_string(member.name)
    if member.nick is None:
        userNick = member.name
    else:
        userNick = member.nick

    userNick = await ascii_string(userNick)
    userNick = userNick.lower()

    count = "SELECT lfgd FROM useridlist WHERE userid = (?)"
    vars = (userID,)

    cursor = database.cursor()
    try:
        cursor.execute(count, vars)
        old_lfgd = cursor.fetchone()
    except:
        print(traceback.format_exc())

    if old_lfgd is None:
        old_lfgd = 0
    else:
        old_lfgd = int(old_lfgd[0])
    try:
        toExecute = "INSERT OR REPLACE INTO useridlist VALUES (?, ?, ?, ?)"
        values = (userID, userNick, userName, old_lfgd)
        database.execute(toExecute, values)
    except:
        print(traceback.format_exc())


async def get_role(mess, id):
    for x in mess.server.roles:
        if x.id == id:
            return x


@client.event
async def on_message(mess):
    global VCMess
    global VCInvite
    global PATHS

    roles = []
    for x in mess.author.roles:
        roles.append(str(x.id))
    if mess.channel.id not in ["147153976687591424", "152757147288076297", "200185170249252865"]:
        #     await add_message_to_log(mess)
        await mongo_add_message_to_log(mess)

    # BLACKLIST MODS
    if mess.author.id != MERCY_ID and not (
                mess.author.server_permissions.manage_roles or
                any(x in [str(TRUSTED_ROLE), str(MVP_ROLE)] for x in roles)):
        if mess.channel.id not in ["147153976687591424", "152757147288076297",
                                   "200185170249252865"] and mess.channel.id not in [MOD_CHAT_ID, TRUSTED_CHAT_ID,
                                                                                     SPAM_CHANNEL_ID]:
            match = reg.search(mess.content)
            if match != None:
                await invite_checker(mess, match)


                # WHITELIST MODSt
    if mess.author.id != MERCY_ID and (
                mess.author.server_permissions.manage_roles or
                any(x in [str(TRUSTED_ROLE), str(MVP_ROLE)] for x in roles)):
        if "`getmentions" == mess.content:
            await get_mentions(mess)
            return
        if mess.channel.id == GENERAL_DISCUSSION_ID and not mess.author.server_permissions.manage_roles:
            match = lfgReg.search(mess.content)
            if match != None:
                await client.send_message(client.get_channel(NADIR_AUDIT_LOG_ID), mess.content)

        if '`lfg' == mess.content[0:4]:

            if mess.author.server_permissions.manage_roles or any(
                            x in [str(TRUSTED_ROLE), str(MVP_ROLE)] for x in roles):
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
                        count = await increment_lfgd(author)
                        authorMention += " (" + str(count[0]) + ")"
                    except:
                        print(traceback.format_exc())

                else:
                    async for messageCheck in client.logs_from(mess.channel, 8):
                        if messageCheck.author.id != MERCY_ID:  # and not mess.author.server_permissions.manage_roles:
                            match = lfgReg.search(messageCheck.content)
                            if match is not None:
                                authorMention = ", " + messageCheck.author.mention
                                count = await increment_lfgd(messageCheck.author)
                                authorMention += " (" + str(count[0]) + ")"
                                break
                        else:
                            authorMention = ""
                lfgText += authorMention
                await client.send_message(mess.channel, lfgText)

        if mess.author.server_permissions.manage_roles:
            if "`kill" in mess.content:
                await client.send_message(mess.channel, "Shut down by " + mess.author.name)
                await client.send_message(client.get_channel(NADIR_AUDIT_LOG_ID), "Shut down by " + mess.author.name)
                await client.logout()
        if "`join" == mess.content[0:5]:
            VCMess = mess
            instainvite = await get_vc_link(mess)
            VCInvite = await client.send_message(mess.channel, instainvite)
        if "`ping" == mess.content:
            await ping(mess)
        if "`find" == mess.content[0:5]:
            command = mess.content[6:]
            command = command.lower()
            command = command.split("|", 2)
            await fuzzy_match(mess, *command)

        if mess.channel.id == "240310063082897409":
            await client.send_message(client.get_channel("240320691868663809"), mess.content)
        if mess.author.id == ZENITH_ID:
            if "`clear" in mess.content and mess.server.id == "236343416177295360":
                await client.purge_from(mess.channel)
            if "`tetactivity" in mess.content:
                await getactivity(mess)
            if "`rebuildIDs" in mess.content:
                database.execute('''CREATE TABLE useridlist (
                    userid   TEXT,
                    nickname TEXT,
                    username TEXT,
                    lfgd     INTEGER DEFAULT(0),
                    UNIQUE (
                        userid
                    )
                )''')
                print("BUILDING DATABASE")
                for member in mess.server.members:
                    await add_to_nickIdList(member)
                    database.commit()
                return
            if "`buildlogs" in mess.content:
                build_logs(mess)
            if "`firstbuild" in mess.content:
                messageBase.execute('''CREATE TABLE messageList (
                    userid   TEXT,
                    messageContent   TEXT,
                    messageLength   INTEGER,
                    dateSent   DATETIME
                )''')
                messageBase.commit()


async def get_mentions(mess):
    target = mess.author

    await client.send_message(target, "Automated Mention Log Fetcher Starting Up!")
    await client.send_message(target, "Please respond with the number in the parentheses (X)")
    await client.send_message(target, "Would you like to query personal mentions (1), role mentions (2), or both (3)?")

    pass


async def get_logs_mentions(type):
    cursor = messageBase.cursor()
    toExecute = ""
    vars = ()
    toExecute = "SELECT author_id, content, channel_id, message_id  FROM messageLog "
    if type == 1:
        toExecute += "WHERE mentioned_users_ids LIKE (?)"
    elif type == 2:
        toExecute += "WHERE mentioned_role_ids LIKE (?)"
    elif type == 3:
        toExecute += "WHERE mentioned_users_ids LIKE (?)"

    try:
        messageBase.execute(toExecute, vars)
    # print(str(database.commit()))
    except:
        print(traceback.format_exc())


async def invite_checker(mess, regexMatch):
    try:
        invite = await client.get_invite(regexMatch.group(1))
        serverID = invite.server.id

        if serverID != OVERWATCH_ID:
            channel = mess.channel
            # await client.send_message(mess.channel, serverID + " " + OVERWATCH_ID)
            warn = await client.send_message(mess.channel,
                                             "Please don't link other discord servers here " +
                                             mess.author.mention + "\n" +
                                             mess.server.get_member(ZENITH_ID).mention)
            await client.delete_message(mess)

            await log_automated("deleted an external invite: " + str(invite.url) + " from " + mess.author.mention)
            await client.send_message(client.get_channel(SPAM_CHANNEL_ID), "~an " + mess.author.mention +
                                      " AUTOMATED: Posted a link to another server")
    except discord.errors.NotFound:
        pass
    except:
        print(traceback.format_exc())


# noinspection PyPep8Naming
async def get_vc_link(mess):
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
    await client.send_message(client.get_channel(SPAM_CHANNEL_ID), action)


async def ping(message):
    # lag = (datetime.utcnow() - message).timestamp.total_seconds() * 1000) + " ms")
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
    voice = random.choice(voiceLines)
    sent = await client.send_message(message.channel, voice)
    await client.edit_message(sent,
                              voice + " (" + str(
                                  (sent.timestamp - message.timestamp).total_seconds() * 1000) + " ms) " +
                              message.author.mention)
    await client.delete_message(message)


# noinspection PyBroadException
async def add_message_to_log(mess):
    userid = mess.author.id
    messageContent = await ascii_string(mess.content)
    messageLength = len(messageContent)
    dateSent = mess.timestamp
    mentioned_users = []
    mentioned_channels = []
    mentioned_roles = []
    for x in mess.mentions:
        mentioned_users.append(x.id)
    for x in mess.channel_mentions:
        mentioned_channels.append(x.id)
    for x in mess.role_mentions:
        mentioned_roles.append(x.id)

    toExecute = "INSERT INTO messageLog VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (dateSent, userid, messageContent, messageLength, mess.channel.id, mess.id, str(mentioned_users),
              str(mentioned_channels), str(mentioned_roles))

    try:
        messageBase.execute(toExecute, values)
    # print(str(database.commit()))
    except:
        print(traceback.format_exc())
    messageBase.commit()


async def build_logs(mess) -> object:
    """

    :rtype: object
    """
    channel = mess.channel
    async for message in client.logs_from(channel, 100000):
        pass


# noinspection PyBroadException
async def getactivity(mess):
    command = mess.content[13:]
    await client.delete_message(mess)
    d = timedelta(days=int(command))

    sinceTime = mess.timestamp - d
    messageCountConsolidated = []
    consolidatedDict = {}
    print(str(sinceTime))
    for channel in (y for y in mess.server.channels if y.type == discord.ChannelType.text):
        try:
            channelDict = {}
            messageCount = []
            count = 0
            async for message in client.logs_from(channel, 100000):
                count += 1
                for x in range(len(str(message.content)) - 1):
                    # messageCount.append(mess age.author.name)
                    author = await ascii_string(message.author.name)
                    channelDict[author] = channelDict.get(author, 0) + 1
                    # messageCountConsolidated.append(message.author.name)
                    consolidatedDict[author] = channelDict.get(author, 0) + 1
                if count % 100 == 0:
                    # noinspection PyTypeChecker
                    print(len(channelDict.keys()))
            print("messages retrieved: " + str(count))
            with open(PATHS["logs"] + str(channel.name) + ".csv", 'w', newline='') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL)

                for x in channelDict.keys():
                    print(channelDict[x])
                    user = await ascii_string(x)
                    count = channelDict[user]
                    wr.writerow([user, count])
        except:
            print(traceback.format_exc())

    print("finished")
    with open(PATHS["logs"] + "consolidated.csv", 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL)
        # print(messageCount)
        # for x in collections.Counter(messageCount).most_common():
        # y = (str(x[0]).encode('ascii','ignore').decode("utf-8"), str(x[1]).encode('ascii','ignore').decode("utf-8"))

        # print("y = " + str(y))
        # wr.writerow(list(y))
        for x in channelDict.keys():
            user = await ascii_string(x)
            count = channelDict[user]
            wr.writerow([user, count])
    return


# async def fuzzy_match(mess, nick, count):
async def fuzzy_match(*args):
    if len(args) == 2:
        count = 1
    else:
        count = args[2]
    nickToFind = args[1]
    mess = args[0]

    cursor = database.cursor()
    cursor.execute('SELECT userid,nickname FROM useridlist')
    nickIdList = cursor.fetchall()
    nickIdDict = {}
    for id, nick in nickIdList:
        nickIdDict.setdefault(nick, []).append(id)

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
            prettyList.append(["ID: '" + str(singleID),
                               "| Nickname: " + nick,
                               " (" + str(nickFuzz[nick]) + ")"])

        messageToSend += await pretty_column(prettyList)
        messageToSend += "```"
        await client.send_message(mess.channel, messageToSend)


async def manually_reset():
    pass


async def pretty_column(list_of_rows):
    widths = [max(map(len, col)) for col in zip(*list_of_rows)]
    output = ""
    for row in list_of_rows:
        output += ("  ".join((val.ljust(width) for val, width in zip(row, widths)))) + "\n"
    return output


# client.loop.create_task(stream())
client.run("MjM2MzQxMTkzODQyMDk4MTc3.CvBk5w.gr9Uv5OnhXLL3I14jFmn0IcesUE", bot=True)
