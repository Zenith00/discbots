import logging
import os
import traceback

import discord
import sys
from imgurpython import ImgurClient


from tkinter import Tk
from utils import utils_text, utils_file

import constants
from TOKENS import *

client = discord.Client()


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)



@client.event
async def on_message(message_in):
    if message_in.content.startswith("..getbans") and message_in.author == client.user:
        bans = await client.get_bans(client.get_server("94882524378968064"))
        print("\n".join(user.id for user in bans))


client.run(USER_AUTH_TOKEN, bot=False)