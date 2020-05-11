import discord
import TOKENS
import logging
import mcstatus
import asyncio
logging.basicConfig(level=logging.INFO)

client = discord.Client()

async def clock():
    await client.wait_until_ready()
    while True:
        try:

            await client.change_presence(
                activity=discord.Game(name=f"{mcstatus.MinecraftServer.lookup('owowatch.ardittristan.xyz').status().players.online} users online")
            )
            await asyncio.sleep(30)
        except:
            pass

client.loop.create_task(clock())
client.run(TOKENS.STATUSBOT_TOKEN, bot=True)