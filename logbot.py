import json
import logging
import textwrap
from datetime import datetime, timedelta
import traceback
import discord
import motor.motor_asyncio
import regex as re
from utils import utils_text, utils_parse, utils_file
import regex as re
import TOKENS
import constants

logging.basicConfig(level=logging.INFO)

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://{usn}:{pwd}@nadir.space".format(usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS))
# mongo_client = motor.motor_asyncio.AsyncIOMotorClient()

log_db = mongo_client.logbot
client = discord.Client()

STATES = {"init": False}

@client.event
async def on_message(message_in):
    if message_in.author.id == client.user.id:
        return
    if message_in.channel.is_private:
        if message_in.author.id == "129706966460137472":
            command_list = message_in.content.replace("[[","").split(" ")
            if command_list[0] == "reply":
                reply_id = command_list[1]
                reply_content = " ".join(command_list[2:])
                target_user = await client.get_user_info(reply_id)
                await client.send_message(target_user, reply_content)
                await client.send_message(message_in.author, "[" + target_user.name + "]" + "»" + reply_content)

                return
        await client.send_message(await client.get_user_info("129706966460137472"),
                                  "[{id}]{name}#{discrim}: {content}".format(id=message_in.author.id, name=message_in.author.name,
                                                                             discrim=message_in.author.discriminator, content=message_in.content))
        await client.send_message(message_in.author, "[[register to start the registation process. For more help, PM me an invite link to your server")
        if message_in.content.startswith("[["):
            await client.send_message(message_in.author, "Commands must be used in a specific server")
        return
    if message_in.server.id in log_config.keys():
        prefix = log_config[message_in.server.id]["prefix"]
    else:
        prefix = "[["

    if message_in.content.startswith(prefix):
        input = message_in.content[len(prefix):]
        command_list = input.split(" ")
        if message_in.author.id == "129706966460137472":
            print(command_list)
            if command_list[0] == "renick":
                for server in client.servers:
                    await client.change_nickname(server.me, "Logbot")
            if command_list[0] == "reset":
                del log_config[command_list[1]]
                update()
            if command_list[0] == "dump":
                if len(command_list) > 1:
                    target = command_list[1]
                    if target in log_config.keys():
                        await client.send_message(await client.get_user_info("129706966460137472"), log_config[target])
                else:
                    await client.send_message(await client.get_user_info("129706966460137472"), log_config)
        if message_in.author.server_permissions.manage_server or message_in.author.id == "129706966460137472":
            if command_list[0] == "register":
                await client.send_message(message_in.channel, "Starting up the registration process...")
                await client.send_message(message_in.channel, "What would you like your command prefix to be? For example, `!!` in !!ban.")
                message = await client.wait_for_message(author=message_in.author, channel=message_in.channel)
                log_config[message_in.server.id] = {"states": {}}
                log_config[message_in.server.id]["prefix"] = message.content
                await client.send_message(message_in.channel,
                                          "Setting prefix to {prefix}".format(prefix="`" + log_config[message_in.server.id]["prefix"] + "`"))
                await client.send_message(message_in.channel,
                                          "The server log records joins, leaves, bans, and unbans.\nIf you want to enable the server log, please respond with "
                                          "a channel mention or ID. Ex: `#general`. Otherwise, say `no`")
                target_id = None

                def check(msg):
                    nonlocal target_id
                    reg = re.search("\d+", msg.content)
                    if reg:
                        target_id = reg.group(0)
                        return True
                    elif msg.content in ["no", "none", "disable"]:
                        return True
                    else:
                        def send_msg():
                            yield from client.send_message("Sorry, please respond with a channel mention. For example, `#general` or `#bot-log`")

                        discord.compat.create_task(send_msg(), loop=client.loop)

                message = await client.wait_for_message(author=message_in.author, channel=message_in.channel, check=check)
                print(target_id)
                if not target_id:
                    log_config[message_in.server.id]["states"]["server_log"] = False
                else:
                    log_config[message_in.server.id]["states"]["server_log"] = True
                    await client.send_message(message_in.channel, "Setting server log to {channel}".format(channel="<#" + target_id + ">"))
                log_config[message_in.server.id]["server_log"] = target_id

                await client.send_message(message_in.channel,
                                          "The message log records message edits and deletions.\nIf you want to enable the message log, please respond with"
                                          " a channel mention or ID. Ex: `#general`. Otherwise, say `no`")
                target_id = None

                def check(msg):
                    nonlocal target_id
                    reg = re.search("\d+", msg.content)
                    if reg:
                        target_id = reg.group(0)
                        return True
                    elif msg.content in ["no", "none", "disable"]:
                        return True
                    else:
                        def send_msg():
                            yield from client.send_message("Sorry, please respond with a channel mention. For example, `#general` or `#bot-log`")

                        discord.compat.create_task(send_msg(), loop=client.loop)

                message = await client.wait_for_message(author=message_in.author, channel=message_in.channel, check=check)
                if not target_id:
                    log_config[message_in.server.id]["states"]["message_log"] = False
                else:
                    log_config[message_in.server.id]["states"]["message_log"] = True
                    await client.send_message(message_in.channel, "Setting message log to {channel}".format(channel="<#" + target_id + ">"))
                log_config[message_in.server.id]["message_log"] = target_id

                await client.send_message(message_in.channel,
                                          "The voice log records voice channel movement.\n If you want to enable the voice log, please respond with"
                                          " a channel mention or ID. Ex: `#general`. Otherwise, say `no`")
                target_id = None

                def check(msg):
                    nonlocal target_id
                    reg = re.search("\d+", msg.content)
                    if reg:
                        target_id = reg.group(0)
                        return True
                    elif msg.content in ["no", "none", "disable"]:
                        return True
                    else:
                        def send_msg():
                            yield from client.send_message("Sorry, please respond with a channel mention. For example, `#general` or `#bot-log`")

                        discord.compat.create_task(send_msg(), loop=client.loop)

                message = await client.wait_for_message(author=message_in.author, channel=message_in.channel, check=check)
                if not target_id:
                    log_config[message_in.server.id]["states"]["voice_log"] = False
                else:
                    log_config[message_in.server.id]["states"]["voice_log"] = True
                    await client.send_message(message_in.channel, "Setting voice log to {channel}".format(channel="<#" + target_id + ">"))
                log_config[message_in.server.id]["voice_log"] = target_id

                log_config[message_in.server.id]["states"]["global"] = True
                await update()
            if command_list[0] == "toggle":
                if len(command_list) == 1:
                    await client.send_message(message_in.channel, "Toggle <server/message/voice> to switch the logging on and off")
                    return
                state_target = None
                if "server" in command_list[1:]:
                    state_target = "server_log"
                elif "message" in command_list[1:]:
                    state_target = "message_log"
                elif "voice" in command_list[1:]:
                    state_target = "voice_log"
                if state_target:
                    start_state = message_in[message_in.server.id]["states"][state_target]
                    log_config[message_in.server.id]["states"][state_target] = not message_in[message_in.server.id]["states"][state_target]
                    await client.send_message(message_in.channel,
                                              "Toggling {state} from {state_start} to {state_end}".format(state=state_target, state_start=start_state,
                                                                                                          state_end=not start_state))
                    await update()
                else:
                    await client.send_message(message_in.channel, "Did not recognize. Please try again with either `server`, `message`, or `message`")
            if command_list[0] == "setprefix":
                log_config[message_in.server.id]["prefix"] = " ".join(command_list[1:])
                await client.send_message(message_in.channel, "Setting prefix to {prefix}".format(prefix=command_list[1:]))
                await update()
            if command_list[0] == "oauth":
                await client.send_message(message_in.author, discord.utils.oauth_url(client_id=client.user.id))
            if command_list[0] == "info":
                server_config = log_config[message_in.server.id]
                text = [["Log","Channel","Enabled"]]
                for log_type in ["server_log","voice_log","message_log"]:
                    text.append([log_type, message_in.server.get_channel(server_config[log_type]).name if server_config[log_type] else "Unset", "Enabled" if server_config["states"][log_type] else "Disabled"])
                print(text)
                await send(destination=message_in.channel, text=text, send_type="rows")
            if command_list[0] == "help":
                await client.send_message(message_in.channel,
                                          "{pfx}register to restart the registration process"
                                          "\n{pfx}toggle <logname> to toggle a log on or off"
                                          "\n{pfx}setprefix to change the bot's prefix"
                                          "\n{pfx}oauth to get an invite link"
                                          "\n{pfx}info to see current log positions".format(pfx=prefix))


