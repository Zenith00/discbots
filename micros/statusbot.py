import discord
import TOKENS
import mcstatus
import asyncio
client = discord.Client()



async def clock():
    await client.wait_until_ready()
    while not client.is_closed():
        await client.change_presence(
            activity=discord.Game(name=f"{mcstatus.MinecraftServer.lookup('owowatch.ardittristan.xyz').status().players.online} users online")
        )
        await asyncio.sleep(30)



client.loop.create_task(clock())



client.run(TOKENS.STATUSBOT_TOKEN, bot=True)