"""Provide an asynchronous equivalent *to exec*."""

import ast

# from . import compat
import discord
import re

from io import StringIO
import random
import asyncio
import sys
import traceback
from datetime import datetime

# from io import BytesIO, StringIO
# from concurrent.futures import ProcessPoolExecutor
# import pandas as pd

streamFile = "C:\\Users\\Austin\\Desktop\\Programming\\stream.txt"
# lock = filelock.FileLock(streamFile

PATHS = None

ZENITH_ID = "129706966460137472"

VCMess = None
VCInvite = None

# path =	"C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"

with open("paths.txt", "r") as f:
    # noinspection PyRedeclaration
    global PATHS
    pathList = f.read()
    # noinspection PyRedeclaration
    PATHS = ast.literal_eval(pathList)
    print("PATHS: " + str(PATHS))

# LFGBOT
print("Selfbot Starting Up")
client = discord.Client()
lfgReg = re.compile("/lf(G|\d)/ig")


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


async def ascii_string(string):
    return string.encode('ascii', 'ignore').decode("utf-8")


# noinspection PyShadowingNames,PyBroadException,PyBroadException,PyBroadException
@client.event
async def on_message(mess):
    global PATHS
    global VCMess
    global VCInvite
    path2 = PATHS["logs"]

    reg = re.compile(
        (r"(lf(G|\d))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF(((NA)|(EU))|(\s?\d)))|((NA|EU)"
         "(LF(g|\d)*))|(http(s?)://discord.gg/)|(xbox)|(ps4)"),

        re.IGNORECASE)
    match = reg.search(mess.content)
    if mess.author.id == ZENITH_ID:

        if "!setstatus" in mess.content:
            status = mess.content[11:]
            await client.change_presence(game=discord.Game(name=str(status)))
            return

        if match is not None and mess.channel.id == "94882524378968064":
            await client.send_message(client.get_channel("240310063082897409"), mess.content)
            return

        if "!getlogs" in mess.content:
            counter = 1
            async for message in client.logs_from(mess.channel, 1000000):
                counter += 1
                with open(path2 + "logs.txt", "a") as myfile:
                    try:
                        myfile.write(
                            message.timestamp.strftime("[%Y-%m-%d %H:%m:%S] ") + str(message.author.nick).encode(
                                'ascii', 'ignore').decode("utf-8") + ": " + message.content.encode('ascii',
                                                                                                   'ignore').decode(
                                "utf-8") + "\n")
                    except:
                        print("error")
                if counter % 200 == 0:
                    await client.edit_message(mess,
                                              "Log Retrieval at minimum " + str((float(counter) / 1000000) * 100) + "%")

            return

        if "!geticon" in mess.content:
            userID = mess.content[5:]
            user = await client.get_user_info(userID)
            await client.send_message(mess.channel, user.avatar_url)
            client.delete_message(mess)

        if "!run" in mess.content:
            code = mess.content[5:]
            result = None
            try:
                result = eval(code)
            except Exception:
                formatted_lines = traceback.format_exc().splitlines()
                await client.edit_message(mess, (
                    '```py\n{}\n{}\n```'.format(formatted_lines[-1], '/n'.join(formatted_lines[4:-1]))))

            if result:
                await client.edit_message(mess, "```py" + "\n" + "@Input:\n" + str(code) + "\n" + "@Output:\n" + str(
                    result) + "\n```")

        if "!exe" in mess.content:
            code = mess.content[5:]
            old_stdout = sys.stdout
            redirected_output = sys.stdout = StringIO()
            output = redirected_output
            try:
                exec(code)
            except Exception:
                formatted_lines = traceback.format_exc().splitlines()
                output = '```py\n{}\n{}\n```'.format(formatted_lines[-1], '\n'.join(formatted_lines[4:-1]))
            finally:
                sys.stdout = old_stdout

            if not isinstance(output, str):
                await client.edit_message(mess, output.getvalue())
            else:
                await client.edit_message(mess, str(output))
                print(output)

        if mess.content == '!count':
            asyncio.sleep(.5)
            await client.edit_message(mess, mess.server.member_count)
            asyncio.sleep(.5)
        if mess.content == '!refreshart':
            f = open(PATHS["comms"] + "botdata.txt", "r")
            for link in f:
                print("NOTE" * 3)
                stripLink = link.rstrip('\n')
                await client.send_message(mess.channel, stripLink)
                asyncio.sleep(1)
            f.close()
            f = open(PATHS["comms"] + "botdata.txt", "w")
            f.close()

        if mess.content == '!lfg':
            lfgText = ("You're probably looking for <#182420486582435840> or <#185665683009306625>."
                       "Please avoid posting LFGs in <#94882524378968064> . ")
            await client.edit_message(mess, lfgText)
            authorMention = ""

            async for messageCheck in client.logs_from(mess.channel, 8):
                if messageCheck.author.id != client.user.id:
                    print(messageCheck.content)
                    reg = re.compile(
                        (r"(lf(G|\d))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF(((NA)|(EU))|(\s?\d)))|((NA|EU)"
                         "(LF(g|\d)*))|(http(s?)://discord.gg/)|(xbox)|(ps4)"), re.IGNORECASE)
                    match = reg.search(messageCheck.content)
                if match is not None:
                    print("ASDF")
                    authorMention = "<@" + messageCheck.author.id + ">"
                    break
                else:
                    authorMention = ""
            lfgText += authorMention
            await client.edit_message(mess, lfgText)
    if "gib" in mess.content.lower() and "art" in mess.content.lower() and mess.server is None:
        print("SENDING \n" * 5)
        await client.send_message(mess.author, "http://bit.ly/zenithfanart")
    if mess.content == "!nothingbutfanarthere":
        f = open(PATHS["comms"] + "fileList.txt", "r")
        files = f.readline().split("^")
        f.close()
        print(files)
        rand_art = random.sample(files, 15)
        f = open(PATHS["comms"] + "toUpload.txt", "a")
        for artpiece in rand_art:
            print(artpiece)
            f.write(artpiece + "\n")
        f.close()
    if mess.content == "!ping":
        print(str(datetime.utcnow()))
        newMessContent = "Ping!\nPong! " + str(
            (datetime().utcnow() - mess.timestamp).total_seconds() * 1000) + " ms"
        await client.send_message(mess.channel, newMessContent)
        await client.delete_message(mess)
        return


client.run("mfa.u17NxslSy23KcTcaMF7bwTgqvCONorAJ7JClDguYJ-Gj1np9pWWlngdxn57DQ_qGY1Dbj8-GlxsvI1rXwAf3", bot=False)
