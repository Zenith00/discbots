import logging
import traceback

import discord
import TOKENS


client = discord.Client()
logging.basicConfig(level=logging.INFO)


@client.event
async def on_message(message_in):
    try:
        if message_in.channel.id == "334043962094387201":
            if len(message_in.embeds) > 0 and message_in.content:
                await client.send_message(message_in.author, message_in.content, embed=discord.Embed().from_data(message_in.embeds[0]))
            elif len(message_in.embeds) > 0:
                await client.send_message(message_in.author, embed=message_in.embeds[0])
            elif message_in.content:
                await client.send_message(message_in.author, message_in.content)

            await client.delete_message(message_in)
    except:
        print(traceback.format_exc())

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

client.run(TOKENS.LINKBOT_TOKEN, bot=True)