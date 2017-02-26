"""Provide an asynchronous equivalent *to exec*."""

# from . import compat
import logging
import os
import textwrap
from io import BytesIO
import asyncio
import traceback
import utils_text
import discord
import requests
import urbandictionary
from PIL import Image
from googleapiclient import discovery
from imgurpython import ImgurClient

from TOKENS import *
from utils_text import multi_block

logging.basicConfig(level=logging.INFO)

perspective_api = discovery.build('commentanalyzer', 'v1alpha1', developerKey=GOOGLE_API_TOKEN)
client = discord.Client()
imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
                           IMGUR_REFRESH_TOKEN)


@client.event
async def on_message(message_in):
    if message_in.author == client.user and message_in.content.startswith("%%"):
        command = message_in.content.replace("%%", "")
        command_list = command.split(" ")
        await client.delete_message(message_in)
        output = None
        if command_list[0] == "pfp":
            pfp = command_list[1]
            print("Switching to " + pfp)
            try:
                with open(pfp + ".png", "rb") as pfp:
                    await client.edit_profile(password=PASS, avatar=pfp.read())
            except:
                with open("default.png", "rb") as pfp:
                    await client.edit_profile(password=PASS, avatar=pfp.read())
        if command_list[0] == "owner":
            output.append((message_in.server.owner.name, "text"))
        if command_list[0] == "ud":
            defs = urbandictionary.define(" ".join(command_list[1:]))
            output.append((defs, "text"))
        if command_list[0] == "servers":
            server_list = [[server.name, str(server.member_count)] for server in client.servers]
            output.append((server_list, "rows"))
        if command_list[0] == "rs":
            await client.send_message(client.get_channel("176236425384034304"), ".restart")
        if command_list[0] == "big":
            text = str(" ".join(command_list[1:]))
            big_text = ""
            for character in text:
                if character == " ":
                    big_text += "     "
                else:
                    big_text += "​:regional_indicator_{c}:".format(c=character)
            output.append((big_text, "text"))
        if command_list[0] == "jpeg":
            url = command_list[1]
            url = await more_jpeg(url)
            output.append(("{url}. Compressed to {ratio}% of original".format(url=url[0], ratio=url[1]), "text"))
        if command_list[0] == "helix":
            helix = ("{helix_left}　{helix_right}\n   {helix_left}{helix_right}\n　 {helix_right}\n   {helix_right}{helix_left}\n {helix_right}　"
                     "{helix_left}\n{helix_right}　　{helix_left}\n{helix_right}　　{helix_left}\n {helix_right}　{helix_left}\n  {helix_right} "
                     "{helix_left}\n　  {helix_left}\n　{helix_left} {helix_right}\n {helix_left}　 {helix_right}\n{helix_left}　　{helix_right}\n"
                     "{helix_left}   　 {helix_right}\n {helix_left}　  {helix_right}\n　{helix_left}{helix_right}\n     {helix_right}{helix_left}\n  "
                     "{helix_right}    {helix_left}").format(
                helix_left=command_list[1], helix_right=command_list[2])
            output.append((helix, "text"))
        if command_list[0] == "persp":
            text = " ".join(command_list[1])
            analyze_request = {
                'comment'            : {'text': text},
                'requestedAttributes': {'TOXICITY': {}}
            }
            response = perspective_api.comments().analyze(body=analyze_request).execute()
            toxicity_score = (response["attributeScores"]["TOXICITY"]["summaryScore"]["value"] * 100)
            score_text = "```"

        if output:
            # noinspection PyTypeChecker
            for item in output:
                await send(destination=message_in.channel, text=item[0], send_type=item[1])


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

async def more_jpeg(url):
    response = requests.get(url)
    original_size = len(response.content)
    img = Image.open(BytesIO(response.content))
    img_path = os.path.join(os.path.dirname(__file__), "tmp\\tmp.jpeg")
    if os.path.isfile(img_path):
        os.remove(img_path)

    img.save(img_path, 'JPEG', quality=1)
    new_size = os.path.getsize(img_path)
    ratio = str(((new_size / original_size) * 100))[:6]
    config = {
        'album': None,
        'name' : 'Added JPEG!',
        'title': 'Added JPEG!'
    }
    ret = imgur_client.upload_from_path(img_path, config=config, anon=True)
    return ret["link"], ratio


async def send(destination, text, send_type):
    if isinstance(destination, str):
        destination = await client.get_channel(destination)

    if send_type == "rows":
        message_list = multi_block(text, True)
        for message in message_list:
            await client.send_message(destination, "```" + message + "```")
        return
    if send_type == "list":
        text = str(text)[1:-1]

    text = str(text)
    text = text.replace("\n", "<NL<")
    lines = textwrap.wrap(text, 2000, break_long_words=False)

    for line in lines:
        if len(line) > 2000:
            continue
        line = line.replace("<NL<", "\n")
        await client.send_message(destination, line)

async def remind_me(command_list, message):
    try:
        time = await utils_text.parse_time_to_end(" ".join(command_list[1:]))
        await asyncio.sleep(time["delt"].total_seconds())

        await client.send_message(message.channel, "Reminding after " + str(
            time) + " seconds:\n" + command_list[0])
    except:
        print(traceback.format_exc())

client.run(ZENITH_AUTH_TOKEN, bot=False)
