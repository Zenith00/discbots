import asyncio
import datetime
import logging
import traceback

import discord
import praw
from praw import models as praw_models
import lux
import TOKENS
logging.basicConfig(level=logging.INFO)

CONFIG = lux.config.Config(botname="KVSRSTREAM").load()
client = lux.client.Lux(CONFIG)

redd = praw.Reddit(client_id=TOKENS.REDDIT_ID, client_secret=TOKENS.REDDIT_SECRET, user_agent="KVStream")



@asyncio.coroutine
async def astream():
    await client.wait_until_ready()
    for submission in redd.subreddit("kindvoice").stream.submissions():
        try:
            print("Yielding...?", flush=True)
            embed = discord.Embed()
            embed.set_author(name="/u/"+submission.author.name, icon_url=submission.author.icon_img,
                             url=f"https://www.reddit.com/u/{submission.author.name}")
            embed.description = lux.zutils.threshold_string(submission.selftext, 1000)
            embed.set_footer(text=f"Submitted at {datetime.datetime.utcfromtimestamp(submission.created_utc).isoformat(' ')}")
            channel = client.get_channel(540332172670926851)
            await channel.send(content=submission.shortlink, embed=embed)
        except:
            print(traceback.format_exc())

client.loop.create_task(astream())
client.run(CONFIG.TOKEN)
