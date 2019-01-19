import logging
import os
import traceback
import motor.motor_asyncio

import discord
import sys

from tkinter import Tk
from utils import utils_text, utils_file
import pymongo
import CONSTANTS
from utils.utils_text import *
import TOKENS

client = discord.Client()
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://{usn}:{pwd}@{site}".format(
        usn=TOKENS.MONGO_USN,
        pwd=TOKENS.MONGO_PASS,
        site=TOKENS.MONGO_SITE))

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
async def on_message(message_in):
    if message_in.content.startswith("..getage"):
        ages = {}
        for member in message_in.server.members:
            res = await mongo_client.discord.message_log.find_one({"user_id": member.id, "server_id": message_in.server.id},
                                                                  sort=[("date", pymongo.DESCENDING)])
            if res:
                ages[member.name] = res["date"]
            else:
                print(member.id)
        print(ages)
        await send(message_in.channel, dict2rows(ages), "rows")

async def send(destination, text, send_type, delete_in=0):
    if isinstance(destination, str):
        destination = await client.get_channel(destination)

    if send_type == "rows":
        print("FIRING")
        message_list = format_rows(text)
        for message in message_list:
            try:
                await client.send_message(destination,
                                          "```" + message.rstrip() + "```")
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

def dict2rows(in_dict):
    return [(k, str(v)) for k, v in in_dict.items()]

client.run("NDM2NzA0OTQxNDUzNzM3OTg0.DbrYrw.nTn7AeeqvLknBVkwUdEqcOKx884", bot=True)

dict = {
 'Zenith'           : '2017-07-30 00:19:45.052000', 'TEHHERO': '2017-07-30 00:19:09.150000', 'ScarletBliss': '2017-07-30 00:02:08.755000',
 'Dragory'          : '2017-07-28 12:02:24.507000', 'squeezetoy': '2017-07-29 21:29:52.887000', 'Polo': '2017-07-29 19:46:39.576000',
 'Syber'            : '2017-07-30 00:02:06.586000', 'TheSojum': '2017-07-29 20:42:40.836000', 'Mike': '2017-07-30 00:12:45.707000',
 'Yolt.exe™® \uf8ff': '2017-07-29 14:28:51.953000', 'Kyozel': '2017-07-29 18:49:19.418000', 'Krayon': '2017-07-29 07:15:32.763000',
 'RHDragoste'       : '2017-07-29 18:01:06.843000', 'Andrewﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠﾠ': '2017-07-30 00:17:20.788000', 'Saltwater': '2017-07-29 21:43:20.150000',
 'Titanium'         : '2017-07-29 18:10:42.119000', 'Rice': '2017-07-16 04:05:57.441000', 'Astolfo': '2017-07-29 20:19:09.538000',
 'KawaiiBot'        : '2017-07-29 20:07:24.671000', 'Bleach': '2017-07-28 16:29:41.330000', 'shiro': '2017-07-29 14:11:10.228000',
 'Moh'              : '2017-07-29 23:46:35.785000', 'WND': '2017-07-29 21:25:10.664000', 'dshna': '2017-07-20 20:21:36.395000',
 'ErisBot'          : '2017-07-21 14:26:57.698000', 'Hutch': '2017-07-29 22:19:17.659000', 'Lily': '2017-07-29 02:46:31.957000',
 'Nafayl'           : '2017-07-29 17:14:46.290000', 'キットちゃん': '2017-07-28 11:09:23.466000', 'DGauze': '2017-07-28 15:48:33.735000',
 'chels'            : '2017-07-29 01:10:03.936000', 'IIMrUniverse': '2017-07-23 07:52:43.011000', 'Scrab': '2017-07-29 19:51:36.850000',
 'Septapus'         : '2017-07-27 19:35:19.510000', 'lunu': '2017-07-30 00:08:34.795000', 'Kitana': '2017-07-29 19:45:39.908000',
 'Nova'             : '2017-07-29 22:41:36.074000', 'Safari_Mike': '2017-07-25 14:23:49.348000', 'Yukimaru': '2017-07-22 02:51:03.955000',
 'MarcySun'         : '2017-07-29 21:52:48.464000', 'Ignetia': '2017-07-29 21:27:16.285000', 'Sporta 🐸': '2017-07-29 21:49:50.887000',
 'Nadeko'           : '2017-07-29 19:46:39.921000', 'Dank Johnson': '2017-07-28 16:20:52.563000', 'Tatsumaki': '2017-07-26 20:39:20.826000',
 'whydavid'         : '2017-07-29 15:02:45.273000', 'Sodi': '2017-07-26 20:53:44.245000', 'Suu': '2017-07-29 17:14:46.103000',
 'kitty'            : '2017-07-29 00:59:43.086000', 'Soy': '2017-07-29 02:17:25.407000', 'Xamadam': '2017-07-29 19:27:09.183000',
 'Ismael'           : '2017-07-30 00:06:25.715000', 'Bud': '2017-07-29 22:11:34.088000', 'neon': '2017-07-23 04:29:51.523000',
 'CodeDoritos'      : '2017-07-29 23:59:11.615000', 'Neo-Tokyokko': '2017-07-28 22:11:38.281000', 'ividyon': '2017-07-29 22:36:24.071000',
 'sem'              : '2017-07-30 00:18:23.706000', 'Cam': '2017-07-30 00:01:39.544000', 'Dinomo': '2017-07-29 23:35:38.881000',
 'ropi'             : '2017-07-23 21:41:51.663000', 'yok': '2017-07-29 14:39:43.454000', 'Plutonium': '2017-07-27 21:29:03.244000',
 'chii'             : '2017-07-29 23:55:20.199000', 'Dyrexic': '2017-07-29 21:51:09.067000', 'DarknessZone': '2017-07-29 23:51:35.246000',
 'Teo'              : '2017-07-29 23:54:41.531000', 'Stan': '2017-07-29 00:11:49.660000', 'DawnKai': '2017-07-28 16:17:34.033000',
 'tonythunderbolt'  : '2017-07-28 20:07:15.858000', 'Nik': '2017-07-30 00:07:58.521000'}
