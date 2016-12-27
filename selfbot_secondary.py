import asyncio
import discord
import logging
import constants
from simplegist.simplegist import Simplegist
from datetime import datetime
from utils_text import *
from TOKENS import *
from duration_timer import timer
from utils_file import *
client = discord.Client()
logging.basicConfig(level=logging.INFO)
gistClient = Simplegist()

art_timer = timer(1800)
art_on = False
@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
async def on_message(message):
    global art_on
    if message.author == client.user:
        if message.content.startswith("]]"):
            command = message.content.replace("]]", "")
            await client.delete_message(message)
            if command == "art":
                await client.send_message(client.get_server("262761876373372938"), "Toggling artbot from {} to {}".format(art_on, not art_on))
                art_on = not art_on
            if command == "1":
                modlist = await get_moderators(message.server)
                infodump = []
                for mod in modlist:
                    infodump.append([ascii(mod.name), mod.id])
                info = await pretty_column(infodump, True)
                print(str(info))
                # info = info.replace("'","")
                gist = gistClient.create(name="Modlist", description=message.server.name + " moderators",
                                         public=False,
                                         content=info)
                await client.send_message(client.get_server(constants.OVERWATCH_SERVER_ID).get_member(constants.ZENITH_ID), gist["Gist-Link"])

    if art_timer.is_next() and art_on:
        file = extract_line(artlist)
        if file != "":
            await client.send_message(client.get_server(constants.OVERWATCH_SERVER_ID).get_channel("168567769573490688"), file)
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

client.run(APSIS_AUTH_TOKEN, bot=False)