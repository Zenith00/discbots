import asyncio
import datetime
import logging
import traceback

import aioify
import discord
import praw
from praw import models as praw_models
import lux
import TOKENS
logging.basicConfig(level=logging.INFO)

CONFIG = lux.config.Config(botname="KVSRSTREAM")
client = lux.client.Lux(CONFIG)

redd = praw.Reddit(client_id=TOKENS.REDDIT_ID, client_secret=TOKENS.REDDIT_SECRET, user_agent="KVStream")

@client.append_event
async def on_message(mess):
    print("Debug found message")


def astream():
    for submission in redd.subreddit("KindVoice").stream.submissions(skip_existing=True):
        try:
            print("Yielding...?", flush=True)
            embed = discord.Embed(title=submission.title)
            embed.set_author(name="/u/"+submission.author.name, icon_url=submission.author.icon_img,
                             url=f"https://www.reddit.com/u/{submission.author.name}")
            embed.description = lux.zutils.threshold_string(submission.selftext, 1000)
            embed.set_footer(text=f"Submitted at {datetime.datetime.utcfromtimestamp(submission.created_utc).isoformat(' ')}")
            channel = client.get_channel(540332172670926851)
            client.loop.create_task(channel.send(content=submission.shortlink, embed=embed))
        except:
            print(traceback.format_exc(), flush=True)

client.loop.run_in_executor(None, astream)
client.run(CONFIG.TOKEN)
