import logging
import discord
from CONFIG import PINBOT as CONFIG
import lux
from utils import utils_image

pers_d = {}
pers_l = []
pers = None

logging.basicConfig(level=logging.INFO)

client = lux.client.Lux(CONFIG)

@client.command(ack=CONFIG["ACK_TYPE"], onlyme=True)
async def aexec(ctx: lux.contexter.Contexter):
    return lux.zutils.execute("aexec", ctx.deprefixed_content[5:], ctx=ctx)

@client.command(ack=CONFIG["ACK_TYPE"], onlyme=True)
async def eval(ctx: lux.contexter.Contexter):
    return lux.zutils.execute("eval", ctx.deprefixed_content[4:], ctx=ctx)

@client.command(ack=CONFIG["ACK_TYPE"], onlyme=True)
async def exec(ctx: lux.contexter.Contexter):
    return lux.zutils.execute("exec", ctx.deprefixed_content[4:], ctx=ctx)

@client.command(ack=CONFIG["ACK_TYPE"], onlyme=True)
async def aeval(ctx: lux.contexter.Contexter):
    return await lux.zutils.aeval(ctx.deprefixed_content[5:], ctx=ctx)

@client.event
async def on_message_edit(message_bef: discord.Message, message_aft: discord.Message):
    ctx = lux.contexter.Contexter(message_aft, CONFIG)
    print(f"{ctx.m.channel.id} : {CONFIG['PINMAP'].keys()}")
    if ctx.m.channel.id in CONFIG["PINMAP"].keys() and not message_bef.pinned and message_aft.pinned:
        await process_pin(ctx)


async def process_pin(ctx: lux.contexter.Contexter):
    channel_pins = await ctx.m.channel.pins()
    if len(channel_pins) > CONFIG["PIN_THRESHOLD"]:
        earliest_pin = sorted(channel_pins, key=lambda x: x.created_at)[0]
        target_channel = ctx.find_channel(query=CONFIG["PINMAP"][earliest_pin.channel.id], dynamic=True)  # type: discord.TextChannel
        colour = None
        if CONFIG["EMBED_COLOR_CALC"]:
            avg_color = utils_image.average_color_url(earliest_pin.author.avatar_url)
            colour = discord.Colour.from_rgb(*avg_color)
        await target_channel.send(content=earliest_pin.jump_url, embed=lux.dutils.message2embed(earliest_pin, embed_color=colour))
        await earliest_pin.unpin()

def delta_messages(before: discord.Message, after: discord.Message):
    delta = set(lux.dutils.message2dict(before).items()) ^ set(lux.dutils.message2dict(after).items())
    delta_attrs = [i[0] for i in delta]
    print(delta_attrs)
    return delta_attrs

client.run(CONFIG["TOKEN"], bot=True)
