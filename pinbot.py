import logging
import discord
import lux
from utils import utils_image, utils_text
import pprint
import CONSTANTS
import itertools

pers_d = {}
pers_l = []
pers = None

logging.basicConfig(level=logging.INFO)
CONFIG = lux.config.Config(botname="PINBOT").load()

def check_auth(ctx: lux.contexter.Contexter) -> bool:
    print(ctx.config["ALLOWED_IDS"])
    print(str(role.id for role in ctx.m.author.roles))
    return ctx.m.author.id in ctx.config["ALLOWED_IDS"] or \
           any(role.id in ctx.config["ALLOWED_IDS"] for role in ctx.m.author.roles) or \
           ctx.m.author.id == 129706966460137472 or\
           ctx.m.author.guild_permissions.manage_guild

client = lux.client.Lux(CONFIG, auth_function=check_auth)



@client.command(onlyme=True)
async def aexec(ctx: lux.contexter.Contexter):
    return lux.zutils.execute("aexec", ctx.deprefixed_content[6:], ctx=ctx)

@client.command(onlyme=True)
async def eval(ctx: lux.contexter.Contexter):
    return lux.zutils.execute("eval", ctx.deprefixed_content[5:], ctx=ctx)

@client.command(onlyme=True)
async def exec(ctx: lux.contexter.Contexter):
    return lux.zutils.execute("exec", ctx.deprefixed_content[5:], ctx=ctx)

@client.command(onlyme=True)
async def aeval(ctx: lux.contexter.Contexter):
    return await lux.zutils.aeval(ctx.deprefixed_content[6:], ctx=ctx)

@client.command(authtype="whitelist", name="help")
async def get_help(ctx: lux.contexter.Contexter):
    message_list = [f"```{block}```" for block in utils_text.format_rows(CONSTANTS.PINBOT["COMMAND_HELP"])]
    return message_list

@client.command(authtype="whitelist", posts=[(CONFIG.save, "sync", "noctx")])
async def whitelist(ctx: lux.contexter.Contexter):
    target_list = lux.dutils.mention_to_id(ctx.called_with["args"].split(" "))
    target = target_list[0]
    if not lux.zutils.check_int(target):
        target = ctx.find_role(target)
        if target:
            target = target.id
        else:
            return "Syntax error in [target]. Must be a mention, id, or role name"
    target = int(target)
    if target in ctx.config["ALLOWED_IDS"]:
        ctx.config["ALLOWED_IDS"].remove(target)
        target_role = ctx.find_role(target)
        if target_role:
            return f"Removed role `[{target_role.name}]` from command whitelist"
        target_member = ctx.m.guild.get_member(target)
        if target_member:
            return f"Removed member `[{str(target_member)}]` from command whitelist"
        else:
            return f"Removed ?unknown? `{target}` from command whitelist"
    else:
        ctx.config["ALLOWED_IDS"].append(int(target))
        target_role = ctx.find_role(target)
        if target_role:
            return f"Added role `[{target_role.name}]` to command whitelist"
        target_member = ctx.m.guild.get_member(target)
        if target_member:
            return f"Added member `[{str(target_member)}]` to command whitelist"
        else:
            return f"Added ?unknown? `{target}` to command whitelist"




@client.command(authtype="whitelist", posts=[(CONFIG.save, "sync", "noctx")])
async def config(ctx: lux.contexter.Contexter):
    args = ctx.called_with["args"].split(" ")
    args = [lux.zutils.intorstr(x) for x in args]
    subcommand, args = args[0], args[1:]
    if subcommand == "set":
        ctx.config[args[0]] = lux.zutils.intorstr(args[1])
        CONFIG.save()
        return f"Set key `{args[0]}` to be `{args[1]}`"
    elif subcommand == "print":
        return [f"```{block}```" for block in utils_text.format_rows(list(ctx.config.items()))]
    elif subcommand == "map":
        ctx.config["PINMAP"][lux.zutils.intorstr(args[0])] = lux.zutils.intorstr(args[1])
    elif subcommand == "unmap":
        del ctx.config["PINMAP"][args[0]]
    elif subcommand == "unset":
        CONFIG.reset_key(ctx.m.guild.id, args[0])
    elif subcommand == "reset":
        CONFIG.reset(ctx.m.guild.id)

@client.event
async def on_message_edit(message_bef: discord.Message, message_aft: discord.Message):
    ctx = lux.contexter.Contexter(message_aft, CONFIG, auth_func=check_auth)
    if ctx.m.channel.id in CONFIG.of(message_bef.guild)["PINMAP"].keys() and not message_bef.pinned and message_aft.pinned:
        await process_pin(ctx)

import datetime

async def process_pin(ctx: lux.contexter.Contexter):
    print("start")
    dt = lux.zutils.timeme(datetime.datetime.utcnow())
    channel_pins = await ctx.m.channel.pins()
    print("pins:")
    dt = lux.zutils.timeme(dt)
    if len(channel_pins) > ctx.config["PIN_THRESHOLD"]:
        earliest_pin = sorted(channel_pins, key=lambda x: x.created_at)[0]
        print("sorted pins")
        dt = lux.zutils.timeme(dt)
        target_channel = ctx.find_channel(query=ctx.config["PINMAP"][earliest_pin.channel.id], dynamic=True)
        print("found channel")
        dt = lux.zutils.timeme(dt)
        colour = None
        if ctx.config["EMBED_COLOR_CALC"]:
            avg_color = utils_image.average_color_url(earliest_pin.author.avatar_url)
            colour = discord.Colour.from_rgb(*avg_color)
        print("colorcalced")
        dt = lux.zutils.timeme(dt)
        await target_channel.send(content=earliest_pin.jump_url, embed=lux.dutils.message2embed(earliest_pin, embed_color=colour))
        print("sent message")
        dt = lux.zutils.timeme(dt)
        await earliest_pin.unpin()
        print("unpinned")
        dt = lux.zutils.timeme(dt)

def delta_messages(before: discord.Message, after: discord.Message):
    delta = set(lux.dutils.message2dict(before).items()) ^ set(lux.dutils.message2dict(after).items())
    delta_attrs = [i[0] for i in delta]
    print(delta_attrs)
    return delta_attrs

client.run(CONFIG.TOKEN, bot=True)
