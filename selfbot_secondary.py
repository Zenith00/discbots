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
    if message_in.author.id == "192169418502045697":
        try:
            code = utils_text.regex_test(r'[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+', message_in.content).group(0)
        except:
            print("No code?")
            return
        if code:
            r = Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(code)
            r.update()
            r.destroy()


client.run(USER_AUTH_TOKEN, bot=False)