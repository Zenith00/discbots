import ast
import csv
import re
import sqlite3
import traceback
from datetime import timedelta

import discord
from fuzzywuzzy import fuzz

PATHS = {}

with open("paths.txt", "r") as f:
    # global PATHS
    pathList = f.read()
    # noinspection PyRedeclaration
    PATHS = ast.literal_eval(pathList)

database = sqlite3.connect(PATHS["comms"] + "userIDlist.db")

messageBase = sqlite3.connect("E:\\Logs\\messages.db")

ZENITH_ID = "129706966460137472"

global before

client = discord.Client()
lfgReg = re.compile("/lf(G|\d)/ig")


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


@client.event
async def on_member_join(member):
    # if "!startup" in mess.content:
    print("NEW USER JOINED")

    await add_to_nickIdList(member)
    database.commit()
    return


# noinspection PyShadowingNames
@client.event
async def on_member_update(before, after):
    if before.nick is not after.nick:
        await add_to_nickIdList(after)


async def ascii_string(toascii):
    return toascii.encode('ascii', 'ignore').decode("utf-8")


# noinspection PyBroadException,PyPep8Naming
async def add_to_nickIdList(member):
    userID = member.id
    userNick = member.nick
    userName = await ascii_string(member.name)
    if userNick is None:
        userNick = userName
    else:
        userNick = await ascii_string(userNick)

    userNick = userNick.lower()

    toExecute = "INSERT INTO useridlist VALUES (?, ?, ?)"
    values = (userID, userNick, userName)
    try:
        database.execute(toExecute, values)
    # print(str(database.commit()))
    except:
        pass


@client.event
async def on_message(mess):
    global PATHS
    if "!join" == mess.content[0:5]:
        instainvite = await get_vc_link(mess)
        await client.send_message(mess.channel, instainvite)
    if "!find" == mess.content[0:5]:
        command = mess.content[6:]
        await fuzzy_match(command, mess)

    if mess.channel.id == "240310063082897409":
        await client.send_message(client.get_channel("240320691868663809"), mess.content)
    if "!clear" in mess.content and mess.server.id == "236343416177295360":
        await client.purge_from(mess.channel)

    if mess.author.id == ZENITH_ID:
        if "!tetactivity" in mess.content:
            await getactivity(mess)
        if "!rebuildIDs" in mess.content:
            database.execute('''CREATE TABLE useridlist (
                userid   STRING,
                nickname STRING,
                username STRING,
                UNIQUE (
                    userid
                )
            )''')
            print("BUILDING DATABASE")
            for member in mess.server.members:
                await add_to_nickIdList(member)
                database.commit()
            return
        if "!buildlogs" in mess.content:
            build_logs(mess)
        if "!firstbuild" in mess.content:
            messageBase.execute('''CREATE TABLE messageList (
                userid   TEXT,
                messageContent   TEXT,
                messageLength   INTEGER,
                dateSent   DATETIME
            )''')
            messageBase.commit()
    if mess.channel.id not in ["147153976687591424", "152757147288076297", "200185170249252865"]:
        add_message_to_log(mess)


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
                 "ID: " + str(userID) + " | Nickname: " + nick + " (" + str(topScore) + ")" ))


async def manually_reset():
    pass


# client.loop.create_task(stream())
client.run("MjM2MzQxMTkzODQyMDk4MTc3.CvBk5w.gr9Uv5OnhXLL3I14jFmn0IcesUE", bot=True)
