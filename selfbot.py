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

import PIL
import discord
import markovify
import motor.motor_asyncio
import requests
import urbandictionary
import logging

# import wand.image

from utils import utils_file, utils_text, utils_image, utils_parse, utils_persist
from PIL import Image
from googleapiclient import discovery
from imgurpython import ImgurClient
from unidecode import unidecode
# from utils_text import multi_block

import constants
from TOKENS import *
from utils import utils_file

logging.basicConfig(level=logging.INFO)

perspective_api = discovery.build('commentanalyzer', 'v1alpha1', developerKey=GOOGLE_API_TOKEN)

client = discord.Client()
imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
                           IMGUR_REFRESH_TOKEN)
overwatch_db = motor.motor_asyncio.AsyncIOMotorClient().overwatch

@client.event
async def on_message(message_in):
    #                                                                                           server-meta     server log   bot  log  voice channel
    if message_in.server and message_in.server.id == constants.OVERWATCH_SERVER_ID and message_in.channel.id not in ["264735004553248768", "152757147288076297",
                                                                                                                     "147153976687591424",
                                                                                                                     "200185170249252865"]:
        try:
            await mess2log(message_in)
        except AttributeError:
            pass
    if message_in.server.id == "266279338305912832" and message_in.author.id == "183083101436641280":
        print(int("#%06x" % random.randint(0, 0xFFFFFF), 16))
        await client.edit_role(message_in.server, await get_role(message_in.server, "307400427954110465"), color=discord.Color(int("#%06x" % random.randint(0, 0xFFFFFF), 16)))
    if message_in.author == client.user and message_in.content.startswith("%%"):

        command = message_in.content.replace("%%", "")
        command_list = command.split(" ")
        await client.delete_message(message_in)
        output = []

        if command_list[0] == "ava":
            ava = command_list[1] + ".png"
            print("Switching to " + ava)
            try:
                with open(utils_file.relative_path(__file__, "avatars/" + ava), "rb") as ava:
                    await client.edit_profile(password=PASS, avatar=ava.read())
            except:
                with open(utils_file.relative_path(__file__, "avatars/default.png"), "rb") as ava:
                    await client.edit_profile(password=PASS, avatar=ava.read())
        if command_list[0] == "dump_channel_overwrites":
            channel = await client.get_channel(command_list[1])
            # role = await get_role(message_in.server, command_list[2])
            overwrites = channel.overwrites
            result_dict = {}
            for tupleoverwrite in overwrites:
                # result_dict[t]
                result_dict[tupleoverwrite[0].name] = {}
                pair = tupleoverwrite[1].pair()
                for allow in pair[0]:
                    pass
        if command_list[0] == "getava":
            response = requests.get(command_list[1])
            img = Image.open(BytesIO(response.content))
            img_path = utils_file.relative_path(__file__, "avatars/" + command_list[2] + ".png")
            # if os.path.isfile(img_path):
            #     os.remove(img_path)
            img.save(img_path, 'PNG')
            with open(img_path, "rb") as ava:
                await client.edit_profile(password=PASS, avatar=ava.read())
        if command_list[0] == "stealava":
            command_list = await mention_to_id(command_list)
            target_user_id = command_list[1]
            url = message_in.server.get_member(target_user_id).avatar_url
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img_path = utils_file.relative_path(__file__, "avatars/" + target_user_id + ".png")
            # if os.path.isfile(img_path):
            #     os.remove(img_path)
            img.save(img_path, 'PNG')
            with open(img_path, "rb") as ava:
                await client.edit_profile(password=PASS, avatar=ava.read())
        if command_list[0] == "imp":
            command_list = await mention_to_id(command_list)
            target_user_id = command_list[1]
            target_member = message_in.server.get_member(target_user_id)
            response = requests.get(target_member.avatar_url)
            img = Image.open(BytesIO(response.content))
            img_path = utils_file.relative_path(__file__, "avatars/" + target_user_id + ".png")
            # if os.path.isfile(img_path):
            #     os.remove(img_path)
            img.save(img_path, 'PNG')
            with open(img_path, "rb") as ava:
                await client.edit_profile(password=PASS, avatar=ava.read())
            await client.change_nickname(message_in.server.me, target_member.nick if target_member.nick else target_member.name)

        if command_list[0] == "multinote":
            start = int(command_list[1])
            end = int(command_list[2])
            reason = " ".join(command_list[3:])

            for case_number in range(start, end):
                message = "<@!274119184953114625> update {number} {reason}, starting from {first}".format(number=case_number, reason=reason, first="715")
                await client.send_message(message_in.channel, message)
        if command_list[0] == "owner":
            output.append((message_in.server.owner.name, "text"))
        if command_list[0] == "ud":
            defs = str(urbandictionary.define(" ".join(command_list[1:]))[0])
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
            async for message_dict in overwatch_db.message_log.find({"userid": target_user_id}):
                utils_file.append_line(utils_file.relative_path(__file__, "markov/" + target_user_id + ".txt"), message_dict["content"])
        if command_list[0] == "markov":
            command_list = await mention_to_id(command_list)
            target_user_id = command_list[1]
            markovify.NewlineText(utils_file.relative_path(__file__, "markov/" + target_user_id + ".txt"))
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

