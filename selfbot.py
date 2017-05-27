"""Provide an asynchronous equivalent *to exec*."""

# from . import compat
import asyncio
import hashlib
import os
import random
import re
import textwrap
import traceback
from datetime import datetime
from io import BytesIO
import heapq
import PIL
import discord
import markovify
import motor.motor_asyncio
import pymongo
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
import collections
import constants
from TOKENS import *
import TOKENS
from utils import utils_file
from fuzzywuzzy import fuzz
from simplegist.simplegist import Simplegist

logging.basicConfig(level=logging.ERROR)
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://{usn}:{pwd}@nadir.space".format(
        usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS))
gistClient = Simplegist()

perspective_api = discovery.build('commentanalyzer', 'v1alpha1', developerKey=GOOGLE_API_TOKEN)

client = discord.Client()
imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
                           IMGUR_REFRESH_TOKEN)
overwatch_db = mongo_client.overwatch

botClient = discord.Client()


@client.event
async def on_message(message_in):
    try:
        # if message_in.server.id == constants.OVERWATCH_SERVER_ID:
        #     await import_message(message_in)
        # server-meta     server log   bot  log  voice channel
        if message_in.server and message_in.server.id == constants.OVERWATCH_SERVER_ID and message_in.channel.id not in ["264735004553248768", "152757147288076297",
                                                                                                                         "147153976687591424",
                                                                                                                         "200185170249252865"]:
            try:
                await mess2log(message_in)
            except AttributeError:
                pass

        if message_in.author == client.user and message_in.content.startswith("%%"):

            command = message_in.content.replace("%%", "")
            command_list = command.split(" ")
            await client.delete_message(message_in)
            command_list = await mention_to_id(command_list)
            output = []

            if command_list[0] == "userlogs":
                output.append(await output_logs(
                    userid=command_list[1], count=command_list[2], message_in=message_in))
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
            if command_list[0] == "dumpinfo":
                target = await export_user(command_list[1])
                rows = [(k, str(v)) for k, v in target.items()]
                print(rows)
                output.append((rows, "rows"))
            if command_list[0] == "lfg":
                await serve_lfg(message_in)
            if command_list[0] == "ui":
                embed = await output_user_embed(command_list[1], message_in)
                if embed:
                    await client.send_message(
                        destination=message_in.channel,
                        content=None,
                        embed=embed)
                else:
                    await client.send_message(
                        destination=message_in.channel,
                        content="User not found")
            if command_list[0] == "backfill":
                more = True
                while more == True:
                    print("Starting up...")
                    cursor = overwatch_db.message_log.find({"toxicity":{"$exists":False}}).sort("date",pymongo.DESCENDING)
                    if cursor:
                        count = 0
                        operations = []
                        async for messInfo in cursor:
                            if count > 500:
                                res = await overwatch_db.message_log.bulk_write(operations)
                                print(res.modified_count)
                                count = 0
                                operations = []
                            print(count)
                            if not messInfo["content"] or len(messInfo["content"]) < 10:
                                print("Skipping")
                                continue
                            toxicity = await perspective(messInfo["content"])
                            print(messInfo["date"])
                            operations.append(pymongo.operations.UpdateOne({"message_id": messInfo["message_id"]}, {"$set": {"toxicity": toxicity}}))
                            # await overwatch_db.message_log.update_one({"message_id":messInfo["message_id"]}, {"$set":{"toxicity":toxicity}})
                            print(".")
                            await overwatch_db.userinfo.update_one({"userid": messInfo["userid"]}, {"$inc": {"toxicity": toxicity, "toxicity_count": 1}})
                            print("..")
                            await asyncio.sleep(0.1)
                            count = count + 1

                    else:
                        more = False
                        print("Ending...")
            if command_list[0] == "transfer":
                seen_ids = []
                async for message in overwatch_db.message_log.find():
                    overwatch_db.message_log_new.insert_one(message)

                # cursor = overwatch_db.message_log.aggregate(
                #     [
                #         {"$group": {"_id": "$message_id", "unique_ids": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
                #         {"$match": {"count": {"$gte": 2}}}
                #     ]
                # , allowDiskUse = True )
                # response = []
                # count = 0
                # async for doc in cursor:
                #
                #     print(count)
                #     count = count + 1
                #     del doc["unique_ids"][0]
                #     for id in doc["unique_ids"]:
                #         response.append(id)
                # await overwatch_db.message_log.remove({"_id": {"$in": response}})

            if command_list[0] == "find":
                # await output_find_user(message_in)
                raw_params = " ".join(command_list[1:])
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="current",
                        server=message_in.server,
                        count=int(params[1])))
                else:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="current",
                        server=message_in.server))
            if command_list[0] == "findow":
                # await output_find_user(message_in)
                raw_params = " ".join(command_list[1:])
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="current",
                        server=client.get_server("94882524378968064"),
                        count=int(params[1])))
                else:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="current",
                        server=client.get_server("94882524378968064")))
            if command_list[0] == "findall":
                # await output_find_user(message_in)
                raw_params = " ".join(command_list[1:])
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="history",
                        server=message_in.server,
                        count=int(params[1])))
                else:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="history",
                        server=message_in.server))

            if command_list[0] == "findban":
                raw_params = " ".join(command_list[1:])
                params = raw_params.split("|")
                if len(params) > 1:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="bans",
                        server=message_in.server,
                        count=int(params[1])))
                else:
                    output.append(await find_user(
                        matching_ident=params[0],
                        find_type="bans",
                        server=message_in.server))
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
    except:
        print(traceback.format_exc())

