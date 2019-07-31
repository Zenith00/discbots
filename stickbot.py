import asyncio
import logging

import discord

import CONFIG_DEFAULT
import lux

pers_d = {}
pers_l = []
pers = None

logging.basicConfig(level=logging.INFO)
CONFIG = lux.config.Config(botname="STICKBOT", config_defaults=CONFIG_DEFAULT.STICKBOT).load()


def check_auth(ctx: lux.contexter.Contexter) -> bool:
    if "ALLOWED_IDS" not in ctx.config:
        ctx.config["ALLOWED_IDS"] = []
        CONFIG.save()
    return ctx.m.author.id in ctx.config["ALLOWED_IDS"] or \
           any(role.id in ctx.config["ALLOWED_IDS"] for role in ctx.m.author.roles) or \
           ctx.m.author.id == 129706966460137472 or \
           ctx.m.author.guild_permissions.manage_guild

client = lux.client.Lux(CONFIG, auth_function=check_auth,
                        activity=discord.Game(name="Sticking Messages!"))

client.sticklock = asyncio.Lock()


@client.command(authtype="whitelist", posts=[(CONFIG.save, "sync", "noctx")], name="setprefix")
async def set_prefix(ctx: lux.contexter.Contexter):
    new_prefix = ctx.called_with["args"].split(" ")[0]
    resp = f"Prefix changed from `{ctx.config['PREFIX']}` to `{new_prefix}`"
    ctx.config["PREFIX"] = new_prefix
    return resp

@client.command(authtype="whitelist", posts=[(CONFIG.save, "sync", "noctx")], name="stick")
async def stick_message(ctx: lux.contexter.Contexter):
    args = lux.dutils.mention_to_id(ctx.called_with["args"].split(" "))
    message_id = int(args[0])
    message_to_stick = await ctx.m.channel.fetch_message(message_id)
    print(ctx.config)
    newmap = ctx.config["STICKMAP"].get(ctx.m.channel.id, [])
    newmap.append((message_to_stick.id, False))
    ctx.config["STICKMAP"][ctx.m.channel.id] = newmap
    print(ctx.config["STICKMAP"])
    return (f"Now sticking message [{message_to_stick.id}]<{message_to_stick.content[:15]}...> "
            f"in channel <#{message_to_stick.channel.id}>")


@client.command(authtype="whitelist", posts=[(CONFIG.save, "sync", "noctx")], name="unstick")
async def unstick_message(ctx: lux.contexter.Contexter):
    args = lux.dutils.mention_to_id(ctx.called_with["args"].split(" "))
    message_id = int(args[0])
    message_to_stick = await ctx.m.channel.fetch_message(message_id)
    newmap = ctx.config["STICKMAP"].get(ctx.m.channel.id, [])
    print(newmap)
    newmap = [entry for entry in newmap if entry[0] != message_id]
    ctx.config["STICKMAP"][ctx.m.channel.id] = newmap

    return (f"Unsticking message [{message_to_stick.id}]<{message_to_stick.content[:15]}...> "
            f"in channel <#{message_to_stick.channel.id}>")


@client.append_event
async def on_message(message: discord.Message):
    print("", flush=True)
    ctx = lux.contexter.Contexter(message=message, configs=CONFIG)
    if message.content.startswith(ctx.config["PREFIX"] + "stick"):
        return
    message_channel = message.channel
    if message_channel.id in ctx.config["STICKMAP"]:
        if client.sticklock.locked():
            return
        async with client.sticklock:
            print("LOCK START")
            print(f"Got message {message.id}, <<{message.content}>>, "
                  f"stickmap {ctx.config['STICKMAP'][message_channel.id]}")
            if message.id not in map(lambda x: x[0], ctx.config["STICKMAP"][message_channel.id]):
                new_sticks = []
                for sticked_message_id, fancy in ctx.config["STICKMAP"][message_channel.id]:
                    print(f"Fetching stuck message id {sticked_message_id} from channel {message_channel} type"
                          f" {type(sticked_message_id)}")
                    sticked_message = await message_channel.fetch_message(sticked_message_id)
                    replacement_message = await message_channel.send(content=sticked_message.content,
                                                                     embed=sticked_message.embeds[
                                                                         0] if sticked_message.embeds else None)
                    await sticked_message.delete()
                    new_sticks.append((replacement_message.id, fancy))
                ctx.config["STICKMAP"][message_channel.id] = new_sticks
                print(f"New stickmap {ctx.config['STICKMAP'][message_channel.id]}")
            print("LOCK END")
    CONFIG.save()


client.run(CONFIG.TOKEN, bot=True)