async def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x


async def perspective(text):
    analyze_request = {
        'comment'            : {'text': text},
        'requestedAttributes': {'TOXICITY': {}},
        'languages'          : ["en"]
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
    toxicity_string = str(round(toxicity * 100, 1)).rjust(4, "0") + "%"

    log_str = unidecode(
        "[{toxicity}][{time}][{channel}][{name}] {content}".format(toxicity=toxicity_string, time=time,
                                                                   channel=channel, name=nick, content=message.content)).replace(
        "\n", r"[\n]")
    logfile_txt = r"logfile.txt"
    lines = utils_file.append_line(utils_file.relative_path(__file__, logfile_txt), log_str)
    if message.author.id in ["262652360008925184", "163008912348413953", "108962416582238208", "110182909993857024", "164564849915985922", "217276714244505600",
                             "111911466172424192", "195671081065906176", "258500747732189185", "218133578326867968", "133884121830129664"]:
        await client.send_message(client.get_channel("295260183352049664"), log_str)

async def more_jpeg(url):
    response = requests.get(url)
    original_size = len(response.content)
    img = Image.open(BytesIO(response.content))
    img_path = utils_file.relative_path(__file__, "tmp/tmp.jpeg")

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
        destination = client.get_channel(destination)

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

#
# def do_gmagik(self, ctx, gif):
# 	try:
# 		try:
# 			gif = PIL.Image.open(gif)
# 		except:
# 			return '\N{WARNING SIGN} Invalid Gif.'
# 		if gif.size >= (3000, 3000):
# 			return '\N{WARNING SIGN} `GIF resolution exceeds maximum >= (3000, 3000).`'
# 		elif gif.n_frames > 150 and ctx.message.author.id != self.bot.owner.id:
# 			return "\N{WARNING SIGN} `GIF has too many frames (> 150 Frames).`"
# 		count = 0
# 		frames = []
# 		while gif:
# 			b = BytesIO()
# 			try:
# 				gif.save(b, 'GIF')
# 			except:
# 				continue
# 			b.seek(0)
# 			frames.append(b)
# 			count += 1
# 			try:
# 				gif.seek(count)
# 			except EOFError:
# 				break
# 		imgs2 = []
# 		for image in frames:
# 			try:
# 				im = wand.image.Image(file=image)
# 			except:
# 				continue
# 			i = im.clone()
# 			i.transform(resize='800x800>')
# 			i.liquid_rescale(width=int(i.width*0.5), height=int(i.height*0.5), delta_x=1, rigidity=0)
# 			i.liquid_rescale(width=int(i.width*1.5), height=int(i.height*1.5), delta_x=2, rigidity=0)
# 			i.resize(i.width, i.height)
# 			b = BytesIO()
# 			i.save(file=b)
# 			b.seek(0)
# 			imgs2.append(b)
# 		imgs2 = [PIL.Image.open(i) for i in imgs2]
# 		final = BytesIO()
# 		i = imgs2[0].save(final, 'GIF', loop=0, save_all=True, append_images=imgs2)
# 		final.seek(0)
# 		return final
# 	except Exception as e:
# 		print(traceback.format_exc())
#
# async def do_gmagik2(self, url):
# 	path = self.files_path(self.bot.random(True))
# 	await self.download(url, path)
# 	args = ['convert', '(', path, '-resize', '256x256>', '-resize', '256x256<', ')']
# 	i = 5
# 	while i <= 70:
# 		args.extend(['(', '-clone', '0', '(', '+clone', '-liquid-rescale', '{0}%'.format(int(100-i)), ')', '(', '+clone', '-resize', '256', ')', '-delete', '-2', '-delete', '-2', ')'])
# 		i += 5
# 	args.extend(['-delay', '8', '-set', 'delay', '8', 'gif:-'])
# 	final = await self.bot.run_process(args, b=True)
# 	return path, final


# def do_gmagik(self, ctx, gif):
# 	try:
# 		try:
# 			gif = PIL.Image.open(gif)
# 		except:
# 			return '\N{WARNING SIGN} Invalid Gif.'
# 		if gif.size >= (3000, 3000):
# 			return '\N{WARNING SIGN} `GIF resolution exceeds maximum >= (3000, 3000).`'
# 		elif gif.n_frames > 150 and ctx.message.author.id != self.bot.owner.id:
# 			return "\N{WARNING SIGN} `GIF has too many frames (> 150 Frames).`"
# 		count = 0
# 		frames = []
# 		while gif:
# 			b = BytesIO()
# 			try:
# 				gif.save(b, 'GIF')
# 			except:
# 				continue
# 			b.seek(0)
# 			frames.append(b)
# 			count += 1
# 			try:
# 				gif.seek(count)
# 			except EOFError:
# 				break
# 		imgs2 = []
# 		for image in frames:
# 			try: wand.
# 				im = wand.image.Image(file=image)
# 			except:
# 				continue
# 			i = im.clone()
# 			i.transform(resize='800x800>')
# 			i.liquid_rescale(width=int(i.width*0.5), height=int(i.height*0.5), delta_x=1, rigidity=0)
# 			i.liquid_rescale(width=int(i.width*1.5), height=int(i.height*1.5), delta_x=2, rigidity=0)
# 			i.resize(i.width, i.height)
# 			b = BytesIO()
# 			i.save(file=b)
# 			b.seek(0)
# 			imgs2.append(b)
# 		imgs2 = [PIL.Image.open(i) for i in imgs2]
# 		final = BytesIO()
# 		i = imgs2[0].save(final, 'GIF', loop=0, save_all=True, append_images=imgs2)
# 		final.seek(0)
# 		return final
# 	except Exception as e:
# 		return f'{str(e)} {e.__traceback__.tb_lineno}'


# # Projects
# async def wolfram(message):
#     command = message.content.replace("..wa ", "")
#     res = WA_client.query(command)
#     try:
#         podlist = res["pod"]
#         print(ascii(res))
#     except:
#         print(ascii(res))
#         print("LOLFAIL")
#         return
#     numpods = int(res["@numpods"])
#     keydict = {}
#     options = ""
#     print("numpods = " + str(numpods))
#     print(res["@numpods"])
#     try:
#         for num in range(0, numpods - 1):
#             pod = podlist[num]
#             options += "[" + str(num) + "] " + pod["@title"] + "\n"
#             print("NUM = " + str(pod["@numsubpods"]))
#             for sub_num in range(0, int(pod["@numsubpods"])):
#                 subpod = pod["subpod"]
#                 if subpod["@title"] != "":
#                     options += "    [" + str(num) + "." + str(sub_num) + "] " + subpod["@title"] + "\n"
#             keydict[num] = pod
#         options = await client.send_message(message.channel, options)
#     except:
#         pass
#
#     def check(msg):
#         if message.server == msg.server and msg.author.id == message.author.id and message.channel == msg.channel:
#             if re.match(r"^\d*$", msg.content):
#                 return True
#         return False
#
#     response = await client.wait_for_message(timeout=15, check=check)
#     try:
#         response = int(response.content)
#         pod = podlist[response]
#         subpods = []
#         text = ""
#         if pod["@numsubpods"] == "1":
#             subpods.append(pod["subpod"])
#
#         else:
#             for x in pod["subpod"]:
#                 subpods.append(x)
#
#         for subpod in subpods:
#             img = (subpod["img"])["@src"]
#             # img = shorten_link(img)
#             text += img + "\n"
#         await client.send_message(message.channel, text)
#
#     except:
#         print(traceback.format_exc())
#     await client.delete_message(options)

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys

sys.stdout = Unbuffered(sys.stdout)

client.run(ZENITH_AUTH_TOKEN, bot=False)
