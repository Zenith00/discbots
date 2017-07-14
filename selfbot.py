# from . import compat
import asyncio
import copy
import heapq
import logging
import os
import random
import re
import textwrap
import traceback
from datetime import datetime
from io import BytesIO
import git
import dateparser
import discord
import motor.motor_asyncio
import pymongo
import requests
import pip
from imgurpython import ImgurClient
from unidecode import unidecode
from utils import utils_text, utils_image, utils_parse
from PIL import Image
import collections
from TOKENS import *
import TOKENS
from utils import utils_file
from fuzzywuzzy import fuzz
from collections import defaultdict
import tqdm
from config import *
from utils.utils_text import dict2rows

# logging.basicConfig(level=logging.INFO)

if config["remote_mongo"]:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
        "mongodb://{usn}:{pwd}@{site}".format(
            usn=TOKENS.MONGO_USN,
            pwd=TOKENS.MONGO_PASS,
            site=TOKENS.MONGO_SITE))
else:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient('localhost', 27017)

# gistClient = Simplegist()

client = discord.Client()

if config["perspective"]:
    from googleapiclient import discovery

    perspective_api = discovery.build(
        'commentanalyzer', 'v1alpha1', developerKey=GOOGLE_API_TOKEN)
    print("asdf")

if config["imgur"]:
    imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID,
                               IMGUR_ACCESS_TOKEN, IMGUR_REFRESH_TOKEN)

# test

@client.event
async def on_member_remove(member):
    await import_to_server_user_set(
        member=member,
        server=member.server.id,
        set_name="server_leaves",
        entry=datetime.utcnow().isoformat(" "))

@client.event
async def on_member_ban(member):
    await import_to_server_user_set(
        member=member,
        server=member.server.id,
        set_name="bans",
        entry=datetime.utcnow().isoformat(" "))

@client.event
async def on_member_unban(server, member):
    await import_to_server_user_set(
        member=member,
        server=member.server.id,
        set_name="unbans",
        entry=datetime.utcnow().isoformat(" "))

@client.event
async def on_voice_state_update(before, after):
    """
    :type after: discord.Member
    :type before: discord.Member
    """
    pass

@client.event
async def on_member_join(member):
    await asyncio.sleep(5)
    await import_user(member)

@client.event
async def on_member_update(before, after):
    """

    :type after: discord.Member
    :type before: discord.Member
    """

    if before.nick != after.nick:
        await import_to_user_set(
            member=after, set_name="nicks", entry=after.nick)
    if before.name != after.name:
        await import_to_user_set(
            member=after, set_name="names", entry=after.nick)
    if before.voice == after.voice:
        await import_user(after)

# Startup


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

async def run_startup():
    await client.wait_until_ready()
    await asyncio.sleep(10)
    if "334043962094387201" not in [server.id for server in client.servers]:
        # Joins RELAY server to allow for relay-based output
        await client.accept_invite("sDCHMrX")

    await ensure_database_struct()
    print("Finished setting up database")
    await asyncio.sleep(3)
    await update_members()
    print("Finished importing members")
    await asyncio.sleep(3)
    await update_messages()
    print("Finished importing messages")

