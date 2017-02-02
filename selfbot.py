"""Provide an asynchronous equivalent *to exec*."""

# from . import compat
import discord
import logging
import urbandictionary
from TOKENS import *

logging.basicConfig(level=logging.INFO)

from pip.utils import logging


# from io import BytesIO, StringIO
# from concurrent.futures import ProcessPoolExecutor
# import pandas as pd

client = discord.Client()

@client.event
async def on_message(message_in):
    if message_in.author == client.user:
        if message_in.content.startswith("%%"):
            command = message_in.content.replace("%%", "")
            command_list = command.split(" ")
            await client.delete_message(message_in)
            if command_list[0] == "pfp":
                pfp = command_list[1]
                print("Switching to " + pfp)
                try:
                    with open(pfp + ".png", "rb") as pfp:
                        await client.edit_profile(password=PASS, avatar=pfp.read())
                except:
                    with open("default.png", "rb") as pfp:
                        await client.edit_profile(password=PASS, avatar=pfp.read())
            if command_list[0] == "owner":
                await client.send_message(message_in.channel, message_in.server.owner.name)
            if command_list[0] == "ud":
                defs = urbandictionary.define(" ".join(command_list[1:]))
                await client.send_message(message_in.channel, defs[0])
            if command_list[0] == "servers":
                text = ""
                text = "\n".join(server.name + " " + str(server.member_count) for server in client.servers)
                await client.send_message(message_in.channel, text)
            if command_list[0] == "rs":
                await client.send_message(client.get_channel("176236425384034304"), ".restart")


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)



client.run(ZENITH_AUTH_TOKEN, bot=False)