async def import_message(mess, toxicity):
    messInfo = await utils_parse.parse_message_info(mess)
    messInfo["toxicity"] = toxicity
    try:
        await overwatch_db.message_log.insert_one(messInfo)
        await overwatch_db.userinfo.update_one({"userid":messInfo["userid"]}, {"$inc":{"toxicity":toxicity, "toxicity_count":1}})
    except:
        pass

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

async def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x

# Log Based
async def output_logs(userid, count, message_in):
    cursor = overwatch_db.message_log.find(
        {
            "userid": userid
        }, limit=int(count))
    cursor.sort("date", -1)
    message_list = []
    count = 0
    async for message_dict in cursor:
        if count % 500 == 0:
            print(count)
        count += 1
        message_list.append(await format_message_to_log(message_dict))
    if count == 0:
        return ("No logs found", None)

    if message_list:
        gist = gistClient.create(
            name="User Log",
            description=userid + "'s Logs",
            public=False,
            content="\n".join(message_list))
        return (gist["Gist-Link"], None)
    else:
        return ("No logs found", None)

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
    await import_message(message, toxicity)

    log_str = unidecode(
        "[{toxicity}][{time}][{channel}][{name}] {content}".format(toxicity=toxicity_string, time=time,
                                                                   channel=channel, name=nick, content=message.content)).replace(
        "\n", r"[\n]")
    logfile_txt = r"logfile.txt"
    lines = utils_file.append_line(utils_file.relative_path(__file__, logfile_txt), log_str)
    # if message.author.id in ["262652360008925184", "163008912348413953", "108962416582238208", "110182909993857024", "164564849915985922", "217276714244505600",
    #                          "111911466172424192", "195671081065906176", "258500747732189185", "218133578326867968", "133884121830129664"]:
    #     await client.send_message(client.get_channel("295260183352049664"), log_str)

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
            try:
                await client.send_message(destination, "```" + message + "```")
            except:
                print(message)
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

