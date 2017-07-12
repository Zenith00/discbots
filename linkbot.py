import discord
import TOKENS


client = discord.Client()


@client.event
async def on_message(message_in):
    if message_in.channel.id == "334043962094387201":
        await client.send_message(message_in.author, message_in.content)
        await client.delete_message(message_in)


client.run(TOKENS.LINKBOT_TOKEN, bot=True)