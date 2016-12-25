import asyncio
import discord
import logging
from simplegist.simplegist import Simplegist
from datetime import datetime

from TOKENS import *
client = discord.Client()
logging.basicConfig(level=logging.DEBUG)
gistClient = Simplegist()

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
async def on_message(message):
    if message.author == client.user:
        if message.content.startswith("]]"):
            command = message.content.replace("]]", "")
            await client.delete_message(message)

            if command == "1":
                modlist = await get_moderators(message.server)
                gist = gistClient.create(name="Mods of " + message.server.name,
                                         description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                         public=False,
                                         content=str(modlist))
                print(gist)


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