import logging
import os
import traceback

import discord
import sys
from imgurpython import ImgurClient


from simplegist.simplegist import Simplegist
from utils import utils_text, utils_file

import constants
from TOKENS import *
from utils.duration_timer import timer
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"
os.environ["PYTHONUNBUFFERED"] = "True"
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

client = discord.Client()
logging.basicConfig(level=logging.INFO)
gistClient = Simplegist()

art_timer = timer(1)
art_on = True
imgur = ImgurClient("5e1b2fcfcf0f36e",
                    "d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)
@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

    for image in imgur.get_album_images("KWuZF"):
        await client.send_message(client.get_channel("331605496077484034") , image.link)


@client.event
async def on_message(message_in):
    pass





async def get_moderators(server):
    users = []
    for role in server.roles:
        if role.permissions.manage_roles:
            members = await get_role_members(role)
            users.extend(members)
    return users

async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members

client.run(USER_AUTH_TOKEN, bot=False)