@client.event
async def on_member_remove(member):
    if not STATES["init"]:
        return
    await log_action(member.server, "leave", {"mention": member.mention, "id": member.id})

@client.event
async def on_member_ban(member):
    if not STATES["init"]: return
    await log_action(member.server, "ban", {"member": member})

@client.event
async def on_member_unban(server, member):
    if not STATES["init"]: return
    await log_action(server, "unban", {"mention": "<@!{id}>".format(id=member.id), "id": member.id})

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
async def on_member_join(member):
    if not STATES["init"]: return

    current_date = datetime.utcnow()
    age = abs(current_date - member.created_at)
    await log_action(member.server, "join", {"mention": member.mention, "id": member.id, "age": str(age)[:-7]})

@client.event
async def on_voice_state_update(before, after):
    """
    :type after: discord.Member
    :type before: discord.Member
    """
    if not STATES["init"]: return

    if before.voice.voice_channel != after.voice.voice_channel:
        await log_action(after.server, "voice_update", {"before": before, "after": after, "id": before.id})

# noinspection PyShadowingNames
@client.event
async def on_member_update(before, after):
    """

    :type after: discord.Member
    :type before: discord.Member
    """
    if not STATES["init"]: return

    if not STATES["init"]:
        return

    if len(before.roles) != len(after.roles):
        await log_action(after.server, "role_change",
                         {"member": after, "old_roles": before.roles[1:], "new_roles": after.roles[1:]})

