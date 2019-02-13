import collections
import discord
import pandas as pd
client = discord.Client()
import logging
logging.basicConfig(level=logging.INFO)
@client.event
async def on_message(message_in : discord.Message):
    if message_in.author == client.user and message_in.content == "!!dmgraph":
        print("Flattening...")
        results = collections.deque()
        for dt in await message_in.channel.history(limit=1E10).map(lambda x: x.created_at).flatten():
            results.append(dt)
        series = pd.Series(list(results)) # type: pd.Series
        series.to_pickle(f"{message_in.channel.recipient.name}.pckl")
        print("Done")

client.run("MTI5NzA2OTY2NDYwMTM3NDcy.DzUKzg.C4NRyrWDZQf5DeJTZHB97zvdqmQ", bot=False)