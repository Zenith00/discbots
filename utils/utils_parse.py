import asyncio
from pyshorteners import Shortener
import traceback
async def parse_message_info(mess) -> dict:
    """
    :type mess: discord.Message
    """
    user_id = mess.author.id
    messageContent = mess.content
    messageLength = len(messageContent)
    mentioned_users = []
    mentioned_channels = []
    mentioned_roles = []
    for x in mess.mentions:
        mentioned_users.append(str(x.id))
    for x in mess.channel_mentions:
        mentioned_channels.append(str(x.id))
    for x in mess.role_mentions:
        mentioned_roles.append(str(x.id))
    server_id = mess.server.id if mess.server else mess.channel.id
    info_dict = {
        "user_id"            : user_id,
        "content"           : messageContent,
        "length"            : messageLength,
        "date"              : mess.timestamp.isoformat(" "),
        "mentioned_users"   : mentioned_users,
        "mentioned_channels": mentioned_channels,
        "mentioned_roles"   : mentioned_roles,
        "channel_id"        : mess.channel.id   ,
        "server_id"         : server_id,
        "message_id"           : mess.id

    }
    return info_dict

async def parse_user_info(user) -> dict:
    """

    :type user: discord.User
    """
    info_dict = {
        "name"       : user.name,
        "id"         : user.id,
        "is_bot"     : user.bot,
        "avatar_url" : user.avatar_url,
        "mention_str": user.mention,
        "created_at" : user.created_at.isoformat(" "),
        "discrim" : user.discriminator,

    }
    return info_dict

async def parse_member_info(member) -> dict:
    """
    :type member: discord.Member
    """
    info_dict = await parse_user_info(member)
    if member.nick is None:
        userNick = member.name
    else:
        userNick = member.nick

    userNick = userNick
    userNick = userNick.lower()

    roleIDs = []
    roleNames = []
    # print(member.roles)
    for x in member.roles:
        roleIDs.append(x.id)
        # print(roleIDs)
        roleNames.append(x.name)
        # print(roleNames)

    info_dict["role_ids"] = roleIDs
    info_dict["role_names"] = roleNames
    info_dict["color"] = member.color
    info_dict["nick"] = userNick
    try:
        info_dict["joined_at"] = member.joined_at.isoformat(" ")
    except:
        print(info_dict["name"])
        print(traceback.format_exc())
    return info_dict





def reverse_dict(indict):
    return dict([[v, k] for k, v in indict.items()])