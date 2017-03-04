"""Provide an asynchronous equivalent *to exec*."""

# from . import compat
import asyncio
import os
import random
import re
import textwrap
import traceback
from datetime import datetime
from io import BytesIO

import discord
import markovify
import motor.motor_asyncio
import requests
import urbandictionary
from utils import utils_file, utils_text, utils_image, utils_parse, utils_persist
from PIL import Image
from googleapiclient import discovery
from imgurpython import ImgurClient
from unidecode import unidecode
# from utils_text import multi_block

import constants
from TOKENS import *
from utils import utils_file

# logging.basicConfig(level=logging.INFO)

perspective_api = discovery.build('commentanalyzer', 'v1alpha1', developerKey=GOOGLE_API_TOKEN)

client = discord.Client()
imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
                           IMGUR_REFRESH_TOKEN)
overwatch_db = motor.motor_asyncio.AsyncIOMotorClient().overwatch

@client.event
async def on_message(message_in):
    #                                                                                           server-meta     server log   bot  log  voice channel
    if message_in.server and message_in.server.id == constants.OVERWATCH_SERVER_ID and message_in.channel.id not in ["264735004553248768", "152757147288076297", "147153976687591424",
                                                                                               "200185170249252865"]:
        try:
            await mess2log(message_in)
        except AttributeError:
            pass
    if message_in.author == client.user and message_in.content.startswith("%%"):
        command = message_in.content.replace("%%", "")
        command_list = command.split(" ")
        await client.delete_message(message_in)
        output = []
        if command_list[0] == "pfp":
            pfp = command_list[1] + ".png"
            print("Switching to " + pfp)
            try:
                with open(utils_file.relative_path("avatars\\" + pfp), "rb") as pfp:
                    await client.edit_profile(password=PASS, avatar=pfp.read())
            except:
                with open(utils_file.relative_path("avatars\\default.png"), "rb") as pfp:
                    await client.edit_profile(password=PASS, avatar=pfp.read())
        if command_list[0] == "owner":
            output.append((message_in.server.owner.name, "text"))
        if command_list[0] == "ud":
            defs = urbandictionary.define(" ".join(command_list[1:]))
            output.append((defs, "text"))
        if command_list[0] == "servers":
            server_list = [[server.name, str(server.member_count)] for server in client.servers]
            output.append((server_list, "rows"))
        if command_list[0] == "mercyshuffle":
            link_list = [x.link for x in imgur_client.get_album_images("umuvY")]
            random.shuffle(link_list)
            for link in link_list[:int(command_list[1])]:
                await client.send_message(message_in.channel, link)
        if command_list[0] == "markdump":
            command_list = await mention_to_id(command_list)
            target_user_id = command_list[1]
            async for message_dict in overwatch_db.message_log.find({"userid":target_user_id}):
                utils_file.append_line(utils_file.relative_path("markov\\" + target_user_id + ".txt"), message_dict["content"])
        if command_list[0] == "markov":
            command_list = await mention_to_id(command_list)
            target_user_id = command_list[1]
            markovify.NewlineText(utils_file.relative_path("markov\\" + target_user_id + ".txt"))
        if command_list[0] == "emoji":
            import re
            emoji_id = utils_text.regex_test("\d+(?=>)", " ".join(command_list[1:])).group(0)
            print(emoji_id)
            server_name = None
            for emoji in client.get_all_emojis():
                if emoji_id == emoji.id:
                    server_name = emoji.server.name
                    break
            output.append((server_name, None))
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
            text = " ".join(command_list[1:])
            toxicity_score = await perspective(text)
            score_text = "```{text}``` Toxicity Score: {score}%".format(text=text, score=toxicity_score * 100)
            output.append((score_text, "text"))

        if command_list[0] == "big":
            text = str(" ".join(command_list[1:]))
            big_text = ""
            for character in text:
                if character == " ":
                    big_text += "     "
                else:
                    big_text += " :regional_indicator_{c}:".format(c=character)
            output.append((big_text, None))
        if output:
            # noinspection PyTypeChecker
            for item in output:
                await send(destination=message_in.channel, text=item[0], send_type=item[1])


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

async def perspective(text):
    analyze_request = {
        'comment'            : {'text': text},
        'requestedAttributes': {'TOXICITY': {}}
    }
    response = perspective_api.comments().analyze(body=analyze_request).execute()
    return response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]

async def mess2log(message):
    time = datetime.now().strftime("%I:%M:%S")
    channel = message.channel.name if message.channel.id != "170185225526181890" else "trusted-chat"
    nick = message.author.nick if message.author.nick else message.author.name
    text = message.content
    if len(text) < 2:
        return
    toxicity = await perspective(text)
    if message.author.id == "248841864831041547":
        toxicity = 0.0
    toxicity_string = str(round(toxicity*100, 1)).rjust(4, "0") + "%"



    log_str = unidecode(
        "[{toxicity}][{time}][{channel}][{name}] {content}{trg}".format(trg="" if toxicity < 0.6 else "|| [TRG-]", toxicity=toxicity_string, time=time,
                                                                        channel=channel, name=nick, content=message.content)).replace(
        "\n", r"[\n]")
    logfile_txt = r"C:\Users\Austin\Desktop\Programming\Disc\logfile.txt"
    lines = utils_file.append_line(logfile_txt, log_str)

async def more_jpeg(url):
    response = requests.get(url)
    original_size = len(response.content)
    img = Image.open(BytesIO(response.content))
    img_path = utils_file.relative_path("tmp\\tmp.jpeg")
    # img_path = os.path.join(os.path.dirname(__file__), "tmp\\tmp.jpeg")
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
        message_list = utils_text.multi_block(text, True)
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

async def mention_to_id(command_list):
    new_command = []
    reg = re.compile(r"<[@#](!?)\d*>", re.IGNORECASE)
    for item in command_list:
        match = reg.search(item)
        if match is None:
            new_command.append(item)
        else:
            idmatch = re.compile(r"\d")
            id_chars = "".join(idmatch.findall(item))
            new_command.append(id_chars)
    return new_command

client.run(ZENITH_AUTH_TOKEN, bot=False)
