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
MERCY_ID = "236341193842098177"
ZENITH_ID = "129706966460137472"

MOD_CHAT_ID = "106091034852794368"
TRUSTED_CHAT_ID = "170185225526181890"
GENERAL_DISCUSSION_ID = "94882524378968064"

NADIR_AUDIT_LOG_ID = "240320691868663809"
global before

client = discord.Client()

linkReg = reg = re.compile(
    r"(http(s?)://discord.gg/(\w){5})",
    re.IGNORECASE)

lfgReg = re.compile(
    r"((lf(G|\d)))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF((((NA)|(EU)))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|(http(s?)://discord.gg/)|(xbox)|(ps4)",
    re.IGNORECASE)

VCInvite = None
VCMess = None


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

    toExecute = "INSERT OR REPLACE INTO useridlist VALUES (?, ?, ?, ?)"
    values = (userID, userNick, userName, 0)
    try:
        database.execute(toExecute, values)
    # print(str(database.commit()))
    except:
        print(traceback.format_exc())


@client.event
async def on_message(mess):
    global VCMess
    global VCInvite
    global PATHS

    if mess.author.id != MERCY_ID:
        if mess.channel.id == GENERAL_DISCUSSION_ID and not mess.author.server_permissions.manage_roles:
            match = lfgReg.search(mess.content)
            if match != None:
                await client.send_message(client.get_channel(NADIR_AUDIT_LOG_ID), mess.content)

        if mess.content == '`lfg' and mess.author.server_permissions.manage_roles:

            lfgText = ("You're probably looking for <#182420486582435840> or <#185665683009306625>."
                       "Please avoid posting LFGs in <#94882524378968064> . ")
            await client.delete_message(mess)
            authorMention = ""
            async for messageCheck in client.logs_from(mess.channel, 8):
                if messageCheck.author.id != MERCY_ID:  # and not mess.author.server_permissions.manage_roles:
                    match = lfgReg.search(messageCheck.content)
                    if match is not None:
                        authorMention = messageCheck.author.mention
                        count = await increment_lfgd(mess.author)
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
        if "`roles" in mess.content:
            for x in mess.server.roles:
                await client.send_message(mess.channel, x.name + " " + str(x.id))
        if "`join" == mess.content[0:5]:
            VCMess = mess
            instainvite = await get_vc_link(mess)
            VCInvite = await client.send_message(mess.channel, instainvite)
        if "`ping" == mess.content:
            await ping(mess)
        if "`find" == mess.content[0:5]:
            command = mess.content[6:]
            await fuzzy_match(command, mess)
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
        if mess.channel.id not in ["147153976687591424", "152757147288076297", "200185170249252865"]:
            await add_message_to_log(mess)

            if mess.channel.id not in [MOD_CHAT_ID, TRUSTED_CHAT_ID]:
                match = reg.search(mess.content)
                if match != None:
                    await invite_checker(mess, match)


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

            await log_automated("deleted an external invite: " + invite.url)
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
    await client.send_message(client.get_channel("209609220084072450"), action)


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
                              voice + " (" + str((sent.timestamp - message.timestamp).total_seconds() * 1000) + " ms)")


# noinspection PyBroadException
async def add_message_to_log(mess):
    userid = mess.author.id
    messageContent = await ascii_string(mess.content)
    messageLength = len(messageContent)
    dateSent = mess.timestamp

    toExecute = "INSERT INTO messageList VALUES (?, ?, ?, ?)"
    values = (userid, messageContent, messageLength, dateSent)
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


async def fuzzy_match(command, mess):
    sentMessages = [await client.send_message(mess.channel, "Input: " + command)]
    cursor = database.cursor()
    cursor.execute('SELECT userid,nickname FROM useridlist')
    nickIdList = cursor.fetchall()
    nickIdDict = {}
    for v, k in nickIdList:
        nickIdDict.setdefault(k, []).append(v)
    topScore = 0
    topNick = ""
    # noinspection PyUnusedLocal
    ratio = 0
    for k in nickIdDict.keys():
        ratio = fuzz.ratio(command, str(k))
        if ratio > topScore:
            topScore = ratio
            topNick = k
            print("new topScore: " + str(topScore))
            print("new nick: " + str(topNick))
    nick = topNick
    for userID in nickIdDict[nick]:
        sentMessages.append(
            await client.send_message(mess.channel,
                                      "ID: " + str(userID) + " | Nickname: " + nick + " (" + str(topScore) + ")"))


async def manually_reset():
    pass


# client.loop.create_task(stream())
client.run("MjM2MzQxMTkzODQyMDk4MTc3.CvBk5w.gr9Uv5OnhXLL3I14jFmn0IcesUE", bot=True)
