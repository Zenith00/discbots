import pip

pip.main(["install", "discord.py"])
pip.main(["install", "tqdm"])

import discord
import time
from tqdm import tqdm

client = discord.Client()


@client.event
async def on_message(message_in):
    if message_in.author.id == client.user.id:
        if message_in.content.startswith("%%clear"):
            target_id = message_in.content.split(" ")[1]
            for channel in tqdm(client.get_guild(int(target_id)).text_channels):
                with tqdm(desc="Messages deleted") as pbar:
                    async for message in channel.history(limit=200000000):
                        try:
                            await message.delete()
                            pbar.update(1)
                        except Exception as e:
                            print(e)
                        time.sleep(0.01)


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


client.run("TOKENGOESHERE", bot=False)
