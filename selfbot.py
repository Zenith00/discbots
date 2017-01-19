"""Provide an asynchronous equivalent *to exec*."""

# from . import compat
import discord
import logging
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
            print(message_in.content)
            command = message_in.content.replace("%%", "")
            if command == "on":
                print("on")
                await client.delete_message(message_in)
                with open("on.png", "rb") as pfp:
                    await client.edit_profile(password=PASS, avatar=pfp.read())
                await client.change_nickname(message_in.server.get_member(client.user.id), "ZENITH")
            if command == "off":
                print("off")
                await client.delete_message(message_in)
                with open("off.png", "rb") as pfp:
                    await client.edit_profile(password=PASS, avatar=pfp.read())
                await client.change_nickname(message_in.server.get_member(client.user.id), "Zenith")



@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)



client.run(ZENITH_AUTH_TOKEN, bot=False)
