import motor.motor_asyncio
import discord
import asyncio

mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
client = discord.Client()


@client.event
async def on_message(message_in):
    parameterized = message_in.split(" ")
    command = parameterized[0]
    params = parameterized[1:]

    if command == "role":
        for region in params:
            region = region.lower()
            if region in ["na", "north america"]:
                await toggle_role(message_in.author, )
            elif region in ["eu", "europe"]:
                pass
            elif region in ["oce","aus"]:
                pass
    pass


async def toggle_role(member, role):
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
    global STATES
    global temproles
    await client.wait_until_ready()
    global heatmap
    STATES["init"] = True
    print(STATES["init"])
    while not client.is_closed:
        await asyncio.sleep(2)
        await tick()