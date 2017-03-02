import logging

import discord
from simplegist.simplegist import Simplegist
from utils_text import *

import constants
from TOKENS import *
from utils.duration_timer import timer
from utils.utils_file import *

client = discord.Client()
logging.basicConfig(level=logging.INFO)
gistClient = Simplegist()

art_timer = timer(60*60*1)
art_on = False
@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
async def on_message(message_in):
    global art_on
    if message_in.author == client.user:
        if message_in.content.startswith("@@"):
            command = message_in.content.replace("@@", "")
            await client.delete_message(message_in)
            if command == "art":
                await client.send_message(client.get_server("262761876373372938"), "Toggling artbot from {} to {}".format(art_on, not art_on))
                art_on = not art_on
            if command.startswith("set"):
                command = command.replace("set ","")
                art_timer.set_time(int(command))

            if command == "1":
                modlist = await get_moderators(message_in.server)
                infodump = []
                for mod in modlist:
                    infodump.append([ascii(mod.name), mod.id])
                info = await pretty_column(infodump, True)
                print(str(info))
                # info = info.replace("'","")
                gist = gistClient.create(name="Modlist", description=message_in.server.name + " moderators",
                                         public=False,
                                         content=info)
                await client.send_message(client.get_server(constants.OVERWATCH_SERVER_ID).get_member(constants.ZENITH_ID), gist["Gist-Link"])

            if command == "linesplit":
                command = command.split("\n")
                channel = message_in.channel
                await client.delete_message(message_in)
                for x in command:
                    await client.send_message(channel, x)


    if art_timer.is_next() and art_on:
        file = extract_line(artlist)
        if file != "":
            await client.send_message(client.get_server(constants.OVERWATCH_SERVER_ID).get_channel("168567769573490688"), file)
        else:
            print("empty")
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