async def find_user(matching_ident,
                    find_type,
                    server,
                    cast_to_lower=True,
                    count=1):
    ident_id_set_dict = collections.defaultdict(set)
    if find_type == "bans":
        banlist = await client.get_bans(server)
        for banned_user in banlist:
            # print(banned_user.name)
            ident_id_set_dict[banned_user.name].add(banned_user.id)
            ident_id_set_dict[banned_user.name +
                              banned_user.discriminator].add(banned_user.id)
    elif find_type == "current":
        for member in server.members:
            ident_id_set_dict[member.name].add(member.id)
            ident_id_set_dict[member.name +
                              member.discriminator].add(member.id)
            if member.nick and member.nick is not member.name:
                ident_id_set_dict[member.name].add(member.id)

    elif find_type == "history":
        mongo_cursor = overwatch_db.userinfo.find()
        async for userinfo_dict in mongo_cursor:
            try:
                for nick in userinfo_dict["nicks"]:
                    if nick:
                        ident_id_set_dict[nick].add(userinfo_dict["userid"])
                for name in userinfo_dict["names"]:
                    if name:
                        ident_id_set_dict[name].add(userinfo_dict["userid"])
            except:
                print(traceback.format_exc())

    if cast_to_lower:
        matching_ident = matching_ident.lower()
        # ID_ROLENAME_DICT = dict([[v, k] for k, v in constants.ROLENAME_ID_DICT.items()])
        new_dict = dict([(ident.lower(), id_set)
                         for ident, id_set in ident_id_set_dict.items()])
        ident_id_set_dict = new_dict

    # for nick in nick_id_dict.keys():
    #     ratio = fuzz.ratio(nick_to_find.lower(), str(nick).lower())
    #     nick_fuzz[str(nick)] = int(ratio)
    ident_ratio = {}
    for ident in ident_id_set_dict.keys():
        ratio = fuzz.ratio(matching_ident, ident)
        ident_ratio[ident] = ratio

    top_idents = heapq.nlargest(
        int(count), ident_ratio, key=lambda k: ident_ratio[k])
    output = "Fuzzy Searching {} with the input {}, {} ignoring case\n".format(
        find_type, matching_ident, "" if cast_to_lower else "not")
    for ident in top_idents:
        id_set = ident_id_set_dict[ident]
        for userid in id_set:
            output += "`ID: {userid} | Name: {name} |` {mention}\n".format(
                userid=userid, name=ident, mention="<@!{}>".format(userid))
    return (output, None)

async def output_user_embed(member_id, message_in):
    # target_member = message_in.author
    target_member = message_in.server.get_member(member_id)
    if not target_member:
        target_member = await client.get_user_info(member_id)
    if not target_member:
        target_member = message_in.author

    user_dict = await export_user(target_member.id)

    embed = discord.Embed(
        title="{name}#{discrim}'s userinfo".format(
            name=target_member.name, discrim=str(target_member.discriminator)),
        type="rich")

    # avatar_link = shorten_link(target_member.avatar_url)

    avatar_link = target_member.avatar_url

    # color = "0x" + color

    embed.add_field(name="ID", value=target_member.id, inline=True)
    if user_dict:
        if "server_joins" in user_dict.keys():
            server_joins = user_dict["server_joins"]
            server_joins = [join[:10] for join in server_joins]

            embed.add_field(
                name="First Join", value=server_joins[0], inline=True)
        if "bans" in user_dict.keys():
            bans = user_dict["bans"]
            bans = [ban[:10] for ban in bans]
            bans = str(bans)[1:-1]
            embed.add_field(name="Bans", value=bans, inline=True)
        if "unbans" in user_dict.keys():
            unbans = user_dict["unbans"]
            unbans = [unban[:10] for unban in unbans]
            unbans = str(unbans)[1:-1]
            embed.add_field(name="Unbans", value=unbans, inline=True)
    embed.add_field(
        name="Creation",
        value=target_member.created_at.strftime("%B %d, %Y"),
        inline=True)

    if isinstance(target_member, discord.Member):
        roles = [role.name for role in target_member.roles][1:]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles), inline=True)
        voice = target_member.voice
        if voice.voice_channel:
            voice_name = voice.voice_channel.name
            embed.add_field(name="Current VC", value=voice_name)
        status = str(target_member.status)
    else:
        if target_member in await client.get_bans(message_in.server):
            status = "Banned"
        else:
            status = "Not part of the server"
    embed.add_field(name="Status", value=status, inline=False)
    if avatar_link:
        embed.set_thumbnail(url=avatar_link)
        color = utils_image.average_color_url(avatar_link)
        embed.add_field(
            name="Avatar",
            value=avatar_link.replace(".webp", ".png"),
            inline=False)
        hex_int = int(color, 16)
        embed.colour = discord.Colour(hex_int)
        embed.set_thumbnail(url=target_member.avatar_url)
    return embed

async def export_user(member_id):
    """

    :type member: discord.Member
    """
    userinfo = await overwatch_db.userinfo.find_one(
        {
            "userid": member_id
        },
        projection={
            "_id"        : False,
            "mention_str": False,
            "avatar_urls": False,
            "lfg_count"  : False
        })
    if not userinfo:
        return None
    return userinfo

