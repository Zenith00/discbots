import discord
import TOKENS


client = discord.Client()


@client.event
async def on_message(message_in):
    if message_in.channel.id == "334043962094387201":
        if message_in.embed and message_in.content:
            await client.send_message(message_in.author, message_in.content, embed=message_in.embed)
        elif message_in.embed:
            await client.send_message(message_in.author, embed=message_in.embed)
        elif message_in.content:
            await client.send_message(message_in.author, message_in.content)

        await client.delete_message(message_in)


client.run(TOKENS.LINKBOT_TOKEN, bot=True)