@client.event
async def on_server_join(server):
    try:
        await client.send_message(server.default_channel, "Hi and welcome to Logbot. Get started by typing `[[register`")
    except:
        pass
    await client.change_nickname(server.me, "Logbot")

@client.event
async def on_message_edit(before, after):
    if not STATES["init"]: return
    if before.content == after.content:
        return
    await log_action(after.server, "edit",
                     {"channel": before.channel.mention, "mention": before.author.mention, "id": before.author.id,
                      "before" : before.content, "after": after.content})

@client.event
async def on_message_delete(message):
    if not STATES["init"]: return
    mention = message.author.mention if message.author.mention else message.author.name + message.author.discriminator
    await log_action(message.server, "delete",
                     {"channel": message.channel.mention, "mention": mention, "id": message.author.id,
                      "content": message.content})

async def log_action(server, action, detail):
    if server.id in log_config.keys():
        server_log = client.get_channel(log_config[server.id]["server_log"])
        message_log = client.get_channel(log_config[server.id]["message_log"])
        voice_log = client.get_channel(log_config[server.id]["voice_log"])
    else:
        return
    if not log_config[server.id]["states"]["global"]:
        return


    time = datetime.utcnow().isoformat(" ")
    time = time[5:19]
    time = time[6:19] + " " + time[0:5]
    print("Logging action")
    if any(key in ["before", "after", "content", "mention"] for key in detail.keys()):
        for key in detail.keys():
            if key == "before" and isinstance(detail["before"], str):
                target = "before"
            elif key == "after" and isinstance(detail["before"], str):
                target = "after"
            elif key == "content":
                target = "content"
            elif key == "mention":
                target = "mention"
            else:
                continue
            new = []
            for word in re.split(r"\s", detail[target]):
                if utils_text.regex_test(
                        r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)",
                        word):
                    word = "<" + word + ">"
                new.append(word)
            detail[target] = " ".join(new)
            if action not in ["leave", "ban"]:
                detail[target] = await scrub_text(detail[target], server_log)

    time = "`" + time + "`"
    message = None
    target_channel = None
    if log_config[server.id]["states"]["message_log"]:
        if action == "delete":

            message = "{time} :wastebasket: [DELETE] [{channel}] [{mention}] [{id}]:\n{content}".format(time=time,
                                                                                                        channel=detail[
                                                                                                            "channel"],
                                                                                                        mention=detail[
                                                                                                            "mention"],
                                                                                                        id=detail["id"],
                                                                                                        content=detail[
                                                                                                            "content"])
            target_channel = message_log
            await log_db[server.id].insert_one(
                {"date"   : datetime.utcnow().isoformat(" "), "action": action, "channel": detail["channel"],
                 "mention": detail["mention"], "id": detail["id"],
                 "content": detail["content"]})
        elif action == "edit":
            message = "{time} :pencil: [EDIT] [{channel}] [{mention}] [{id}]:\n`-BEFORE:` {before} \n`+ AFTER:` {after}".format(
                time=time, channel=detail["channel"], mention=detail["mention"], id=detail["id"], before=detail["before"],
                after=detail["after"])
            target_channel = message_log
            await log_db[server.id].insert_one(
                {"date"   : datetime.utcnow().isoformat(" "), "action": action, "channel": detail["channel"],
                 "mention": detail["mention"], "id": detail["id"],
                 "before" : detail["before"], "after": detail["after"]})

    if log_config[server.id]["states"]["server_log"]:
        if action == "join":
            message = "{time} :inbox_tray: [JOIN] [{mention}] [{id}]. Account Age: {age}".format(time=time,
                                                                                                 mention=detail["mention"],
                                                                                                 id=detail["id"],
                                                                                                 age=detail["age"])
            target_channel = server_log
            await log_db[server.id].insert_one(
                {"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"], "age": detail["age"]})
        elif action == "leave":
            message = "{time} :outbox_tray: [LEAVE] [{mention}] [{id}]".format(time=time, mention=detail["mention"],
                                                                               id=detail["id"])
            target_channel = server_log
            await log_db[server.id].insert_one(
                {"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"]})

        elif action == "ban":
            message = "{time} :no_entry_sign: [BAN] [{mention}] [{id}] Name: {name} {nick}".format(time=time,
                                                                                                   mention=detail[
                                                                                                       "member"].mention,
                                                                                                   id=detail["member"].id,
                                                                                                   name=detail[
                                                                                                            "member"].name + "#" +
                                                                                                        detail[
                                                                                                            "member"].discriminator,
                                                                                                   nick=
                                                                                                   detail["member"].nick if
                                                                                                   detail[
                                                                                                       "member"].nick else "")
            target_channel = server_log
            await log_db[server.id].insert_one(
                {"date"   : datetime.utcnow().isoformat(" "), "action": action, "id": detail["member"].id,
                 "mention": detail["member"].mention})

        elif action == "unban":
            message = "{time} :white_check_mark:  [UNBAN] [{mention}] [{id}]".format(time=time,
                                                                                     mention="<@!" + detail["id"] + ">",
                                                                                     id=detail["id"])

            target_channel = server_log
            await log_db[server.id].insert_one(
                {"date"   : datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"],
                 "mention": detail["mention"]})
        elif action == "role_change":
            # print("TRIGGERING ROLE CHANGE")
            target_channel = server_log

            member = detail["member"]
            old_roles = detail["old_roles"]
            new_roles = detail["new_roles"]
            # old_role_ids = [role.id for role in old_roles]
            new_role_ids = " ".join([role.id for role in new_roles])
            before = " ".join([role.mention for role in old_roles])
            after = " ".join([role.mention for role in new_roles])
            mention = member.mention
            mention = await scrub_text(mention, target_channel)

            message = "{time} :pencil: [ROLECHANGE] [{mention}] [{id}]:\n`-BEFORE:` {before} \n`+ AFTER:` {after}".format(
                time=time, mention=mention,
                id=member.id, before=before, after=after)
            message = await scrub_text(message, target_channel)

    if log_config[server.id]["states"]["voice_log"]:
        if action == "voice_update":
            # if log_config[]
            before = detail["before"]
            voice_state = before.voice
            if not voice_state.voice_channel:
                before = "Joined Voice"
            else:
                before = voice_state.voice_channel.name
            after = detail["after"]
            voice_state = after.voice
            if not voice_state.voice_channel:
                after = ":Left Voice:"
            else:
                after = voice_state.voice_channel.name

            now = datetime.utcnow()
            threshold = timedelta(minutes=5)
            ago = now - threshold
            date_text = ago.isoformat(" ")

            movecount = await (
                log_db[server.id].find({"action": action, "id": detail["id"], "date": {"$gt": date_text}}).count())

            if movecount < 5:
                emoji = ":white_check_mark:"
            elif movecount < 10:
                emoji = ":grey_question:"
            elif movecount < 15:
                emoji = ":warning:"
            elif movecount < 20:
                emoji = ":exclamation:"
            else:  # movecount < 25:
                emoji = ":bangbang:"
            target_channel = voice_log
            if voice_state.voice_channel:
                in_room = str(len(voice_state.voice_channel.voice_members))
                room_cap = str(voice_state.voice_channel.user_limit)
            else:
                in_room = "0"
                room_cap = "0"
            message = "{emoji} {date} {mention} : `{before}` → `{after}` [{usercount}/{userlimit}] ({count})".format(
                emoji=emoji, date=time,
                mention="<@!" + detail["id"] + ">",
                before=before, after=after, usercount=in_room,
                userlimit=room_cap, count=movecount)

            await log_db[server.id].insert_one(
                {"date": datetime.utcnow().isoformat(" "), "action": action, "id": detail["id"]})

    if message and target_channel:
        message = await scrub_text(message, voice_log)
        await client.send_message(target_channel, message)