async def import_user(member):
    user_info = await utils_parse.parse_member_info(member)
    result = await overwatch_db.userinfo.update_one(
        {
            "userid": member.id
        }, {
            "$addToSet": {
                "nicks"       : {
                    "$each": [
                        user_info["nick"], user_info["name"],
                        user_info["name"] + "#" + str(user_info["discrim"])
                    ]
                },
                "names"       : user_info["name"],
                "avatar_urls" : user_info["avatar_url"],
                "server_joins": user_info["joined_at"]
            },
            "$set"     : {
                "mention_str": user_info["mention_str"],
                "created_at" : user_info["created_at"]
            },
        },
        upsert=True)
    pass

async def format_message_to_log(message_dict):
    cursor = await overwatch_db.userinfo.find_one({
        "userid":
            message_dict["userid"]
    })
    try:
        name = cursor["names"][-1]
        if not name:
            name = cursor["names"][-2]
    except:
        try:
            await import_user(client.get_server("94882524378968064").get_member(message_dict["userid"]))
            cursor = await overwatch_db.userinfo.find_one({
                "userid":
                    message_dict["userid"]
            })
            name = cursor["names"][-1]
        except:
            name = message_dict["userid"]
        if not name:
            name = message_dict["userid"]

    try:
        content = message_dict["content"].replace("```", "")
        try:
            channel_name = constants.CHANNELID_CHANNELNAME_DICT[str(
                message_dict["channel_id"])]
        except KeyError:
            channel_name = "Unknown"

        return "[" + message_dict["date"][:
        19] + "][" + channel_name + "][" + str(
            name) + "]:" + content

    except:
        print(traceback.format_exc())
        return "Errored Message : " + str(message_dict)

async def serve_lfg(message_in):
    found_message = None
    warn_user = None
    if len(message_in.mentions) == 0:
        found_message = await finder(
            message=message_in, regex=constants.LFG_REGEX, blacklist="mod")
    else:
        warn_user = message_in.mentions[0]
    # await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
    #                           "`lfg called by " + message_in.author.name)
    await lfg_warner(
        found_message=found_message,
        warn_user=warn_user,
        channel=message_in.channel)
    await client.delete_message(message_in)

async def finder(message, regex, blacklist):
    """

    :type exclude: str
    :type message: discord.Message
    :type reg: retype
    """
    auth = False
    match = None
    found_message = None
    async for messageCheck in client.logs_from(message.channel, 20):
        if messageCheck.author.id != message.author.id and messageCheck.author.id != constants.MERCY_ID:
            if blacklist == "none":
                auth = False
            elif blacklist == "mod":
                auth = "mod" in await get_auths(messageCheck.author)
                # auth = await w    tial(messageCheck.author, "mod")
            else:
                auth = False
            if not auth:
                if isinstance(regex, str):
                    if messageCheck.content == regex:
                        match = messageCheck
                else:
                    match = regex.search(messageCheck.content)
                if match is not None:
                    found_message = messageCheck
                    return found_message
    return found_message


async def get_moderators(server):
    users = []
    for role in server.roles:
        if role.permissions.manage_roles or role.permissions.ban_members:
            members = await get_role_members(role)
            users.extend(members)
    return users

async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members

async def get_auths(member):
    """
    :type member: discord.Member
    """
    author_info = await utils_parse.parse_member_info(member)
    role_whitelist = any(x in [
        constants.ROLENAME_ID_DICT["TRUSTED_ROLE"],
        constants.ROLENAME_ID_DICT["MVP_ROLE"]
    ] for x in author_info["role_ids"])

    mods = await get_moderators(member.server)
    auths = set()
    if member.id == constants.ZENITH_ID:
        auths |= {"zenith"}
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"mod"}
    if member in mods:
        auths |= {"mod"}
        auths |= {"warn"}
        auths |= {"trusted"}
    if role_whitelist:
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"lfg"}
    if any(x in "138132942542077952" for x in author_info["role_ids"]):
        auths |= {"mod"}

    if member.server.id == "236343416177295360":
        if "261550254418034688" in [role.id for role in member.roles]:
            auths |= {"host"}
    return auths


async def lfg_warner(found_message, warn_user, channel):
    lfg_text = (
        "You're probably looking for <#306512316843950091>, <#182420486582435840>, <#185665683009306625>, or <#177136656846028801>."
        " Please avoid posting LFGs in ")
    if found_message:
        author = found_message.author
        channel = found_message.channel
    else:
        author = warn_user
        channel = channel
    lfg_text += channel.mention
    if author:
        lfg_text += ", " + author.mention

    await client.send_message(channel, lfg_text)

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
