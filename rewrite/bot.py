import discord
import asyncio
import logging

from command import router
import TOKENS
Command = router.CommandRouter()

PREFIX = "@@"


logging.basicConfig(level=logging.INFO)

class Client(discord.Client):
    async def on_ready(self):
        print("Ready!")
    async def on_message(self, message):
        if message.author == self.user:
            if message.content.startswith(PREFIX):
                message.content = message.content[len(PREFIX):]
                response = Command.build(*message.content.split(" ", 1))


client = Client()
client.run(TOKENS.token, bot=False)