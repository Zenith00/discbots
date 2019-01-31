import logging

from googleapiclient import discovery
import TOKENS
import discord
import lux
from aioify import aioify
perspective_api = discovery.build('commentanalyzer', 'v1alpha1', developerKey=TOKENS.PERSPECTIVE_KEY)
CONFIG = lux.config.Config(botname="PHAROS").load()
client = lux.client.Lux(CONFIG)
logging.basicConfig(level=logging.INFO)

@aioify
def persp_req(content):
    print("requing with " + str(content))
    req = {
        "comment":{"text":content},
        "requestedAttributes":{"TOXICITY":{}, "SEVERE_TOXICITY":{}},
        "languages":["en"]
    }
    response = perspective_api.comments().analyze(body=req).execute()
    print(req)
    print(response)
    return response["attributeScores"]["TOXICITY"]["summaryScore"]["value"], response["attributeScores"]["SEVERE_TOXICITY"]["summaryScore"]["value"]

@client.event
async def on_message(message_in : discord.Message):
    if message_in.author == client.user:
        return
    toxicity, severe = persp_req(message_in.content)
    toxicity_string = str(round(toxicity * 100, 1)).rjust(4, "0") + "%"
    severe_toxicity_string = str(round(severe * 100, 1)).rjust(4, "0") + "%"

    embed = lux.dutils.message2embed(message_in).add_field(name="Toxicity", value=toxicity_string, inline=False).add_field(name="Toxicity2", value=severe_toxicity_string)
    embed.colour = discord.Colour.from_rgb(*lux.zutils.rgb_percent(toxicity))
    await message_in.guild.get_channel(537466385240948747).send(content=message_in.jump_url, embed=embed)

client.run(CONFIG.TOKEN, bot=True)