async def ensure_database_struct():
    if "message_log" not in await mongo_client.discord.collection_names():
        await mongo_client.discord.create_collection("message_log")
    if "tags" not in await mongo_client.discord.collection_names():
        await mongo_client.discord.create_collection("tags")

    messages = mongo_client.discord.message_log
    message_index_info = await messages.index_information()
    missing_indexes = list({
                               "_id_", "message_id_1", "toxicity_1", "server_id_1", "channel_id_1",
                               "user_id_1", "date_1"
                           } - set(message_index_info.keys()))
    for full_index_name in missing_indexes:
        if "message_id" in full_index_name:
            mongo_client.discord.message_log.create_index(
                full_index_name[:-2], unique=True)
        else:
            mongo_client.discord.message_log.create_index(
                full_index_name[:-2], background=True)

    if "user_id_1" not in (await mongo_client.discord.userinfo.index_information()).keys():
        duplicates = []
        try:
            await mongo_client.discord.userinfo.create_index("user_id", unique=True)
        except:
            try:
                print("Running.….")
                cursor = mongo_client.discord.userinfo.aggregate(
                    [
                        {"$group": {"_id": "user_id", "unique_ids": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
                        {"$match": {"count": {"$gte": 2}}}
                    ]
                )

                response = []
                async for doc in cursor:
                    print("Running...")
                    del doc["unique_ids"][0]
                    for id in doc["unique_ids"]:
                        response.append(id)

                await mongo_client.discord.userinfo.delete_many({"_id": {"$in": response}})
            except:
                await trace(traceback.format_exc())
                print(traceback.format_exc())

        pass
    if "tag_1" not in (await mongo_client.discord.tags.index_information()).keys():
        try:
            await mongo_client.discord.tags.create_index("tag", unique=True)
        except:
            await trace(traceback.format_exc())

    # await mongo_client.discord.userinfo.update_many({}, {"$pull": {"server_joins": None, "server_leaves": None, "bans": None, "unbans": None}})

async def update_members():
    for server in client.servers:
        print("Startup: Importing members from " + server.name)
        memberlist = []
        for member in server.members:
            memberlist.append(member)
        for member in tqdm.tqdm(memberlist):
            await import_user(member)

async def update_messages():
    newest = await mongo_client.discord.message_log.find_one(
        sort=[("date", pymongo.DESCENDING)], skip=50)
    datetime = dateparser.parse(newest["date"])
    for server in client.servers:
        for channel in server.channels:
            async for message in client.logs_from(
                    channel, after=datetime, limit=1000000):
                await import_message(message)

# Frontend

@client.event
async def on_message(message_in):
    await mess2log(message_in)
    try:
        if message_in.author.id == client.user.id:
            base_list = message_in.content.split(" ")
            expanded_list = []
            for word in base_list:
                if word.startswith(config["prefix"]["tag"]):
                    res = await mongo_client.discord.tags.find_one({"tag":word[2:]})
                    if res:
                        expanded_list.append(res["expansion"])
                    else:
                        await relay("Ignored unset tag call `{}`".format(word))
                else:
                    expanded_list.append(word)
            if set(expanded_list) != set(base_list):
                await client.edit_message(message_in, " ".join(expanded_list))
                message_in.content = " ".join(expanded_list)

            if message_in.content.startswith(config["prefix"]["command"]):
                full_command = message_in.content.replace(
                    config["prefix"]["command"], "")
                segmented_command = full_command.split(" ")
                command = segmented_command[0]
                params = [
                    segmented_command[1]
                ] if len(segmented_command) == 2 else segmented_command[1:]
                await perform_command(
                    command=command, params=params, message_in=message_in)
            if config["autoupdate"] and message_in.channel.id == "334524545077870592" and message_in.author.id == "193000443981463552":
                try:
                    for word in message_in.content:
                        if word.startswith("package!!"):
                            package = word.replace("package!!", "")
                            pip.main(["install", package])
                    g = git.cmd.Git(utils_file.directory_path(__file__))
                    res = g.pull()
                except:
                    await trace(traceback.format_exc())





    except:
        await trace("{}".format(traceback.format_exc()))

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

async def perform_command(command, params, message_in):
    params = await mention_to_id(params)
    try:
        await client.delete_message(message_in)
    except discord.errors.NotFound:
        pass
    output = []
    print("BASE PARAMS: " + str(params))
    if command == "tag":
        await command_tag(params, message_in)
    if command == "query":
        output.extend(await command_query(params, message_in))
    if command == "find":
        output.extend((config["find"]["current"]["output"], await find_user(
            matching_ident=params[:-2] if "|" in params else params,
            find_type="current",
            server=message_in.server,
            count=params[-1] if "|" in params else 1), None))
    if command == "findall":
        output.append((config["find"]["history"]["output"], await find_user(
            matching_ident=params[:-2] if "|" in params else params,
            find_type="history",
            server=message_in.server,
            count=params[-1] if "|" in params else 1), None))
    if command == "findban":
        output.append((config["find"]["bans"]["output"], await find_user(
            matching_ident=params[:-2] if "|" in params else params,
            find_type="bans",
            server=message_in.server,
            count=params[-1] if "|" in params else 1), None))

    if command == "big":
        text = " ".join(params).lower()
        big_text = ""
        for character in text:
            if character == " ":
                big_text += "   "
            else:
                big_text += "​:regional_indicator_{c}:".format(c=character)
        output.extend(("inplace", big_text, "text"))
    if command == "ava":
        await command_avatar(params, message_in)


    # Requires IMGUR
    if command == "jpeg":
        url = params[0]
        url = await more_jpeg(url)
        output.extend(("{url}. Compressed to {ratio}% of original".format(
            url=url[0], ratio=url[1]), "text"))
    # Requires IMGUR
    # Posts X images from a given imgur album's ID: http://imgur.com/a/ID
    # %%imgurshuffle X umuvY
    if command == "imgurshuffle":
        album_id = params[1]
        if album_id == "ow":
            album_id = "umuvY"
        link_list = [x.link for x in imgur_client.get_album_images(album_id)]
        random.shuffle(link_list)
        for link in link_list[:int(params[0])]:
            await client.send_message(message_in.channel, link)

    if command == "logs":
        output.extend(await command_logs(params, {
            "server" : message_in.server,
            "channel": message_in.channel,
            "user"   : message_in.author
        }))

    if command == "remindme":
        member = message_in.author
        raw = " ".join(params)

        time_dict = await utils_text.parse_time_to_end(raw.split(",")[-1])
        await asyncio.sleep(time_dict["duration"].total_seconds())

        await relay("Reminding you after {}: `{}`".format(
            time_dict["readable"], raw.split(",")[0]))
    if output:
        for item in output:
            print(item)
            await parse_output(item, message_in.channel)

async def parse_output(output, context):
    if output[0] == "inplace":
        await send(destination=context, text=output[1], send_type=output[2])
    elif output[0] == "relay":
        await send(
            #                               Relay
            destination=client.get_channel("334043962094387201"),
            text=output[1],
            send_type=output[2])

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
    if send_type == "qrows":
        message_list = utils_text.multi_block(text, True)
        for message in message_list:
            try:
                await client.send_message(destination, message)
            except:
                print(message)
        return
    if send_type == "embed":
        await client.send_message(
            destination=destination, content=None, embed=text)
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

# Commands
async def command_logs(params, context):
    try:
        print(params)
        query = await log_query_parser(params[1:], context)
        if isinstance(query, str):
            print("Failing...")
            return [("relay", query, None)]
        filter = {}
        translate = {
            "users"   : "user_id",
            "channels": "channel_id",
            "servers" : "server_id"
        }
        for key in query.keys():
            filter[translate[key]] = {"$in": query[key]}
        output_text = ""
        print(filter)
        async for doc in mongo_client.discord.message_log.find(
                filter=filter,
                sort=[("date", pymongo.DESCENDING)],
                limit=int(params[0])):
            output_text += await format_message_to_log(doc) + "\n"

        return [(config["logs"]["output"], "\n".join(
            utils_text.hastebin(output_text)), None)]
    except:
        return [("relay", traceback.format_exc(), None)]

async def log_query_parser(query, context):
    try:
        query_state = {"users": [], "channels": [], "servers": []}
        target = ""
        for word in query:
            if word in ["user", "channel", "server"]:
                word += "s"
            if word in query_state.keys():
                target = word
                continue
            if word in ["here", "local"]:
                word = context[target[:-1]].id
            query_state[target].append(word)
        for key in ["users", "channels", "servers"]:
            if len(query_state[key]) == 0:
                del query_state[key]
        return query_state
    except:
        print(traceback.format_exc())
        return "Syntax not recognized. Proper syntax: %%logs 500 user 1111 2222 channel 3333 4444 5555 server 6666. \n Debug: ```py\n{}```".format(
            traceback.format_exc())

async def command_query(params, message_in):
    try:
        if params[0] == "user":
            if params[1] == "embed":
                target_member = message_in.server.get_member(params[2])
                user_dict = await export_user(target_member.id)

                embed = discord.Embed(
                    title="{name}#{discrim}'s userinfo".format(
                        name=target_member.name,
                        discrim=str(target_member.discriminator)),
                    type="rich")
                avatar_link = target_member.avatar_url
                embed.add_field(name="ID", value=target_member.id, inline=True)
                if user_dict:
                    if "server_joins" in user_dict.keys(
                    ) and message_in.server.id in user_dict["server_joins"].keys():
                        server_joins = user_dict["server_joins"][
                            message_in.server.id]
                        server_joins = [join[:10] for join in server_joins]
                        embed.add_field(
                            name="First Join", value=server_joins[0], inline=True)
                    if "bans" in user_dict.keys(
                    ) and message_in.server.id in user_dict["bans"].keys():
                        bans = user_dict["bans"][message_in.server.id]
                        bans = [ban[:10] for ban in bans]
                        bans = str(bans)[1:-1]
                        embed.add_field(name="Bans", value=bans, inline=True)
                    if "unbans" in user_dict.keys(
                    ) and message_in.server.id in user_dict["unbans"].keys():
                        unbans = user_dict["unbans"][message_in.server.id]
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
                        embed.add_field(
                            name="Roles", value=", ".join(roles), inline=True)
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
                embed.add_field(name="Status", value=status, inline=True)
                if avatar_link:
                    embed.set_thumbnail(url=avatar_link)
                    embed.set_footer(text=avatar_link.replace(".webp", ".png"))

                    if config["query"]["user"]["embed"]["color_average_bar"]:
                        color = utils_image.average_color_url(avatar_link)
                        hex_int = int(color, 16)
                        embed.colour = discord.Colour(hex_int)
                    embed.set_thumbnail(url=target_member.avatar_url)
                return [(config["query"]["user"]["embed"]["output"], embed, "embed")]

            if params[1] == "dump":
                print("dumping")
                user_dict = await export_user(params[2])
                user_dict = utils_text.remove_none(user_dict)
                print(user_dict)
                # await trace("```py\n" + str(user_dict) + "\n```")
                target = message_in.server.get_member(params[2])
                if target:
                    name = target.name
                    discrim = "#" + target.discriminator
                else:
                    name = params[2]
                    discrim = ""

                embed = discord.Embed(
                    title="{name}#{discrim}'s userinfo".format(
                        name=name,
                        discrim=str(discrim)),
                    type="rich")
                embed.add_field(
                    name="Creation",
                    value=user_dict["created_at"],
                    inline=True
                )
                embed.add_field(
                    name="Nicks",
                    value=user_dict["nicks"],
                    inline=False
                )
                embed.add_field(
                    name="Names",
                    value=user_dict["names"],
                    inline=False
                )
                output = []
                output.append((config["query"]["user"]["dump"], embed, "embed"))
                list_of_rows = []

                print("!" * 20)

                if "server_joins" in user_dict.keys():
                    base = [["Server Joins", "--"]]
                    named_dict = {}
                    for key in user_dict["server_joins"].keys():
                        if client.get_server(key):
                            try:
                                name = client.get_server(key).name
                                if not name:
                                    name = key
                            except:
                                name = key
                            named_dict[name] = user_dict["server_joins"][key]
                        else:
                            print(key)
                    base.extend(dict2rows(named_dict))
                    output.append([config["query"]["user"]["dump"], base, "rows"])
                    # print(output)

                if "server_leaves" in user_dict.keys():
                    base = [["Server Leaves", "--"]]
                    named_dict = {}
                    for key in user_dict["server_leaves"].keys():
                        if client.get_server(key):
                            named_dict[client.get_server(key).name] = user_dict["server_leaves"][key]
                        else:
                            print(key)
                    base.extend(dict2rows(named_dict))
                    output.append([config["query"]["user"]["dump"], base, "rows"])
                    # print(output)

                if "bans" in user_dict.keys():
                    base = [["Server Bans", "--"]]
                    named_dict = {}
                    for key in user_dict["bans"].keys():
                        if client.get_server(key):
                            named_dict[client.get_server(key).name] = user_dict["bans"][key]
                        else:
                            print(key)
                    base.extend(dict2rows(named_dict))
                    output.append([config["query"]["user"]["dump"], base, "rows"])
                    # print(output)

                if "unbans" in user_dict.keys():
                    base = [["Server Unbans", "--"]]
                    named_dict = {}
                    for key in user_dict["unbans"].keys():
                        if client.get_server(key):
                            named_dict[client.get_server(key).name] = user_dict["unbans"][key]
                        else:
                            print(key)
                    base.extend(dict2rows(named_dict))
                    output.append([config["query"]["user"]["dump"], base, "rows"])
                    # print(output)

                # print(output)
                return output

        if params[0] == "roles":
            if params[1] == "list":
                role_list = []
                role_list.append(
                    ["Name", "ID", "Position", "Color", "Hoisted", "Mentionable"])
                for role in message_in.server.role_hierarchy:
                    new_entry = [
                        role.name, "\"{}\"".format(str(role.id)),
                        str(role.position), str(role.colour.to_tuple()),
                        str(role.hoist), str(role.mentionable)
                    ]
                    role_list.append(new_entry)
                return [(config["query"]["roles"]["list"][
                             "output"], role_list, "rows")]

            if params[1] == "members":
                role_members = await get_role_members(
                    await get_role(message_in.server, params[2]))
                output = config["query"]["roles"]["members"]["delimiter"].join(
                    [member.mention for member in role_members])
                return [(config["query"]["roles"]["members"]["output"], output, None)]
        if params[0] == "emoji":
            import re
            emoji_id = utils_text.regex_test("\d+(?=>)",
                                             " ".join(params[1:])).group(0)
            print(emoji_id)
            server_name = None
            for emoji in client.get_all_emojis():
                if emoji_id == emoji.id:
                    server_name = emoji.server.name
                    break
            return [(config["query"]["emoji"]["output"], server_name, None)]
        if params[0] == "owner":
            return [(config["query"]["owner"]["output"], message_in.server.owner.mention, "text")]


    except:
        await trace(traceback.format_exc())

async def command_avatar(params, message_in):
    if params[0] == "get":
        image = Image.open(BytesIO(requests.get(params[1]).content))
        filename = params[2]
    if params[0] == "copy":
        image = Image.open(BytesIO(requests.get(message_in.server.get_member(params[1]).avatar_url).content))
        filename = params[1]
    if params[0] in ["get", "copy"]:
        image_path = utils_file.relative_path(__file__,
                                              "avatars/" + filename + ".png")

        image.save(image_path, "PNG")
        with open(image_path, "rb") as ava:
            await client.edit_profile(
                password=DISCORD_PASSWORD, avatar=ava.read())
    if params[0] == "set":
        with open(os.path.join(os.path.dirname(__file__), "avatars", params[1] + ".png"), "rb") as ava:
            await client.edit_profile(
                password=DISCORD_PASSWORD, avatar=ava.read())

async def command_tag(params, message_in):
    pass

    if params[0] == "set":
        tag_str = params[1]
        expansion = " ".join(params[2:])
        await mongo_client.discord.tags.update_one({"tag":tag_str},{"expansion": expansion}, upsert=True)
        await relay("Set {}`{}`\n to expand to \n ```\n{}\n```".format(config["prefix"]["tag"], tag_str, expansion))
    if params[0] == "list":
        tags = {}
        async for doc in mongo_client.discord.tags.find({}):
            tags[doc["tag"]] = doc["expansion"]
        await relay(dict2rows(tags), "rows")
    if params[0] == "remove":
        res = await mongo_client.discord.tags.find_one_and_delete({"tag":params[1]})
        if res:
            await relay("Unset {}`{}`\n expanding to \n ```\n{}\n```".format(config["prefix"]["tag"], res["tag"], res["expansion"]))
        else:
            await relay("Tag not found")
# IMGUR
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
    config = {'album': None, 'name': 'Added JPEG!', 'title': 'Added JPEG!'}
    ret = imgur_client.upload_from_path(img_path, config=config, anon=True)
    return ret["link"], ratio

# Output


async def serve_lfg(message_in):
    found_message = None
    warn_user = None
    if len(message_in.mentions) == 0:
        found_message = await find_message(
            message_in,
            re.compile((
                r"(lf(G|\d))|(\d\d\d\d)|(plat|gold|silver|diamond)|(^LF(((NA)|(EU))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|"
                "(http(s?)://discord.gg/)|(xbox)|(ps4)")))
    else:
        warn_user = message_in.mentions[0]

    await lfg_warner(
        found_message=found_message,
        warn_user=warn_user,
        channel=message_in.channel)
    await client.delete_message(message_in)

async def lfg_warner(found_message, warn_user, channel):
    lfg_text = (
        "You're probably looking for <#182420486582435840>, <#185665683009306625>, or <#177136656846028801>."
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

# PERSPECTIVE
async def perspective(text):
    analyze_request = {
        'comment'            : {
            'text': text
        },
        'requestedAttributes': {
            'TOXICITY': {}
        },
        'languages'          : ["en"]
    }
    response = perspective_api.comments().analyze(
        body=analyze_request).execute()
    return response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]

async def query_toxicity(params):
    if params[0] == "mosttox":
        target_user_id = params[1]
        count = int(params[2])
        cursor = mongo_client.discord.message_log.find(
            {
                "user_id": target_user_id
            },
            sort=[
                ("toxicity", pymongo.DESCENDING),
            ],
            limit=count)
        cursor.sort("toxicity", -1)
        content = "<@!" + target_user_id + ">"
        async for document in cursor:
            content += "```[{}] {}```\n".format(document["toxicity"],
                                                document["content"].replace(
                                                    "```", "``"))
        return (content, None)

    if params[0] == "toxtop":
        cursor = mongo_client.discord.userinfo.aggregate([{
            "$match": {
                "toxicity"      : {
                    "$exists": True
                },
                "toxicity_count": {
                    "$gt": 15
                }
            }
        }, {
            "$project": {
                "user_id"         : 1,
                "average_toxicity": {
                    "$divide": ["$toxicity", "$toxicity_count"]
                }
            }
        }, {
            "$sort": {
                "average_toxicity": -1
            }
        }, {
            "$limit":
                int(params[1])
        }])

        info = []
        async for user_dict in cursor:
            info.append((str(round(user_dict["average_toxicity"], 2)), " | ",
                         "<@!" + user_dict["user_id"] + ">"))
        return (info, "qrows")

# API Wrappers


async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members

async def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x

# Database
async def mess2log(message):
    text = message.content
    if len(text) < 2:
        return
    await import_message(message)

    # log_str = unidecode(
    #     "[{toxicity}][{time}][{channel}][{name}] {content}".format(
    #         toxicity=toxicity_string,
    #         time=time,
    #         channel=channel,
    #         name=nick,
    #         content=message.content)).replace("\n", r"[\n]")

async def export_user(member_id):
    """

    :type member: discord.Member
    """
    userinfo = await mongo_client.discord.userinfo.find_one(
        {
            "user_id": member_id
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
    await mongo_client.discord.userinfo.update_one(
        {
            "user_id": member.id
        }, {
            "$addToSet": {
                "nicks"                                   : {
                    "$each": [
                        user_info["nick"], user_info["name"],
                        user_info["name"] + "#" + str(user_info["discrim"])
                    ]
                },
                "names"                                   : user_info["name"],
                "server_joins.{}".format(member.server.id):
                    user_info["joined_at"]
            },
            "$set"     : {
                "mention_str": user_info["mention_str"],
                "created_at" : user_info["created_at"]
            },
        },
        upsert=True)

async def import_message(mess):
    messInfo = await utils_parse.parse_message_info(mess)

    if config["perspective"]:
        toxicity = await perspective(mess.content)
        messInfo["toxicity"] = toxicity
        await mongo_client.discord.userinfo.update_one({
            "user_id":
                messInfo["user_id"]
        }, {"$inc": {
            "toxicity"      : toxicity,
            "toxicity_count": 1
        }})

    await mongo_client.discord.message_log.insert_one(messInfo)

async def import_to_user_set(member, set_name, entry):
    await mongo_client.discord.userinfo.update_one({
        "user_id": member.id
    }, {"$addToSet": {
        set_name: entry
    }})

async def import_to_server_user_set(member, server, set_name, entry):
    await mongo_client.discord.userinfo.update_one({
        "user_id": member.id
    }, {"$addToSet": {
        server: {
            set_name: entry
        }
    }})

# Logging


async def format_message_to_log(message_dict):
    cursor = await mongo_client.discord.userinfo.find_one({
        "user_id":
            message_dict["user_id"]
    })
    try:
        name = cursor["names"][-1]
        if not name:
            name = cursor["names"][-2]
    except:
        try:
            cursor = await mongo_client.discord.userinfo.find_one({
                "user_id":
                    message_dict["user_id"]
            })
            name = cursor["names"][-1]
        except:
            name = message_dict["user_id"]
        if not name:
            name = message_dict["user_id"]

    try:
        content = message_dict["content"].replace("```", "[QUOTE]").replace(
            "\n", r"[\n]")
        try:
            channel_name = client.get_channel(message_dict["channel_id"]).name
        except KeyError:
            channel_name = "Unknown"
        try:
            server_name = client.get_server(message_dict["server_id"]).name
        except KeyError:
            server_name = "Unknown"
        return unidecode(
            "[{}][{}][{}][{}]: {}".format(server_name, message_dict["date"][
                                                       2:-7], channel_name, name, content))

    except:
        print(traceback.format_exc())
        return "Errored Message : " + str(message_dict)

# Utilities
async def find_user(matching_ident,
                    find_type,
                    server,
                    cast_to_lower=True,
                    count=1):
    ident_id_set_dict = collections.defaultdict(set)
    matching_ident = " ".join(matching_ident)
    if find_type == "bans":
        banlist = await client.get_bans(server)
        for banned_user in banlist:
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
        mongo_cursor = mongo_client.discord.userinfo.find()
        async for userinfo_dict in mongo_cursor:
            try:
                for nick in userinfo_dict["nicks"]:
                    if nick:
                        ident_id_set_dict[nick].add(userinfo_dict["user_id"])
                for name in userinfo_dict["names"]:
                    if name:
                        ident_id_set_dict[name].add(userinfo_dict["user_id"])
            except:
                print(traceback.format_exc())

    if cast_to_lower:
        matching_ident = matching_ident.lower()
        new_dict = dict([(ident.lower(), id_set)
                         for ident, id_set in ident_id_set_dict.items()])
        ident_id_set_dict = new_dict

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
        for user_id in id_set:
            output += "`ID: {user_id} | Name: {name} |` {mention}\n".format(
                user_id=user_id, name=ident, mention="<@!{}>".format(user_id))
    return (output, None)

async def find_message(message, regex, num_to_search=20):
    """

    :type exclude: str
    :type message: discord.Message
    :type reg: retype
    """
    match = None
    found_message = None
    async for messageCheck in client.logs_from(message.channel, num_to_search):
        if messageCheck.author.id != message.author.id:
            if isinstance(regex, str):
                if messageCheck.content == regex:
                    match = messageCheck
            else:
                match = regex.search(messageCheck.content)
            if match is not None:
                found_message = messageCheck
                return found_message
    return found_message

async def relay(text, send_type=None):
    await send(
        destination=client.get_channel("334043962094387201"),
        text=text,
        send_type=send_type)

async def trace(text):
    await client.send_message(client.get_channel("335171044014948352"), "```" + text + "```")
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

client.loop.create_task(run_startup())
client.run(USER_AUTH_TOKEN, bot=False)
