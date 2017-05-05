import motor.motor_asyncio
import discord
import asyncio
import TOKENS
import os
import sys

mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
client = discord.Client()
os.environ["PYTHONUNBUFFERED"] = "True"
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

@client.event
async def on_message(message_in):
    if message_in.author.id == client.user.id:
        return
    prefix = "!!"
    if not message_in.content.startswith(prefix):
        return
    parameterized = message_in.content.split(" ")
    command = parameterized[0].replace(prefix, "")
    params = parameterized[1:]
    print(command)
    if command == "role":
        for region in params:
            region = region.lower()
            print(region)
            if region in ["na", "north america"]:
                await toggle_role(message_in.author, "310187563317067776")
            elif region in ["eu", "europe"]:
                await toggle_role(message_in.author, "310187546497908738")
            elif region in ["oce","aus"]:
                await toggle_role(message_in.author, "310187573849096193")
    pass


async def toggle_role(member, role_id):
    role = get_role(member.server, role_id)
    if role in member.roles:
        await client.remove_roles(member, role)
    else:
        await client.add_roles(member, role)


async def get_auths(member):
    if any(role in member.roles for role in [await get_role(member.server, "269494920635613194"), await get_role(member.server, "260186671641919490")]):
        return "moderator"
    if await get_role(member.server, "261550254418034688"):
        return "host"
    pass

async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members

async def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x

async def tick():
    pass

async def clock():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(2)
        await tick()

client.loop.create_task(clock())
client.run(TOKENS.SCRIM_TOKEN, bot=True)