# async def import_to_user_set(member, set_name, entry):
#     await overwatch_db.userinfo_collection.update_one(
#         {"userid": member.id},
#         {
#             "$addToSet": {set_name: entry}
#         }
#     )


async def scrub_text(text,channel):
    try:
        def escape_user(match):
            mention = match.group(0)
            userid = re.search("\d+", mention)
            userid = userid.group(0)
            member = channel.server.get_member(userid)
            permissions = channel.permissions_for(member)
            if permissions.read_messages:
                return member.name
            else:
                return mention
            pass
        text = re.sub("(<@!?\d+>)", escape_user, text)

        def escape_role(match):
            mention = match.group(0)
            roleid = re.search("\d+", mention)
            role = get_role(channel.server, roleid)

            if role and role.mentionable:
                return role.name
            else:
                return mention
        text = re.sub("(<#!?\d+>)", escape_role, text)
    except:
        print(traceback.format_exc())
    return text

            # for group in [group for group in userid_matches.groups() if group]:



async def scrub_text2(text, channel):
    new_words = []
    words = re.split(r" ", text)
    for word in words:
        # Roles
        match = re.match(r"(<@&\d+>)", word)
        if match:
            id = match.group(0)
            id = re.search(r"\d+", id)
            id = id.group(0)
            role = get_role(server=channel.server, roleid=id)
            overwrites = channel.overwrites_for(role)
            perm = overwrites.pair()[0]
            if perm.read_messages:
                new_words.append(r"\@" + role.name)

            else:
                new_words.append(word)
            continue
        match = re.match(r"(<@!?\d+>)|(@everyone)|(@here)", word)
        if match:
            id = match.group(0)
            if id not in ["@everyone", "@here"]:
                id = re.search(r"\d+", id)
                id = id.group(0)
                member = channel.server.get_member(id)
                if not member:
                    continue
                perms = channel.permissions_for(member)
                if perms.read_messages:
                    new_words.append(r"\@" + member.name)
                else:
                    new_words.append(word)
            else:
                new_words.append("\\" + word)
        else:
            new_words.append(word)
    return " ".join(new_words)

