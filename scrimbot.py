import motor.motor_asyncio
import discord
import asyncio
import TOKENS
import os
import sys
import constants

mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
client = discord.Client()
os.environ["PYTHONUNBUFFERED"] = "True"
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys

sys.stdout = Unbuffered(sys.stdout)
event_dict = {}


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
    auths = await get_auths(message_in.author)
    print(command)
    if message_in.author.id == constants.ZENITH_ID:
        if command == "reboot":
            await client.logout()
        elif command == "rebuild_muted_perms":
            muted_perms = discord.PermissionOverwrite()
            muted_perms.connect = False
            muted_perms.speak = False
            muted_perms.mute_members = False
            muted_perms.deafen_members = False
            muted_perms.move_members = False
            muted_perms.use_voice_activation = False
            for channel in message_in.server.channels:
                if channel.type == discord.ChannelType.voice:
                    await client.edit_channel_permissions(
                        channel,
                        await get_role(message_in.server,
                                       "295230064302358528"),
                        overwrite=muted_perms)
                    print("Applying to...{}".format(channel.name))
            muted_perms = discord.PermissionOverwrite()
            muted_perms.send_messages = False
            for channel in message_in.server.channels:
                if channel.type == discord.ChannelType.text:
                    await client.edit_channel_permissions(
                        channel,
                        await get_role(message_in.server,
                                       "295230064302358528"),
                        overwrite=muted_perms)
                    print("Applying to...{}".format(channel.name))
    if message_in.channel.id == "263360306984517633":
        parse_event(message_in.content)
    if command == "role":
        for region in params:
            region = region.lower()
            print(region)
            if region in ["na", "north america"]:
                await toggle_role(message_in.author, "310187563317067776")
            elif region in ["eu", "europe"]:
                await toggle_role(message_in.author, "310187546497908738")
            elif region in ["oce", "aus"]:
                await toggle_role(message_in.author, "310187573849096193")
            else:
                return
            await client.delete_message(message_in)

    if "host" in auths:
        if command == "create":
            if len(params) == 0:
                await client.send_message(message_in.channel, "Please enter a scrim name.")
                params[0] = (await client.wait_for_message(author=message_in.author, channel=message_in.channel)).content
            new_scrim_name = event_dict[" ".join(params)]
            event_dict[new_scrim_name] = scrim_event(new_scrim_name)

            await client.send_message(message_in.channel, "Please enter a time in the format `hh:mm timezone`. For example, 18:30 CET")

            await client.send_message(message_in.channe, "If you would like to attach a description, please respond with one. Otherwise, say `done`")
            in_mess = await client.wait_for_message(author=message_in.author, channel=message_in.channel)
            if in_mess.content != "done":
                event_dict[new_scrim_name].name = in_mess.content


    pass




async def toggle_role(member, role_id):
    role = await get_role(member.server, role_id)
    if role in member.roles:
        await client.remove_roles(member, role)
    else:
        await client.add_roles(member, role)


async def parse_event(text):
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


async def get_auths(member):
    perms = set()
    if "261550254418034688" in [role.id for role in member.roles]:
        perms |= {"host"}
    if any(mod_id in [role.id for role in member.roles] for mod_id in ["260186671641919490", "261550254418034688"]):
        perms |= {"mod"}
        perms |= {"host"}
    if "129706966460137472" == member.id:
        perms |= {"zenith"}
        perms |= {"mod"}
        perms |= {"host"}
    return perms


class scrim_event:
    def __init__(self, name):
        self.name = name
        self.members = []

    def attach(self, member):
        self.members.append(member)

    def detatch(self, member):
        self.members.remove(member)

    def output_members(self):
        return "\n".join(member.name + " " + member.discriminator for member in self.members)

    def output_pings(self):
        return "\n".join(member.mention for member in self.members)

    def __eq__(self, other):
        if isinstance(other, scrim_event):
            return self.name == other.name
        return False


async def tick():
    pass


async def clock():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(2)
        await tick()


client.loop.create_task(clock())
client.run(TOKENS.SCRIM_TOKEN, bot=True)
