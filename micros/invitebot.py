import asyncio
import datetime
import random
import logging
import discord
import lux
from utils import utils_image, utils_text
import pprint
import CONSTANTS
import itertools
import ast

import  utils
logging.basicConfig(level=logging.INFO)
CONFIG = lux.config.Config(botname="INVITEBOT").load()


client = lux.client.Lux(CONFIG)

INVITE_DICTS = {}

async def update_invite_dicts():
    for guild in client.guilds:
        try:
            INVITE_DICTS[str(guild.id)] = await parse_invites(guild)
        except discord.errors.Forbidden:
            print("FAILED PERMS IN " + guild.name)


@client.event
async def on_member_join( member):
    await log_invite_use(guild=member.guild, member=member)


async def parse_invites( guild):
    new_invites = await guild.invites()
    new_invite_dict = {k:v for k,v in zip([invite.id for invite in new_invites], new_invites)}
    return new_invite_dict

async def send_invite_log( joined, invite):
    log_embed = discord.Embed(title=f"{joined} [{joined.id}] has joined".replace(" ",' '*2) + ' ' * (95 - 2*len(str(joined))) + "​​​​​​")
    log_embed.add_field(name="Inviter", value="(" + str(invite.inviter) + f") [{invite.inviter.id}]", inline=False)
    log_embed.add_field(name="Invite ID", value=invite.id)
    log_embed.add_field(name="Invite Uses", value="{invite_uses}/{invite_max}".format(invite_uses=invite.uses, invite_max=invite.max_uses if invite.max_uses != 0 else "∞"))
    log_embed.add_field(name="Invite Expiration", value="in {}".format(utils.utils_text.format_timedelta(datetime.timedelta(seconds=invite.max_age))) if invite.max_age != 0 else "Never")
    if joined.avatar_url:
        log_embed.set_thumbnail(url=joined.avatar_url)
        color = utils.utils_image.average_color_url(joined.avatar_url)
        log_embed.colour = discord.Colour(int(color, 16))
    log_embed.set_footer(text=datetime.datetime.utcnow().isoformat(" ")[:16])


    target_channel = client.get_channel()
    await target_channel.send(embed=log_embed)

async def log_invite_use( guild, member):
    new_invite_dict = await parse_invites(guild)
    used_invites = await find_used_invite(guild, new_invite_dict)
    if len(used_invites) == 1:
        await self.send_invite_log(member, used_invites[0])
    else:
        INVITE_DICTS[str(guild.id)] = new_invite_dict

async def find_used_invite( guild, new_invite_dict):
    changed_invites = []
    print(new_invite_dict)
    for key in new_invite_dict.keys():
        if new_invite_dict[key].uses != INVITE_DICTS[str(guild.id)][key].uses:
            changed_invites.append(new_invite_dict[key])
    return changed_invites

async def update_invite_task():
    await client.wait_until_ready()
    while not client.is_closed():
        await update_invite_dicts()
        await asyncio.sleep(1)

client.loop.create_task(update_invite_task)
client.run(CONFIG.TOKEN, bot=True)