async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members

def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x

async def get_moderators(server):
    members = []
    for role in server.roles:
        if role.permissions.manage_roles or role.permissions.ban_members:
            members = get_role_members(role)
            members.extend(members)
    return members

# async def import_user(member):
#     user_info = await utils_parse.parse_member_info(member)
#     result = await overwatch_db.userinfo.update_one(
#         {"userid": member.id},
#         {
#             "$addToSet": {
#                 "nicks": {"$each": [user_info["nick"], user_info["name"]]},
#                 "names": {"$each": [user_info["name"]]},
#                 "full_name":user_info["name"] + "#" + str(user_info["discrim"]),
#                 "avatar_urls": user_info["avatar_url"],
#                 "server_joins": user_info["joined_at"]},
#             "$set": {"mention_str": user_info["mention_str"],
#                      "created_at": user_info["created_at"]},
#
#         }
#         , upsert=True
#     )
#     pass
async def send(destination, text, send_type, delete_in=0):
    if isinstance(destination, str):
        destination = await client.get_channel(destination)

    if send_type == "rows":
        print("FIRING")
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



async def clock():
    await update()
    await client.wait_until_ready()
    STATES["init"] = True
    STATES["server_log"] = True

    print("Ready")

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

async def update():
    with open(utils_file.relative_path(__file__, "log_config.json"), 'w') as config:
        json.dump(log_config, config)

with open(utils_file.relative_path(__file__, "log_config.json"), 'r') as config:
    log_config = json.load(config)

client.loop.create_task(clock())

client.run(TOKENS.LOGBOT_TOKEN, bot=True)
