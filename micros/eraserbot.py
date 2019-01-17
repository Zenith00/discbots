
import pip

pip.main(["install", "discord.py"])

import discord

client = discord.Client()

@client.event
async def on_message(message_in):
    if message_in.author.id == client.user.id:
        if message_in.content.startswith("%%clear"):
            target_id = message_in.content.split(" ")[1]
            target_channel = [channel for channel in client.private_channels if target_id == channel.recipients[0].id][0]
            print(list([user.name for user in target_channel.recipients]))
            async for message in client.logs_from(target_channel, limit=200000000):
                try:
                    await client.delete_message(message)
                except:
                    pass

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

client.run("mfa.9NnDEsil8OGmYJ0SfOzJZJZ_oFGvBdyAO1IVGi2mMXvhvg4SNjlg89L4px15v_GUoIcnhOH9b9BqHlEKm4jP", bot=False)
