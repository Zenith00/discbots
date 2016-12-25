import copy
import heapq
import logging
import math
import random
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime
from io import StringIO

import discord
import motor.motor_asyncio
import pymongo
import wolframalpha
from asteval import Interpreter
from fuzzywuzzy import fuzz
from imgurpython import ImgurClient
from overwatch_api import OverwatchAPI
from pymongo import ReturnDocument
from simplegist.simplegist import Simplegist
import constants
import unicodedata
from utils_text import *
from utils_parse import *
from unidecode import unidecode
from TOKENS import *
ENABLED = True
logging.basicConfig(level=logging.INFO)
client = discord.Client()
imgur = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_ID, IMGUR_ACCESS_TOKEN,
                    IMGUR_REFRESH_TOKEN)
WA_client = wolframalpha.Client(WA_ID)
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
overwatch_db = mongo_client.overwatch
message_log_collection = overwatch_db.message_log
userinfo_collection = overwatch_db.userinfo
auths_collection = overwatch_db.auths
trigger_str_collection = overwatch_db.trigger_str
aeval = Interpreter()
id_channel_dict = {}
STREAM = None

gistClient = Simplegist()

BOT_HAPPENINGS_ID = "245415914600661003"
ROLENAME_ROLE_DICT = {}
ID_ROLENAME_DICT = dict([[v, k] for k, v in constants.ROLENAME_ID_DICT.items()])
BLACKLISTED_CHANNELS = (
    constants.CHANNELNAME_CHANNELID_DICT["bot-log"], constants.CHANNELNAME_CHANNELID_DICT["server-log"],
    constants.CHANNELNAME_CHANNELID_DICT["voice-channel-output"])
SERVERS = {}
CHANNELNAME_CHANNEL_DICT = {}
VCInvite = None
VCMess = None
INITIALIZED = False

class Streamer:
    def __init__(self, chann, thresh):
        self.channel = chann
        self.threshold = thresh
        self.counter = 0
        self.message = ""

    async def add(self, string):
        self.message += string + "\n"
        # print(ascii(self.message))
        print(str(self.counter) + " " + str(self.threshold))
        if self.counter >= self.threshold:
            await client.send_message(self.channel, self.message)
            self.counter = 0
            self.message = ""
        else:
            self.counter += 1

class ScrimTeam:
    def __init__(self, id, channel):
        self.members = []
        self.name = id
        self.vc = channel

class ScrimMaster:
    def __init__(self, scr1, scr2, txt, spec):
        self.team1 = scr1
        self.team2 = scr2
        # self.members = {}
        self.text = txt
        self.spectate = spec
        self.masters = []

    async def get_managers(self):
        managers = []
        manager_cursor = overwatch_db.scrim.find({"manager": 1})
        async for manager in manager_cursor:
            managers.append(manager["userid"])

        return managers

    async def end(self):
        await client.delete_channel(self.team1.vc)
        await client.delete_channel(self.team2.vc)
        await client.delete_channel(self.text)
        await client.delete_channel(self.spectate)

    async def assign(self, member, team):
        await self.deauth(member)
        return await self.auth(member, team)

    async def reset(self, message):
        cursor = overwatch_db.scrim.find({"active": True})
        async for person in cursor:
            await self.deauth(message.server.get_member(person["userid"]))
            # await overwatch_db.scrim.update_many({"active": True}, {"$set": {"team": "0"}})

    async def auth(self, member, team):
        if team == "0":
            await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"team": "0"}})
            return member.mention + " unassigned"
        if team == "1":
            target_team = self.team1
        else:  # team == "2":
            target_team = self.team2

        # self.members[member.id] = team
        await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"team": target_team.name}})

        target_team.members.append(member.id)
        # print(target_team.members)
        # print(target_team.name)
        user_overwrite_vc = discord.PermissionOverwrite(connect=True)
        await client.edit_channel_permissions(target_team.vc, member, user_overwrite_vc)
        return member.mention + " added to team " + target_team.name

    async def deauth(self, member):
        # try:
        #     target = self.members[member.id]
        # except KeyError:
        #     return "User is not in a team"
        target_member = await overwatch_db.scrim.find_one({"userid": member.id})
        target = target_member["team"]
        if target == "1":
            target_team = self.team1
        elif target == "2":
            target_team = self.team2
        else:
            return
        #
        # try:
        #     target_team.members.remove(member.id)
        # except:
        #     print(traceback.format_exc())
        #     print(target_team.members)
        # del self.members[member.id]

        await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"team": "0"}})
        await client.delete_channel_permissions(target_team.vc, member)
        return member.mention + " removed from team " + target_team.name

    async def add_user(self, member):
        userid = member.id
        await overwatch_db.scrim.update_one({"userid": userid},
                                            {"$set": {"team": "0", "active": True, "manager": 0}}, upsert=True)

    async def leave(self, member):
        userid = member.id
        await overwatch_db.scrim.update_one({"userid": userid},
                                            {"$set": {"team": "0", "active": False, "manager": 0}}, upsert=True)
        return "Removed " + member.mention + " from the active user pool"

    async def register(self, member, btag):
        sr = await get_sr(btag)
        if sr == "0":
            await client.send_message(member,
                                      "BTag not recognized. Please make sure that capitalization and spelling are both correct, and that you have placed on this account")
            sr = "unplaced"
        await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"rank": sr, "btag": btag, "active": True}})
        return sr

    async def refresh(self, member):
        user = await overwatch_db.scrim.find_one({"userid": member.id})
        await self.register(member, user["btag"])


async def initialize():
    global INITIALIZED
    global STREAM
    global stream

    SERVERS["OW"] = client.get_server(constants.OVERWATCH_SERVER_ID)
    for role in SERVERS["OW"].roles:
        if role.id in ID_ROLENAME_DICT.keys():
            ROLENAME_ROLE_DICT[ID_ROLENAME_DICT[role.id]] = role

    for name in constants.CHANNELNAME_CHANNELID_DICT.keys():
        CHANNELNAME_CHANNEL_DICT[name] = SERVERS["OW"].get_channel(constants.CHANNELNAME_CHANNELID_DICT[name])

    STREAM = client.get_channel("255970182881738762")
    stream = Streamer(chann=STREAM, thresh=6)
    INITIALIZED = True


async def get_redirected_url(url):
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    request = opener.open(url)
    return request.url


# noinspection PyPep8


async def get_mentions(mess, auth):
    target = mess.author

    await client.send_message(target, "Automated Mention Log Fetcher Starting Up!")
    await client.send_message(target, "Please respond with the number in the parentheses (X)")
    if auth == "mod":
        await client.send_message(target,
                                  "Would you like to query personal mentions (1), admin/mod mentions (2), or both (3)?")

        response_mess = await get_response_int(target)
        if response_mess is not None:
            await get_logs_mentions(response_mess.content, mess)
        else:
            await client.send_message(target, "You have taken too long to respond! Please restart.")
    else:
        await get_logs_mentions("1", mess)


async def get_response_int(target) -> discord.Message:
    """

    :type target: discord.User
    """

    def check(msg):
        if msg.server == None and msg.author.id == target.id:
            try:
                int(msg.content)
                return True
            except ValueError:
                return False

    return await client.wait_for_message(timeout=30, author=target, check=check)


async def get_response(message):
    def check(msg):
        if message.server == msg.server and msg.author.id == message.author.id and message.channel == msg.channel:
            return True
        return False

    return await client.wait_for_message(timeout=30, check=check)


@client.event
async def on_member_remove(member):
    await add_to_user_set(member=member, set_name="server_leaves", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_member_ban(member):
    await add_to_user_set(member=member, set_name="bans", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_member_unban(member):
    await add_to_user_set(member=member, set_name="unbans", entry=datetime.utcnow().isoformat(" "))


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


@client.event
async def on_member_join(member):
    # await add_to_nick_id_list(member)
    await add_to_user_list(member)
    return


# noinspection PyUnusedLocal
@client.event
async def on_voice_state_update(before, after):
    """
    :type after: discord.Member
    :type before: discord.Member
    """
    global VCInvite
    global VCMess
    if VCInvite is not None and VCMess is not None:
        if after is VCMess.author:
            await client.delete_messages([VCInvite, VCMess])
            VCInvite = None
            VCMess = None


# noinspection PyShadowingNames
@client.event
async def on_member_update(before, after):
    """

    :type after: discord.Member
    :type before: discord.Member
    """
    if not after.joined_at:
        pass
    try:
        await add_to_user_list(after)
    except:
        pass


async def ascii_string(toascii):
    """
    :type toascii: str
    """

    return toascii.encode('ascii', 'ignore').decode("utf-8")


async def get_role(server, roleid):
    for x in server.roles:
        if x.id == roleid:
            return x


async def authorize_user(command_list):
    print(command_list)
    user_id = command_list[0]
    auth_type = command_list[1]

    # if auth_type == "get_art":
    #     utils_persist.set("art_auths", user_id)
    #     # with open(PATHS["comms"] + "art_credentials.txt", "a") as cred_list:
    #     #     cred_list.write(str(user_id) + "\n")
    # if auth_type == "hots":
    #     utils_persist.set("hots_auths", user_id)
    #     # with open(PATHS["comms"] + "hots_credentials.txt", "a") as cred_list:
    #     #     cred_list.write(str(user_id) + "\n")
    # if auth_type == "lfg":
    #     utils_persist.set("lfg_auths", user_id)
    #     # with open(PATHS["comms"] + "lfg_credentials.txt", "a") as cred_list:
    #     #     cred_list.write(str(user_id) + "\n")


# async def credential(member, level):
#     """
#
#     :type level: str
#     :type member: discord.Member
#     """
#
#     author_info = await parse_member_info(member)
#     role_whitelist = any(x in [constants.ROLENAME_ID_DICT["TRUSTED_ROLE"], constants.ROLENAME_ID_DICT["MVP_ROLE"]]
#                          for x in author_info["role_ids"])
#     mod_whitelist = member.server_permissions.manage_roles  and not any(x in "138132942542077952" for x in author_info["role_ids"])
#     zenith = member.id == constants.ZENITH_ID
#     # print("auth: " + level)
#     if level == "mod":
#         return mod_whitelist or zenith
#     elif level == "zenith":
#         return zenith
#     elif level == "trusted":
#         return mod_whitelist or role_whitelist or zenith
#     elif level == "lfg":
#         with open(PATHS["comms"] + "lfg_credentials.txt", "r") as cred_list:
#             creds = cred_list.readlines()
#             return (author_info["id"] + "\n") in creds or role_whitelist or mod_whitelist
#     elif level == "hots":
#         with open(PATHS["comms"] + "hots_credentials.txt", "r") as cred_list:
#             creds = cred_list.readlines()
#             return (author_info["id"] + "\n") in creds or role_whitelist or mod_whitelist
#     elif level == "get_art":
#
#         with open(PATHS["comms"] + "art_credentials.txt", "r") as cred_list:
#             creds = cred_list.readlines()
#
#             return (author_info["id"] + "\n") in creds or role_whitelist or mod_whitelist


async def get_auths(member):
    """

    :type member: discord.Member
    """
    author_info = await parse_member_info(member)
    role_whitelist = any(x in [constants.ROLENAME_ID_DICT["TRUSTED_ROLE"], constants.ROLENAME_ID_DICT["MVP_ROLE"]]
                         for x in author_info["role_ids"])
    mod_whitelist = member.server_permissions.manage_roles and not any(
        x in "138132942542077952" for x in author_info["role_ids"])
    auths = set()
    if member.id == constants.ZENITH_ID:
        auths |= {"zenith"}
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"mod"}
    if mod_whitelist:
        auths |= {"mod"}
        auths |= {"warn"}
        auths |= {"trusted"}
    if role_whitelist:
        auths |= {"trusted"}
        auths |= {"warn"}
        auths |= {"lfg"}
    if any(x in "138132942542077952" for x in author_info["role_ids"]):
        auths |= {"bot"}
    # unspaggheti
    warn_auths = await overwatch_db.auths.find_one({"type": "warn"})
    if warn_auths:
        try:
            auth_list = warn_auths["ids"]
            if member.id in auth_list:
                auths |= {"warn"}
        except (KeyError, TypeError):
            print("ids not found")
            pass
    return auths


async def clear_nicknames():
    await userinfo_collection.update_many({}, {"$unset": {"nicks": ""}})


async def remind_me(command_list, message):
    try:
        time = int(aeval(command_list[1]))
        await asyncio.sleep(time)
        await client.send_message(message.channel, "Reminding " + message.author.mention + " after " + str(
            time) + " seconds:\n" + command_list[0])
    except:
        print(traceback.format_exc())


async def wolfram(message):
    command = message.content.replace("`wa ", "")
    res = WA_client.query(command)
    try:
        podlist = res["pod"]
        print(ascii(res))
    except:
        print(ascii(res))
        print("LOLFAIL")
        return
    numpods = int(res["@numpods"])
    keydict = {}
    options = ""
    print("numpods = " + str(numpods))
    print(res["@numpods"])
    for num in range(0, numpods - 1):
        pod = podlist[num]
        options += "[" + str(num) + "] " + pod["@title"] + "\n"
        print("NUM = " + str(pod["@numsubpods"]))
        for sub_num in range(0, int(pod["@numsubpods"])):
            subpod = pod["subpod"]
            if subpod["@title"] != "":
                options += "    [" + str(num) + "." + str(sub_num) + "] " + subpod["@title"] + "\n"
        keydict[num] = pod
    options = await client.send_message(message.channel, options)
    response = await get_response(message)
    try:
        response = int(response.content)
        pod = podlist[response]
        subpods = []
        text = ""
        if pod["@numsubpods"] == "1":
            subpods.append(pod["subpod"])

        else:
            for x in pod["subpod"]:
                subpods.append(x)

        for subpod in subpods:
            img = (subpod["img"])["@src"]
            img = await shorten_link(img)
            text += img + "\n"
        await client.send_message(message.channel, text)

    except:
        print(traceback.format_exc())
    await client.delete_message(options)
    pass


async def get_role_members(role) -> list:
    members = []
    for member in role.server.members:
        if role in member.roles:
            members.append(member)
    return members


async def get_moderators(server):
    users = []
    for role in server.roles:
        if role.permissions.manage_roles:
            members = await get_role_members(role)
            users.extend(members)
    return users


@client.event
async def on_message(message):
    global VCMess
    global VCInvite
    global PATHS
    global ENABLED

    if not ENABLED:
        return
    if message.author.id == client.user.id:
        return

    if message.server is None:
        if scrim:
            if regex_test(reg_str=r"^\D.{2,12}#\d{4}$", string=message.content):
                await scrim.register(message.author, message.content)

        await client.send_message(await client.get_user_info(constants.ZENITH_ID),
                                  "[" + message.author.name + "]: " + message.content)
        return
    if message.channel.id in BLACKLISTED_CHANNELS:
        return
    if not INITIALIZED and message.server.id == constants.OVERWATCH_SERVER_ID:
        await initialize()
    else:
        # print("message received")
        # if message.content.startswith("-help"):
        #     command = message.content.replace("`help ", "")
        #     command_list = command.split(" ")
        #     await command_info(*[message, command_list])
        if message.content.startswith("`scrim"):
            await scrim_manage(message)

        if message.channel == CHANNELNAME_CHANNEL_DICT["spam-channel"]:
            await message_check(message)
        if message.channel.id not in BLACKLISTED_CHANNELS and message.server.id == constants.OVERWATCH_SERVER_ID:
            await mongo_add_message_to_log(message)

        auths = await get_auths(message.author)
        if "bot" in auths:
            return
        if "zenith" in auths or message.author.id == "203455531162009600":
            if message.content.startswith("`wa"):
                await wolfram(message)
        if "zenith" in auths:
            if message.content.startswith("`rolemembers"):
                id = message.content.replace("`rolemembers, ")
            if message.content.startswith("`parseids"):
                ids = ["213201781096841218",
                       "135288293548883969",
                       "140724909742620672",
                       "66093947541266432",
                       "161931898191478785",
                       "248841864831041547",
                       "153907504810688513",
                       "102209327045033984",
                       "78269059233226752",
                       "187123419043725312",
                       "94966514817441792",
                       "215094448009248768",
                       "95415038768066560",
                       "103057791312203776",
                       "129706966460137472",
                       "90302230506258432",
                       "100447011131654144",
                       "106391128718245888",
                       "192169418502045697",
                       "114550759378386952",
                       "108962416582238208",
                       "95990534006394880",
                       "95152482707050496",
                       "147454963117719552",
                       "113034889233727488",
                       "99170554476515328",
                       "109475514497933312",
                       "126861133955989504",
                       "174875522885615616",
                       "144590937237094400",
                       "84419172146102272",
                       "131211223843733505",
                       "147617541555093504",
                       "178403509656354816",
                       "113182044925763584",
                       "188025061171527680",
                       "139697252712054784",
                       "94408525366697984",
                       "183603736965414921",
                       "77511942717046784",
                       "114660994168520709",
                       "216548128701153291",
                       "116096391171801095",
                       "107344196007907328",
                       "216956538571456523",
                       "105884977274585088",
                       "128980591826829312",
                       "192336550959382528",
                       "154292345804816387",
                       "131150836528054272",
                       "128926571653234688",
                       "203455531162009600",
                       "133884121830129664",
                       "55197013377036288",
                       "154830443156340739",
                       "87272705484656640",
                       "211343735315759104",
                       "193919771165589514",
                       "185106988957564928",
                       "144765828313776128",
                       "102087180465221632",
                       "170624581923504128",
                       "177864529919737856",
                       "94954890064826368",
                       "133123120528752640",
                       "140193750466035712",
                       "146417780319715328",
                       "185459500319375361",
                       "168636602896220170",
                       "109713556513009664",
                       "200311470905360385",
                       "240951935082037249",
                       "104569538640609280",
                       "229340303318843392",
                       "236341193842098177",
                       "221921020985081856",
                       "193771064810143744",
                       "66253300953001984",
                       "239921629952606209",
                       "153705858184904704",
                       "145694691340451841",
                       "81883814099423232",
                       "234830800447602688",
                       "173982717120086016",
                       "91361811382685696",
                       "109032564840226816",
                       "107563539434065920",
                       "162346436111892480",
                       "120655013952487425",
                       "235939140108025856",
                       "195876139678433280",
                       "108502117316083712",
                       "146660812675743745",
                       "86659912490291200",
                       "84694402248749056",
                       "141986063911616512",
                       "224644645726978048",
                       "81857014405271552",
                       "111150306594652160",
                       "180046048125911040",
                       "186547391166414848",
                       "185780141899644939",
                       "118191207259176962",
                       "133260197899534336",
                       "64438382779957248",
                       "158342180904239105",
                       "96393402484019200",
                       "168530785425424386",
                       "164466425065504768",
                       "97771062690865152",
                       "127778787147513865",
                       "170303356802301952",
                       "82175345117102080",
                       "83480674685685760",
                       "186158490484604929",
                       "110761252963221504",
                       "126866524467101696",
                       "127085766491766794",
                       "96671707519029248",
                       "161634690552299521",
                       "153828849497407489",
                       "93785357971107840",
                       "133082672099622912",
                       "117517068378570759",
                       "178430687840436225",
                       "111911466172424192",
                       "234892114784157706",
                       "144071888744873984",
                       "101345079276339200",
                       "223503263348162560",
                       "201853883918712833",
                       "66021157416992768",
                       "188207494072500224",
                       "186883863815913472",
                       "110296169850118144",
                       "231210509800570882",
                       "144258331559591936",
                       "160404210733547520",
                       "163113821521575936",
                       "182888650055352320",
                       "250683040034979850",
                       "82993510503944192",
                       "163008912348413953",
                       "152856310289924096",
                       "181118412947193856",
                       "66697400403623936",
                       "168273385686695936",
                       "122548638319771650",
                       "108647491112550400",
                       "163299066455785472",
                       "114068227390308356",
                       "161148518013206528",
                       "196420412949790720",
                       "147135640620761088",
                       "150774616854364162",
                       "223442874803552256",
                       "105927205908930560",
                       "94907130888327168",
                       "105401020540010496",
                       "166548527802089474",
                       "127897769007382528",
                       "151324096834174976",
                       "185067903232638976",
                       "72490462002290688",
                       "173869239415865344",
                       "105250002154098688",
                       "191592425792339969",
                       "170270325840281600",
                       "98683447937073152",
                       "184464634042908672",
                       "99278737173925888",
                       "199042671283535872",
                       "128188352494174208",
                       "133644191677808640",
                       "97656405300875264",
                       "132259573850570752",
                       "153322645868249088",
                       "136247578588217344",
                       "216669878868901888",
                       "137725178183417857",
                       "160817967410446336",
                       "113032600053919744",
                       "98305506107469824",
                       "115360688217653254",
                       "122317844875706370",
                       "180526293421391872",
                       "85381430737121280",
                       "135547793359110144",
                       "166493287748861952",
                       "150409112239210496",
                       "104322726235238400",
                       "103181183189291008",
                       "146111459028500480",
                       "105651153991118848",
                       "109182240314912768",
                       "185043969682571264",
                       "105792300944207872",
                       "153778873966788608",
                       "165974810084507649",
                       "98773463384207360",
                       "188854531424124936",
                       "91639231486623744",
                       "118562243330834432",
                       "209493075003834368",
                       "243775802720649216",
                       "136689482320707585",
                       "109244329737875456",
                       "200975510572892160",
                       "122706671050031104",
                       "225432040361820181",
                       "133670692175609856",
                       "212208195601563648",
                       "114777914486161411",
                       "155159390637260800",
                       "114881458853642247",
                       "87853815860043776",
                       "106237000423620608",
                       "122116743840661507",
                       "135293735536820224",
                       "198805116810297344",
                       "156216526666596352",
                       "78620326186983424",
                       "175934448372547584",
                       "130128518196625409",
                       "98869847806472192",
                       "112535542876377088",
                       "137715600406478848",
                       "106579156325711872",
                       "160538103784800256",
                       "254775356312125451",
                       "193009725317709824",
                       "95460686674530304",
                       "68934448753676288",
                       "77689118238179328",
                       "110100680605175808",
                       "139140314546962432",
                       "206852280027185152",
                       "89335688234803200",
                       "187970779667890177",
                       "118351756378767361",
                       "128554011774287872",
                       "244950850693234688",
                       "165664060480684032",
                       "95978825338322944",
                       "80142891887890432",
                       "97153000669184000",
                       "195671081065906176",
                       "141009615566405632",
                       "106257001058721792",
                       "165171098554466304",
                       "156649703075741696",
                       "208674560466223104",
                       "168448006188695553",
                       "92006858860040192",
                       "90870687639572480",
                       "212978130057560065",
                       "228492507124596736",
                       "222581386559750144",
                       "94886189416316928",
                       "155824535743102976",
                       "98315077668581376",
                       "168207369413591040",
                       "104200096945537024",
                       "187966224930570240",
                       "102127940052975616",
                       "214152235339350026",
                       "95206413130801152",
                       "125827887793307650",
                       "194746589594517514",
                       "154071358932910080",
                       "183946570750754816",
                       "160317673761275904",
                       "144034766210072576",
                       "68801567083462656",
                       "162049755013316610",
                       "156748824151457794",
                       "205821019208941568",
                       "93872440244969472",
                       "87537114689830912",
                       "95305681195773952",
                       "184545248930693120",
                       "101680917696745472",
                       "253490275471589377",
                       "158428320306954241",
                       "126487183916793856",
                       "173936052384301056",
                       "137650741757083649",
                       "169377341498327040",
                       "144956126247649290",
                       "136295649162297344",
                       "117147763229065224",
                       "186932337638899712",
                       "109857471266324480",
                       "115221674202234881",
                       "123457920946929665",
                       "135256040995422208",
                       "150078752129417216",
                       "118490915303063560",
                       "114210244074274818",
                       "95228264330559488",
                       "112791848363233280",
                       "73877468049571840",
                       "136001883964702720",
                       "132833334010052608",
                       "178525596664594433",
                       "93915158941802496",
                       "126717367794270208",
                       "137821546935877633",
                       "139852743358545920",
                       "160048046707572737",
                       "94929759519125504",
                       "151815468447956992",
                       "145324949261910016",
                       "84805890837864448",
                       "150635259376041984",
                       "112069305943764992",
                       "197075867183218688",
                       "201895701754544128",
                       "106806056121831424",
                       "161630267579170816",
                       "76179896371523584",
                       "123490914202025986",
                       "109774565202198528",
                       "132583718291243008",
                       "149435714684059648",
                       "226088074004660226",
                       "96624561482661888",
                       "67340885968302080",
                       "207332555299487744",
                       "187727042324725761",
                       "110182909993857024",
                       "104078055512752128",
                       "228336202665820160",
                       "119560088858918914",
                       "80660666981027840",
                       "102801975027990528",
                       "83699343017644032",
                       "173125051141324801",
                       "165184478816239617",
                       "178226595440492544",
                       "107151789668737024",
                       "96360769649639424",
                       "178488257917616128",
                       "104297407851814912",
                       "140474849737834496",
                       "165970217913155584",
                       "106143363798941696",
                       "136288320010452992",
                       "99304728537632768",
                       "136412193657716736",
                       "116754222673821696",
                       "126586080312033280",
                       "135415664679583744",
                       "79030979460603904",
                       "140518194573082625",
                       "76741940430778368",
                       "99197585130016768",
                       "145704685414776833",
                       "128796210348687360",
                       "159692540356853760",
                       "143129212717367296",
                       "176751379216465921",
                       "152821379211722754",
                       "84707691540267008",
                       "113079057612099584",
                       "98721459785981952",
                       "187072095883231232",
                       "185183078031818752",
                       "167893876055474177",
                       "195692986997276672",
                       "101414608438329344",
                       "241058163997147136",
                       "103846266559025152",
                       "72351372850233344",
                       "110303345918382080",
                       "129014636208062464",
                       "179270125634060289",
                       "166021833999646720",
                       "101061290834812928",
                       "130011395830841344",
                       "165277505983479808",
                       "132070710888628225",
                       "110665114801143808",
                       "117877366058909696",
                       "229272373482881025",
                       "142797493229453312",
                       "91162857210671104",
                       "83630000862924800",
                       "143115977188442112",
                       "202060804571398144",
                       "251642929532239873",
                       "220971392412286977",
                       "149204733578575872",
                       "118005328368369671",
                       "135534799208185856",
                       "99445722755117056",
                       "142122918523043840",
                       "107393001692598272",
                       "108611736176726016",
                       "84595227507040256",
                       "163134261443035137",
                       "103205313959694336",
                       "179039204066459648",
                       "207588933108760578",
                       "131970466595340288",
                       "98173443148648448",
                       "94923289473843200",
                       "133525998074331136",
                       "98468183517712384",
                       "89544567396769792",
                       "174703904137805834",
                       "142827556654153728",
                       "161688157849518081",
                       "106082853095235584",
                       "122932725895135234",
                       "179038330011385856",
                       "126087122481315840",
                       "155518004220788736",
                       "99317156277149696",
                       "111231686703841280",
                       "108177792323047424",
                       "108218817531887616",
                       "124895958700916736",
                       "210615506602819585",
                       "121476579732881410",
                       "139699866304512000",
                       "123910998175252482",
                       "139720853205024768",
                       "126833303226548224",
                       "165458107567177729",
                       "121589951652560896",
                       "127558963662159872",
                       "114416332069535749",
                       "163935168019693568",
                       "105068196008038400",
                       "77462901991944192",
                       "210189533696884738",
                       "98420027597819904",
                       "147472828340502529",
                       "90892480274272256",
                       "205060188720332800",
                       "87595688522686464",
                       "156125759235162113",
                       "107383175910522880",
                       "154250474172710913",
                       "146475309913341952",
                       "107326404596600832",
                       "113388728692531200",
                       "124968503722770432",
                       "188737140635598849",
                       "101298502214111232",
                       "126849273408126977",
                       "184444131785965568",
                       "95711926088105984",
                       "145531137815478272",
                       "105954349158522880",
                       "192046696622981121",
                       "119900283647033345",
                       "87605824213487616",
                       "185031197066264576",
                       "197504503799349249",
                       "143294199087759361",
                       "128501195693096960",
                       "177748995819569153",
                       "154625491456884737",
                       "152243595913461760",
                       "95160622144040960",
                       "88932627783897088",
                       "156199526103908352",
                       "193255205716885504",
                       "135800085182283776",
                       "118509791088869384",
                       "153521590854877184",
                       "105383306639503360",
                       "174528518087114752",
                       "99555118994706432",
                       "101519575249600512",
                       "139804680392933376",
                       "182515752388132864",
                       "94228836647960576",
                       "110536138871037952",
                       "94966486602354688",
                       "105340789957128192",
                       "163706607467888640",
                       "183248671939362817",
                       "108748654063398912",
                       "114189757008838660",
                       "105268277374099456",
                       "154383355696119808",
                       "194821270792044544",
                       "103895807853367296",
                       "69295529682546688",
                       "138699676164685824",
                       "184411529326624768",
                       "167374068415201281",
                       "232993413270601728",
                       "91369770540097536",
                       "137428824777424897",
                       "133956589735510016",
                       "165936851855605761",
                       "95253010539622400",
                       "166324531567263744",
                       "78927997125529600",
                       "99862213468131328",
                       "114429598195908608",
                       "138864596843888641",
                       "160417252770840576",
                       "227906304134348802",
                       "97271805324050432",
                       "185429394515427328",
                       "211980236621873152",
                       "124397104910172162",
                       "117979871753273347",
                       "147158416018636800",
                       "191336710959923200",
                       "167328122436452354",
                       "109578882436313088",
                       "180805533438181386",
                       "147237543375536128",
                       "145641810062999552",
                       "177891965810114561",
                       "120943894861971459",
                       "83670697972363264",
                       "173112001684439040",
                       "152488725090271232",
                       "134904067431464960",
                       "85084994640310272",
                       "119019640721637377",
                       "85917489170497536",
                       "110770242183004160",
                       "104611507525926912",
                       "139903645239083008",
                       "98404146469699584",
                       "166289685918908427",
                       "168484999215972353",
                       "105320955575812096",
                       "106016555917176832",
                       "84463061313810432",
                       "147138778664796162",
                       "88471098894602240",
                       "242401395771179009",
                       "152352826532691968",
                       "59344382892969984",
                       "129319502155481088",
                       "161266025323692032",
                       "104143726653231104",
                       "95933768770019328",
                       "231715918680555521",
                       "196857580771999744",
                       "184453258885070848",
                       "132852917421080576",
                       "203687058521194506",
                       "109029220084117504",
                       "95106425797226496",
                       "88250015113297920",
                       "164912437215232001",
                       "128328596681916416",
                       "98895805334720512",
                       "154430201978290176",
                       "95525922760822784",
                       "95800047844757504",
                       "184898825016705024",
                       "250672792658378754",
                       "115596490298097671",
                       "183988939747622912",
                       "152943904134529024",
                       "147509586197348352",
                       "72651345726799872",
                       "141594018718023681",
                       "214123935107645440",
                       "92096085773815808",
                       "71831628665593856",
                       "149147592104738816",
                       "164452654561492992",
                       "159868294449463297",
                       "67448559443648512",
                       "145783191700111360",
                       "96399389550981120",
                       "143179748699275265",
                       "202277355845189633",
                       "159124215860166656",
                       "128526809456312320",
                       "145513216187826176",
                       "132437099130519552",
                       "90503528631525376",
                       "94555965663219712",
                       "98195448325496832",
                       "144710714236469248",
                       "98444456285437952",
                       "139623262509334529",
                       "106000931161640960",
                       "158281164056952842",
                       "85091960884322304",
                       "197091780171137034",
                       "126191293100457986",
                       "163686636062900224",
                       "167054113190838272",
                       "116332380934897670",
                       "143916701887496192",
                       "163067348553695232",
                       "179716866711879682",
                       "185721745041260545",
                       "109379094281453568",
                       "105869816824377344",
                       "135142432747683841",
                       "162129862037864448",
                       "95196666298109952",
                       "115313439362121732",
                       "188777348089249792",
                       "245929736625192962",
                       "189802533240176650",
                       "80825380654555136",
                       "194927585799569408",
                       "74856848741642240",
                       "154294750248173569",
                       "216641091334569984",
                       "143034011147698176",
                       "127029394526044160",
                       "203214550869213186",
                       "110429977471639552",
                       "158192639978504192",
                       "97443783448203264",
                       "205415475520208896",
                       "254425893320130562",
                       "122527086031142915",
                       "117758314053500929",
                       "138063196098527232",
                       "100991402237759488",
                       "227399467928649729",
                       "84975052033900544",
                       "71352139959504896",
                       "186951065491603457",
                       "108769797478551552",
                       "91227492488069120",
                       "103547212847403008",
                       "99354803666186240",
                       "116871398005276680",
                       "90974946393604096",
                       "154561783896473600",
                       "184311543536549892",
                       "118295338292477954",
                       "95370361582923776",
                       "103009487459205120",
                       "176160660294598656",
                       "117699617545650177",
                       "119926819376857088",
                       "155628147579158528",
                       "156531124007469056",
                       "131418423635738624",
                       "220053003028267009",
                       "168271319748706305",
                       "221406206701469726",
                       "75066151893204992",
                       "107313276177666048",
                       "80708383283347456",
                       "167063935244042250",
                       "114428165379588097",
                       "111828350732873728",
                       "172073220156030986",
                       "177272191132499980",
                       "136484106019012608",
                       "162056164408819713",
                       "77077128876662784",
                       "214629166853652480",
                       "72517917832380416",
                       "99522276164124672",
                       "151461035054858240",
                       "155529634128068608",
                       "205302290381275136",
                       "95932461950701568",
                       "196036502566731777",
                       "59290651522502656",
                       "154734618430406656",
                       "105471435161526272",
                       "152301951491637248",
                       "137539145877684224",
                       "123635249325277186",
                       "181450963247300608",
                       "98057256389586944",
                       "119596601378471936",
                       "144310685982130176",
                       "120732007088128002",
                       "75074727382614016",
                       "95599051671605248",
                       "148921289157902336",
                       "99906257254617088",
                       "148818547529744384",
                       "150987562272555008",
                       "109442166798974976",
                       "63102810157223936",
                       "228055028080836609",
                       "180041371544059905",
                       "93903410650157056",
                       "178240906019864586",
                       "59528604106629120",
                       "146976946025136129",
                       "210783145044213770",
                       "192340066759081995",
                       "108694032611295232",
                       "184050496393183232",
                       "149250276128194561",
                       "83616712825528320",
                       "84449657790398464",
                       "90159960096247808",
                       "243080047362179072",
                       "182733236617609217",
                       "109273029971832832",
                       "246810097672650754",
                       "155134866374131712",
                       "227098677691285504",
                       "178584118945120257",
                       "88783814083481600",
                       "198579391851134976",
                       "105817436393099264",
                       "172305829284806656",
                       "142666963531857921",
                       "109825246911033344",
                       "77816242232107008",
                       "111863568458080256",
                       "94961756908036096",
                       "82980808666644480",
                       "133215658421780480",
                       "96379394687246336",
                       "105317648602042368",
                       "217574496863780865",
                       "108225176373579776",
                       "184815893866479616",
                       "153340305402363907",
                       "110035681824256000",
                       "199147276306874368",
                       "105477020951031808",
                       "180392196229300224",
                       "148893301301313536",
                       "169726816804667393",
                       "90026239925956608",
                       "134042439668203520",
                       "174285859019816961",
                       "77556116539576320",
                       "253796868159569921",
                       "129656340305018880",
                       "102326409317355520",
                       "162252309592539136",
                       "107887227064852480",
                       "95449117693579264",
                       "137061372222504960",
                       "213631611386855424",
                       "92408544434860032",
                       "80125768578895872",
                       "168803596631146497",
                       "96706075880857600",
                       "175510279042367488",
                       "97860794582044672",
                       "107566269779152896",
                       "120945085301915648",
                       "91002347085381632",
                       "152879502236581888",
                       "238932185904709632",
                       "122948975551578112",
                       "184351086440742914",
                       "194294599840301056",
                       "83919836161245184",
                       "187414303077433344",
                       "95727801654579200",
                       "177317415598686208",
                       "58688906958209024",
                       "86267113357991936",
                       "108960882763014144",
                       "85134489314918400",
                       "96536042198306816",
                       "184841479166885888",
                       "117032512416382981",
                       "121805402550697986",
                       "89186236178112512",
                       "98953206570180608",
                       "150338902828253184",
                       "118219055579529216",
                       "232921983317180416",
                       "112514426199883776",
                       "168549116081602560",
                       "165453415546093568",
                       "111968444244635648",
                       "94542694088450048",
                       "107252404080082944",
                       "141296595927957504",
                       "184283232701906944",
                       "156598255579299841",
                       "93356136777912320",
                       "108168108425928704",
                       "80351110224678912",
                       "118957081524043781",
                       "81348401681137664",
                       "171685899728322560",
                       "176565268296761344",
                       "190941071507849216",
                       "95232952866185216",
                       "169346747276066816",
                       "86133824928378880",
                       "114144075736678404",
                       "193166016266633216",
                       "162455060758921216",
                       "77454100098199552",
                       "150003330666594304",
                       "122537595165999107",
                       "171332011091296256",
                       "96332834972643328",
                       "200235879057457152",
                       "160923942033293312",
                       "106180212634468352",
                       "120224688021438466",
                       "106585498641760256",
                       "73088747880587264",
                       "98136132973248512",
                       "151557210734854144",
                       "106802481773686784",
                       "125143058042978304",
                       "139917783566778368",
                       "141246600126267393",
                       "106640110992265216",
                       "181397691102789632",
                       "135843081743368192",
                       "114929816402132992",
                       "114596561492770820",
                       "99286051889115136",
                       "108983846103461888",
                       "222069903706947584",
                       "106542728422150144",
                       "95711937135902720",
                       "186187765803778048",
                       "143341356843139072",
                       "181076536550621184",
                       "203168106313547776",
                       "96091926939320320",
                       "96387369040617472",
                       "106468610137935872",
                       "186310020365811721",
                       "232636475521499136",
                       "213606417238589440",
                       "221294610465554432",
                       "141322289164713984",
                       "146113265682874368",
                       "131850489288589312",
                       "143899959312252929",
                       "158766059363500032",
                       "190200326828064768",
                       "108954815316373504",
                       "150362087560970240",
                       "210686726564347904",
                       "64443509599383552",
                       "95628557551673344",
                       "144456977697734656",
                       "123803760668573696",
                       "66156133177364480",
                       "95846866733780992",
                       "103248509930582016",
                       "139810062687272960",
                       "190388892799598592",
                       "167267037096181760",
                       "175380132188520449",
                       "186530332139323392",
                       "201802006824878081",
                       "215008292869505024",
                       "169703629375143936",
                       "243453080279056385",
                       "120713932171247617",
                       "211092576718028810",
                       "96355041333489664",
                       "116689392667590657",
                       "108580834935615488",
                       "121349649931042816",
                       "163983209921511425",
                       "180141263067021313",
                       "154012308744437760",
                       "122572254587518979",
                       "183457452686049280",
                       "232676552914108417",
                       "132347850171351041",
                       "207055652999135232",
                       "116448625508352005",
                       "181683645071884288",
                       "91964656372965376",
                       "109858105793236992",
                       "91379551371825152",
                       "136065357713506304",
                       "143494075973238786",
                       "186556433813209089",
                       "156984484263231490",
                       "71439435996069888",
                       "175661198878965760",
                       "156904467961217024",
                       "218094065760206848",
                       "108776499196252160",
                       "130867049781002240",
                       "95957160520855552",
                       "228962741384249344",
                       "178273269982560256",
                       "116851461018746881",
                       "163512069994315787",
                       "153362057176154112",
                       "84028227709861888",
                       "119887857107206147",
                       "200931208681619456",
                       "115208187803598857",
                       "188968114074025984",
                       "191689740066619393",
                       "105450167632711680",
                       "115104783282601992",
                       "109075873424003072",
                       "53259864956211200",
                       "235981720585895936",
                       "106234507203481600",
                       "77496745256300544",
                       "98101909759459328",
                       "183757399381901313",
                       "86103847876980736",
                       "190181644152471552",
                       "130800426156032000",
                       "165636323124838400",
                       "186970291648331779",
                       "102856793742389248",
                       "85075436026986496",
                       "105789297554149376",
                       "177823575917592576",
                       "158697523681165312",
                       "161184794833584128",
                       "119208246513762307",
                       "106260763328466944",
                       "95985604675764224",
                       "115534763044896775",
                       "129274884399300608",
                       "117882089184952321",
                       "162601401053085697",
                       "227905614037254152",
                       "206078670257913857",
                       "101841368434876416",
                       "178882398317051904",
                       "95077872254857216",
                       "111207943608791040",
                       "127874311330463744",
                       "159701274433028096",
                       "108551551026479104",
                       "120736687147057155",
                       "209319069797711872",
                       "103271239639920640",
                       "94894071062994944",
                       "163417864798208001",
                       "137114422626877440",
                       "119190566775947265",
                       "194543875744858112",
                       "182378504535539712",
                       "167490426503168000",
                       "85138387958239232",
                       "139391530053009408",
                       "176340260211392512",
                       "127498017677770752",
                       "194662591287525378",
                       "168177898354769920",
                       "153807321829605376",
                       "94923946306048000",
                       "110032483289968640",
                       "219194492077604865",
                       "111532106210951168",
                       "165666940268838914",
                       "68703007637770240",
                       "142509120526745600",
                       "179974082232713217",
                       "106907841029214208",
                       "81612562222821376",
                       "218466976945799168",
                       "177204012322390017",
                       "159858351772008449",
                       "122700807874412544",
                       "76753207858049024",
                       "143076224963444737",
                       "144663449413222400",
                       "218186666060414976",
                       "113329799803518976",
                       "165756211608813568",
                       "83267441961992192",
                       "234833368498307072",
                       "97770216372580352",
                       "215799666661523456",
                       "108273981655642112",
                       "171091864303304704",
                       "115569858724233216",
                       "105435316315254784",
                       "141485883621638144",
                       "162775656378138624",
                       "142432162346434560",
                       "146165452286984192",
                       "176071267525328906",
                       "224635834266025993",
                       "218576039876624384",
                       "190809188031528960",
                       "213315638507077632",
                       "108155495348461568",
                       "198604711878721536",
                       "122150539717771264",
                       "99932545348554752",
                       "123124171386388480",
                       "137932059812429824"]
                names = []
                for id in ids:
                    try:
                        info = await get_user_info(id)
                        name = info["names"][-1]
                        print("querying")
                    except:
                        print("reverting to server")
                        try:
                            name = message.server.get_member(id).name
                        except:
                            print("reverting to user")
                            try:
                                name = client.get_user_info(id).name
                            except:
                                name = id

                    names.append(name)
                gist = gistClient.create(name="Usernames",
                                         description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                         public=False,
                                         content=str(names))
                await client.send_message(message.channel, gist["Gist-Link"])
            if message.content.startswith("`mostactive"):
                print("STARTING")
                messagelist = []
                activity = defaultdict(int)
                count = 0
                async for mess in message_log_collection.find({"date": {"$gt": "2016-11-18"}}):
                    # async for mess in message_log_collection.find():
                    content = mess["content"]
                    length = len(content.split(" "))
                    activity[mess["userid"]] += length
                    # print(activity)
                    count += 1
                    print(count)
                    print("message found")

                activity = dict(activity)

                hist = ""
                newactivity = {}
                for id in activity.keys():
                    try:
                        info = await get_user_info(id)
                        name = info["names"][-1]
                        print("querying")
                    except:
                        print("reverting to server")
                        try:
                            name = message.server.get_member(id).name
                        except:
                            print("reverting to user")
                            try:
                                name = client.get_user_info(id).name
                            except:
                                name = id
                    newactivity[name] = activity[id]

                sort = sorted(newactivity.items(), key=lambda x: x[1])
                print(sort)
                hist = "\n".join("%s,%s" % tup for tup in sort)

                gist = gistClient.create(name="Userhist",
                                         description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                         public=False,
                                         content=hist)
                await client.send_message(message.channel, gist["Gist-Link"])
            if message.content.startswith("`channeldist"):
                command = message.content.replace("`channeldist ", "")
                command_list = command.split(" ")
                command_list = await mention_to_id(command_list)
                hist = defaultdict(int)

                async for doc in message_log_collection.find({"userid": command_list[0]}):
                    hist[doc["channel_id"]] += len(doc["content"].split(" "))
                named_hist = {}
                hist = dict(hist)
                for key in hist.keys():

                    try:
                        named_hist[constants.CHANNELID_CHANNELNAME_DICT[key]] = hist[key]
                    except:
                        try:
                            name = message.server.get_channel(key).name
                            named_hist[name] = hist[key]
                        except:
                            name = key
                            named_hist[name] = hist[key]

                sort = sorted(named_hist.items(), key=lambda x: x[1])
                print(sort)
                hist = "\n".join("%s,%s" % tup for tup in sort)

                gist = gistClient.create(name="Channelhist",
                                         description=str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")),
                                         public=False,
                                         content=hist)
                await client.send_message(message.channel, gist["Gist-Link"])

            if message.content.startswith("`linesplit"):
                command = message.content.replace("`linesplit ", "")
                command = command.split("\n")
                channel = message.channel
                await client.delete_message(message)
                for x in command:
                    await client.send_message(channel, x)
            if message.content.startswith("`wipemessages"):
                await message_log_collection.delete_many({})
                await message_log_collection.create_index(("message_id", pymongo.DESCENDING), unique=True)
            if message.content.startswith("`superlog"):
                server = message.server
                await client.delete_message(message)
                for channel in server.channels:
                    try:
                        count = 0
                        async for retrieved_message in client.logs_from(channel, limit=1000000000000):
                            if count % 100 == 0:
                                print("Message got " + str(count))
                            try:
                                await mongo_add_message_to_log(retrieved_message)
                            except pymongo.errors.DuplicateKeyError:
                                print("duplicate")
                            count += 1
                    except:
                        print(traceback.format_exc())
            # Clear Mongo Nick List
            if message.content.startswith("`clearnicks"):
                await clear_nicknames()
            elif message.content.startswith("`remindme"):
                command = message.content.replace("`remindme ", "")
                command_list = command.split(" | ", 1)
                await remind_me(command_list, message)
            # XKCD now
            elif message.content.startswith("`timenow"):
                redirected = await get_redirected_url("http://imgs.xkcd.com/comics/now.png")
                await client.send_message(message.channel, redirected)
                await client.delete_message(message)
            # Coroutine exec
            elif message.content.startswith("`exec_c"):
                input_command = message.content.replace("`exec_c ", "")
                command = ('try:\n'
                           '    import asyncio\n'
                           '    def do_task(message):\n'
                           '        asyncio.get_event_loop().create_task({command})\n'
                           '\n'
                           '    asyncio.get_event_loop().call_soon_threadsafe(do_task, message, client)\n'
                           'except RuntimeError:\n'
                           '    pass\n').format(command=input_command)
                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                response_str = None
                try:
                    exec(command)
                except Exception:
                    response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
                    response_str += traceback.format_exc()
                    response_str += "\n```"
                # finally:
                #     sys.stdout = old_stdout
                # if redirected_output.getvalue():
                #     response_str += redirected_output.getvalue()

                if response_str:
                    await client.send_message(message.channel, response_str)
            elif message.content.startswith("`exec_a"):
                input_command = message.content.replace("`exec_a ", "")
                command = ('try:\n'
                           '    import asyncio\n'
                           '    def do_task(message):\n'
                           '        {command}'
                           '\n'
                           '    asyncio.get_event_loop().call_soon_threadsafe(do_task, message)\n'
                           'except RuntimeError:\n'
                           '    pass\n').format(command=input_command)
                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                response_str = None
                try:
                    exec(command)
                except Exception:
                    response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
                    response_str += traceback.format_exc()
                    response_str += "\n```"
                # finally:
                #     sys.stdout = old_stdout
                # if redirected_output.getvalue():
                #     response_str += redirected_output.getvalue()

                if response_str:
                    await client.send_message(message.channel, response_str)
            elif message.content.startswith("`exec_n"):
                input_command = message.content.replace("`exec_n ", "")

                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                response_str = None
                try:
                    eval = aeval(input_command)
                    response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
                    # response_str += traceback.format_exc()

                finally:
                    sys.stdout = old_stdout
                if redirected_output.getvalue():
                    response_str += redirected_output.getvalue()
                    response_str += eval
                response_str += "\n```"
                if response_str:
                    await client.send_message(message.channel, response_str)
            # Wipe all gists
            elif message.content.startswith("`wipegists"):
                gist = gistClient.profile().list(30)
                for x in gist:
                    gistClient.profile().delete(id=x)
            # Have the bot say a command
            elif message.content.startswith("`say"):
                command = message.content.replace("`say ", "")
                command_list = command.split(" | ")
                await client.delete_message(message)
                if len(command_list) == 1:
                    await client.send_message(message.channel, command_list[0])
                else:
                    await client.send_message(message.channel_mentions[0], command_list[1])
            # Give a user perms
            elif "`auth" in message.content:
                command = message.content.replace("`auth ", "")
                command_list = command.split(" ")
                await client.delete_message(message)
                try:
                    await authorize_user(command_list)
                except:
                    print(traceback.format_exc())
            # NADIR PURGE
            elif "`clear" in message.content and message.server.id == "236343416177295360":
                await client.purge_from(message.channel)
            # Re-add all users to nickname database
            elif "`rebuildnicks" in message.content:
                memberlist = []
                for member in message.server.members:
                    memberlist.append(member)
                for member in memberlist:
                    try:
                        print(member.name)
                        await add_to_user_list(member)
                    except:
                        pass
            if message.content.startswith("`fixnicks"):
                cursor = userinfo_collection.find(
                    {"nicks": {"$exists": "false"}})
                id_list = {}
                async for nickless_user_info in cursor:
                    # print(nickless_user_info)
                    id_list[str(nickless_user_info["_id"])] = nickless_user_info["names"]
                    name = nickless_user_info["names"]
                    print(ascii(str(name)) + "    " + ascii(str(nickless_user_info["_id"])))
                print(ascii(id_list))
                print("\n\n\n\n\n")
                for x in id_list.keys():
                    try:
                        print(x + " is x")
                        result = await userinfo_collection.update_one(
                            {"_id": x},
                            {"$addToSet": {"nicks": {"$each": id_list[x]}}}, upsert=True
                        )
                        print(result.raw_result)
                    except:
                        print(traceback.format_exc())
            # Purge messages
            elif message.content.startswith("`purge"):
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
                                          "PURGING:\n" + str(await parse_message_info(message)))

                command = message.content.replace("`purge ", "")
                command_list = command.split(" ")
                command_list = await mention_to_id(command_list)
                number_to_remove = int(command_list[1])
                await client.delete_message(message)
                async for message in client.logs_from(message.channel):
                    print(number_to_remove)
                    print(command_list[0] + " " + command_list[1])
                    if message.author.id == command_list[0] and number_to_remove > 0:
                        await client.delete_message(message)
                        number_to_remove -= 1
                    else:
                        continue
            # Fully wipes a channel. Use with caution.
            if message.content.startswith("`fullpurge"):
                async for found_mess in client.logs_from(message.channel, limit=10000000):
                    await client.delete_message(found_mess)

        if "mod" in auths:
            # if message.content.startswith("`fixperms"):
            #     await initialize()
            #     black_voice_perms = discord.PermissionOverwrite()
            #     black_voice_perms.connect = False
            #     black_voice_perms.speak = False
            #     black_voice_perms.mute_members = False
            #     black_voice_perms.deafen_members = False
            #     black_voice_perms.move_members = False
            #     black_voice_perms.use_voice_activation = False
            #
            #     for channel in message.server.channels:
            #         if channel.type == discord.ChannelType.voice:
            #             await client.edit_channel_permissions(channel, ROLENAME_ROLE_DICT["MUTED_ROLE"],
            #                                                   overwrite=black_voice_perms)
            #             print("running")

            if message.content.startswith("`fixmsg"):
                await overwatch_db.message_log2.create_index([("message_id", pymongo.DESCENDING)], unique=True)
                cursor = overwatch_db.message_log.find()
                async for x in cursor:
                    try:
                        await overwatch_db.message_log2.insert_one(x)
                        print("added_one")
                    except:
                        print("duplicate")
                        pass
                # await overwatch_db.drop_collection("message_log")
                print("inserted new")
                await overwatch_db.message_log2.rename("message_log", dropTarget="message_log")
                await mongo_client.fsync()
                print("done")

            if message.content.startswith("`getroles"):
                await get_roles(message)

            if message.content.startswith("`moveafk"):
                command = message.content.replace("`moveafk ", "")
                command_list = await mention_to_id([command])
                target = message.server.get_member(command_list[0])
                afk = message.server.get_channel("94939166399270912")
                # print(afk.name)
                await client.move_member(target, afk)
            # Generate Join Link
            if "`join" == message.content[0:5]:
                command = message.content.replace("`join ", "")
                command_list = command.split(" ")
                VCMess = message
                instainvite = await get_vc_link(message)
                if instainvite:
                    VCInvite = await client.send_message(message.channel, instainvite)
                else:
                    await client.send_message(message.channel, "User not in a visible voice channel")
            # Fuzzy Nick Find
            if "`find" == message.content[0:5]:
                command = message.content[6:]
                command = command.lower()
                command = command.split("|", 2)
                await fuzzy_match(message, *command)
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
                                          "Fuzzysearch called by " + message.author.name + " on " + command)

            # Get previous nicknames
            if message.content.startswith("`getnicks"):
                command = message.content.strip("`getnicks ")
                nicklist = await get_previous_nicks(message.server.get_member(command))
                await client.send_message(message.channel, str(nicklist)[1:-1])
                pass
                # Reboot
            if "`reboot" == message.content and message.author.id == constants.ZENITH_ID:
                await client.send_message(message.channel, "Rebooting, " + message.author.mention)
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "Shut down by " + message.author.name)
                await client.logout()
            # Kill bot
            # if "`kill" == message.content:
            #     with open(PATHS["comms"] + "bootstate.txt", "w") as f:
            #         f.write("killed")
            #     await client.logout()
            # Get user logs
            if message.content.startswith("`userlogs"):
                command = message.content.replace("`userlogs ", "")
                command_list = command.split(" ")
                command_list = await mention_to_id(command_list)
                member = await client.get_user_info(command_list[0])
                logs = await get_user_logs(member, int(command_list[1]))
                gist = gistClient.create(name="User Log", description=member.name + "'s Logs", public=False,
                                         content="\n".join(logs))
                await client.send_message(message.channel, gist["Gist-Link"])
                await log_action_to_nadir(message=message, action_type="userlogs", target=member)
                # await client.edit_message(contextMess, gist["Gist-Link"])

            if message.content.startswith("`tag"):
                # command = message.content.replace("`blacklist ","")
                await tag_str(message)
            if message.content.startswith("`generate_veterans"):
                pass
            if message.content.startswith("`firstmsgs"):
                command = message.content.replace("`firstmsgs ", "")
                command_list = command.split(" ")
                command_list = await mention_to_id(command_list)
                member = await client.get_user_info(command_list[0])
                query_dict = {"userid": member.id}
                cursor = overwatch_db.message_log.find(query_dict, limit=50)
                cursor.sort("date", 1)
                message_list = []
                async for message_dict in cursor:
                    message_list.append(await message_to_log(message_dict))
                logs = message_list
                gist = gistClient.create(name="First Messages", description=member.name + "'s First Messages",
                                         public=False,
                                         content="\n".join(logs))
                await client.send_message(message.channel, gist["Gist-Link"])
                await log_action_to_nadir(message=message, action_type="userlogs", target=member)
        if "trusted" in auths:
            # User info
            if message.content.startswith("`ui"):
                try:
                    command_list = message.content.split(" ", 1)[1:]
                    command_list = await mention_to_id(command_list)
                    userid = command_list[0]
                except IndexError:
                    userid = message.author.id
                user_dict = await get_user_info(userid)
                if user_dict is not None:
                    formatted = [list(map(str, x)) for x in user_dict.items()]
                    text = await pretty_column(formatted, True)
                    # split = text.replace("\n", "|")
                    # split = split.replace(" ", "+")
                    # google_chart = "http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|12|h|FFFFFF|_|" + split
                    # await client.send_message(message.channel,google_chart)
                    await client.send_message(message.channel, "```\nFound:\n" + text + "```")
                    # for x in split:
                    # await client.send_message(message.channel,"`" + x + "`")
                    # await asyncio.sleep(20)
                    # await client.delete_message(ui_mess)
                else:
                    await client.send_message(message.channel, "User not found")
                return
            # Mention retrieval
            if "`getmentions" == message.content:
                if "mod" in auths:
                    await get_mentions(message, "mod")
                else:
                    await get_mentions(message, "trusted")
                return
            if message.content == "`ping":
                print("tester")
                await ping(message)
        if "warn" in auths:
            if message.content.startswith("`lfg"):
                found_message = None
                warn_user = None
                author = None
                if len(message.mentions) == 0:
                    found_message = await finder(message=message, regex=constants.LFG_REGEX, blacklist="mod")
                else:
                    warn_user = message.mentions[0]
                await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
                                          "`lfg called by " + message.author.name)
                await lfg_warner(found_message=found_message, warn_type="targeted", warn_user=warn_user,
                                 channel=message.channel)
                await client.delete_message(message)
        if "warn" in auths:
            if message.content.startswith("`hots"):
                hots_message = "Please keep Heroes of the Storm party-ups to <#247769594155106304>"
                author = await find_author(message=message, regex=constants.HOTS_REGEX, blacklist="mod")
                if author is not None:
                    hots_message += ", " + author.mention
                await client.send_message(message.channel, hots_message)
                await log_action_to_nadir(message=message, action_type="hots", target=author)
                await client.delete_message(message)
        # if "art" in auths:
        #     if message.content == "`getart" and False:
        #         await client.delete_message(message)
        #         art_channel = CHANNELNAME_CHANNEL_DICT["fanart"])
        #         rand_art = []
        #         count = 8
        #         with open(PATHS["comms"] + "auto_art_list.txt", "r+") as art_list:
        #             if len(art_list.readlines()) <= count:
        #                 link_list = [x.link for x in imgur.get_album_images("umuvY")]
        #                 random.shuffle(link_list)
        #                 for link in link_list:
        #                     art_list.write(link + "\n")
        #         with open(PATHS["comms"] + "auto_art_list.txt", "r") as art_list:
        #             for x in range(1, count):
        #                 line = art_list.readline()
        #                 rand_art.append(line)
        #         await delete_lines(PATHS["comms"] + "auto_art_list.txt", count)
        #         for artlink in rand_art:
        #             await client.send_message(art_channel, artlink)
        #     if message.content.startswith("`flagart"):
        #         command = message.content.replace("`flagart ", "")
        #         imgur_id_reg = re.compile("(?<=http://i.imgur.com/)(\w+)", re.IGNORECASE)
        #         match = imgur_id_reg.search(command)
        #         if "zenith" in auths:
        #             if match is not None:
        #                 imgur_id = match.group(0)
        #                 imgur.delete_image(imgur_id)
        #                 log_action_to_nadir(message, "flagart", target=imgur_id)
        #         found_message = await finder(message, command, "none")
        #         if message is not None:
        #             await client.delete_message(found_message)

        if "mod" not in auths:
            # EXTRA-SERVER INVITE CHECKER
            if "chaos vanguard" in message.content.lower():
                await log_automated("logged a message containing Chaos Vanguard in " + message.channel.name + ":\n[" +
                                    message.author.name + "]: " + message.content)
                # await client.delete_message(message)
                skycoder_mess = await client.send_message(
                    CHANNELNAME_CHANNEL_DICT["spam-channel"],
                    "~an " + message.author.mention +
                    " AUTOMATED: Posted a message containing chaos vanguard: " + message.content)
            if message.channel.id not in BLACKLISTED_CHANNELS:
                match = constants.LINK_REGEX.search(message.content)
                if match is not None:
                    await invite_checker(message, match)
                    # LFG -> Audit
                    # if message.channel.id == constants.CHANNELNAME_CHANNELID_DICT["general-discussion"]:
                    #     match = constants.LINK_REGEX.search(message.content)
                    #     if match is not None:
                    #         await client.send_message(client.get_channel(constants.NADIR_AUDIT_LOG_ID), message.content)
                    #         await invite_checker(message, match)


async def find_author(message, regex, blacklist):
    author = None
    if len(message.mentions) > 0:
        author = message.mentions[0]
    else:
        found_mess = await finder(message, regex, blacklist)
        if found_mess is not None:
            author = found_mess.author
    return author


#
# @client.event
# async def on_message(mess):
#     """
#     Called on client message reception
#     :type mess: discord.Message
#     """
#     global VCMess
#     global VCInvite
#     global PATHS
#     global ENABLED
#     if not ENABLED:
#         return
#     # Not a PM
#     if mess.server is None:
#         await client.send_message(client.get_user(constants.ZENITH_ID), "[" + mess.author.name + "]: " + mess.content)
#     if mess.server is not None:
#         if not INITIALIZED and mess.server.id == constants.OVERWATCH_SERVER_ID:
#             await initialize()
#
#         if mess.channel.id not in BLACKLISTED_CHANNELS:
#             await mongo_add_message_to_log(mess)
#
#         if mess.content == "`getart":
#             if await credential(mess.author, "get_art"):
#                 await client.delete_message(mess)
#                 art_channel = CHANNELNAME_CHANNEL_DICT["fanart"])
#                 rand_art = []
#                 count = 8
#                 with open(PATHS["comms"] + "auto_art_list.txt", "r+") as art_list:
#                     if len(art_list.readlines()) <= count:
#                         link_list = [x.link for x in imgur.get_album_images("umuvY")]
#                         random.shuffle(link_list)
#                         for link in link_list:
#                             art_list.write(link + "\n")
#                 with open(PATHS["comms"] + "auto_art_list.txt", "r") as art_list:
#                     for x in range(1, count):
#                         line = art_list.readline()
#                         rand_art.append(line)
#                 await delete_lines(PATHS["comms"] + "auto_art_list.txt", count)
#
#                 for artlink in rand_art:
#                     await client.send_message(art_channel, artlink)
#         if mess.content.startswith("`flagart"):
#             command = mess.content.replace("`flagart ", "")
#             imgur_id_reg = re.compile("(?<=http://i.imgur.com/)(\w+)", re.IGNORECASE)
#             match = imgur_id_reg.search(command)
#             if await credential(mess.author, "zenith"):
#                 if match is not None:
#                     imgur_id = match.group(0)
#                     imgur.delete_image(imgur_id)
#
#             message = await finder(mess, command, "none")
#             print(message.content)
#             if message is not None:
#                 await client.delete_message(message)
#         # AUTHOR-ONLY
#         if await credential(mess.author, "zenith"):
#             if mess.content.startswith("`clearnicks"):
#                 result = await userinfo_collection.update_many(
#                     {},
#                     {"$unset": {"nicks": ""}}
#                 )
#                 return
#             if mess.content.startswith("`remindme"):
#                 command = mess.content.replace("`remindme ", "")
#                 command_list = command.split(" | ", 1)
#                 print(command_list)
#                 try:
#                     time = int(aeval(command_list[1]))
#                     # time = int(command[0])
#                     await asyncio.sleep(time)
#                     await client.send_message(mess.channel, "Reminding " + mess.author.mention + " after " + str(
#                         time) + " seconds:\n" + command_list[0])
#                 except:
#                     print(traceback.format_exc())
#
#             if mess.content.startswith("`timenow"):
#                 redirected = await get_redirected_url("http://imgs.xkcd.com/comics/now.png")
#                 await client.send_message(mess.channel, redirected)
#                 await client.delete_message(mess)
#             if mess.content.startswith("`aex"):
#                 print("EXECUTING")
#                 input_command = mess.content.replace("`aex ", "")
#                 command = ('try:\n'
#                            '    import asyncio\n'
#                            '    def do_task(message):\n'
#                            '        asyncio.get_event_loop().create_task({command})\n'
#                            '\n'
#                            '    asyncio.get_event_loop().call_soon_threadsafe(do_task, mess)\n'
#                            'except RuntimeError:\n'
#                            '    pass\n').format(command=input_command)
#
#                 old_stdout = sys.stdout
#                 redirected_output = sys.stdout = StringIO()
#                 response_str = "```py\nInput:\n" + input_command + "\nOutput:\n"
#                 try:
#                     exec(command)
#                 except Exception:
#                     response_str += traceback.format_exc()
#                 finally:
#                     sys.stdout = old_stdout
#                 if redirected_output.getvalue():
#                     response_str += redirected_output.getvalue()
#                 response_str += "\n```"
#                 await client.send_message(mess.channel, response_str)
#             if mess.content.startswith("`wipegists"):
#                 gist = gistClient.profile().list(30)
#                 for x in gist:
#                     gistClient.profile().delete(id=x)
#
#             if mess.content.startswith("`say"):
#                 command = mess.content.replace("`say ", "")
#                 command_list = command.split(" | ")
#                 channel = mess.channel
#                 channel_mentions = mess.channel_mentions
#                 await client.delete_message(mess)
#                 if len(command_list) == 1:
#                     await client.send_message(channel, command_list[0])
#                 else:
#                     await client.send_message(channel_mentions[0], command_list[1])
#             if "`auth" in mess.content:
#                 command = mess.content.replace("`auth ", "")
#                 command_list = command.split(" ")
#                 await client.delete_message(mess)
#                 try:
#                     await authorize_user(command_list)
#                 except:
#                     print(traceback.format_exc())
#             # NADIR PURGE
#             if "`clear" in mess.content and mess.server.id == "236343416177295360":
#                 await client.purge_from(mess.channel)
#             if "`rebuildnicks" in mess.content:
#                 memberlist = []
#                 for member in mess.server.members:
#                     memberlist.append(member)
#                 for member in memberlist:
#                     try:
#                         print(member.name)
#                         await add_to_user_list(member)
#                     except:
#                         pass
#             if mess.content.startswith("`purge"):
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
#                                           "PURGING:\n" + str(await parse_message_info(mess)))
#
#                 command = mess.content.replace("`purge ", "")
#                 command_list = command.split(" ")
#                 number_to_remove = int(command_list[1])
#                 await client.delete_message(mess)
#                 async for message in client.logs_from(mess.channel):
#                     print(number_to_remove)
#                     print(command_list[0] + " " + command_list[1])
#                     if message.author.id == command_list[0] and number_to_remove > 0:
#                         await client.delete_message(message)
#                         number_to_remove -= 1
#                     else:
#                         return
#         # BLACK-LIST MODS
#         if mess.author.id != constants.MERCY_ID and not await credential(mess.author, "trusted"):
#             # EXTRA-SERVER INVITE CHECKER
#             if mess.channel.id not in BLACKLISTED_CHANNELS:
#                 match = constants.LINK_REGEX.search(mess.content)
#                 if match is not None:
#                     await invite_checker(mess, match)
#             # LFG -> Audit
#             if mess.channel.id == constants.CHANNELNAME_CHANNELID_DICT["general-discussion"]:
#                 match = constants.LFG_REGEX.search(mess.content)
#                 if match is not None:
#                     await client.send_message(client.get_channel(constants.NADIR_AUDIT_LOG_ID), mess.content)
#                     # match = linkReg.search(mess.content)
#                     # if match is not None:
#                     #     print("FOUND ONE")
#                     #     await invite_checker(mess, match)
#
#         if mess.content.startswith("`hots") and mess.author.id != constants.MERCY_ID and await credential(mess.author,
#                                                                                                           "hots"):
#             hots_message = "Please keep Heroes of the Storm party-ups to <#247769594155106304>"
#             author = None
#             if len(mess.mentions) > 0:
#                 author = mess.mentions[0]
#             else:
#                 HOTS_REGEX = re.compile(r"(heroes of the storm)|(storm)|(heros)|(hots)|(heroes)|(genji)|(oni)",
#                                         re.IGNORECASE)
#                 found_mess = await finder(mess, HOTS_REGEX, "mod")
#                 if found_mess is not None:
#                     author = found_mess.author
#             if author is not None:
#                 hots_message += ", " + author.mention
#             hots_warn = await client.send_message(mess.channel, hots_message)
#             await client.delete_message(mess)
#             # await asyncio.sleep(10)
#             # await client.delete_message(hots_warn)
#         # WHITE-LIST TRUSTED
#
#         if mess.author.id != constants.MERCY_ID and await credential(mess.author, "trusted"):
#
#             # Gets banned userinfo dict
#             if "`ui" in mess.content:
#                 try:
#                     command_list = mess.content.split(" ", 1)[1:]
#                     command_list = await mention_to_id(command_list)
#                     command = command_list[0]
#                 except IndexError:
#                     command = mess.author.id
#                 user_dict = await get_user_info(command)
#                 if user_dict is not None:
#                     formatted = [list(map(str, x)) for x in user_dict.items()]
#                     await client.send_message(mess.channel,
#                                               "```Found:\n" + await pretty_column(formatted, True) + "\n```")
#                 else:
#                     await client.send_message(mess.channel, "User not found")
#                 return
#
#             # Get Mentions
#             if "`getmentions" == mess.content:
#                 await get_mentions(mess)
#                 return
#                 # Call LFG autowarn
#         if mess.author.id != constants.MERCY_ID and await credential(mess.author, "lfg"):
#             if '`lfg' == mess.content[0:4]:
#                 found_mess = None
#                 author = None
#                 if len(mess.mentions) > 0:
#                     author = mess.mentions[0]
#                 else:
#                     found_mess = await finder(mess, constants.LFG_REGEX, "mod")
#                     if found_mess is not None:
#                         print("Found a message!")
#                         print(found_mess.content + " " + found_mess.author.name)
#                         author = found_mess.author
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "`lfg called by " + mess.author.name)
#
#                 await client.delete_message(mess)
#                 await lfg_warner(found_message=found_mess, warn_type="targeted", warn_user=author, channel=mess.channel)
#                 # Ping bot
#         if "`ping" == mess.content or mess.content == "<@!236341193842098177>":
#             await ping(mess)
#
#         if mess.author.id != constants.MERCY_ID and await credential(mess.author, "mod"):
#             # Generate Join Link
#             if "`join" == mess.content[0:5]:
#                 VCMess = mess
#                 instainvite = await get_vc_link(mess)
#                 VCInvite = await client.send_message(mess.channel, instainvite)
#             # Fuzzy Nick Find
#             if "`find" == mess.content[0:5]:
#                 command = mess.content[6:]
#                 command = command.lower()
#                 command = command.split("|", 2)
#                 await fuzzy_match(mess, *command)
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID),
#                                           "Fuzzysearch called by " + mess.author.name + " on " + mess.author.name)
#
#             # Get previous nicknames
#             if mess.content.startswith("`getnicks"):
#                 command = mess.content.strip("`getnicks ")
#                 nicklist = await get_previous_nicks(mess.server.get_member(command))
#                 await client.send_message(mess.channel, str(nicklist)[1:-1])
#                 pass
#             # Kill Bot
#             if "`reboot" == mess.content:
#                 await client.send_message(mess.channel, "Rebooting, " + mess.author.mention)
#                 await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), "Shut down by " + mess.author.name)
#                 await client.logout()
#             if "`kill" == mess.content:
#                 with open(PATHS["comms"] + "bootstate.txt", "w") as f:
#                     f.write("killed")
#                 client.logout()
#             # Get user logs
#             if mess.content.startswith("`userlogs"):
#                 command = mess.content.replace("`userlogs ", "")
#                 command_list = command.split(" ")
#                 command_list = await mention_to_id(command_list)
#                 member = mess.server.get_member(command_list[0])
#                 logs = await get_user_logs(member, int(command_list[1]))
#                 gist = gistClient.create(name="User Log", description=member.name + "'s Logs", public=False,
#                                          content="\n".join(logs))
#                 await client.send_message(mess.channel, gist["Gist-Link"])
#                 await log_action_to_nadir(message=mess, action_type="userlogs", *(member))
#                 # await client.edit_message(contextMess, gist["Gist-Link"])


async def log_action_to_nadir(message, action_type, target):
    text = "a"
    if action_type == "userlogs" or action_type == "hots":
        text = "Userlogs called by " + message.author.name + " on " + target.name
    elif action_type == "reboot":
        text = "Rebooted by " + message.author.name
    elif action_type == "flagart":
        text = "Art flagged " + target
    await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), text)


async def on_message_edit(before, after):
    auths = await get_auths(after.author)
    if "mod" not in auths:
        # EXTRA-SERVER INVITE CHECKER
        if "chaos vanguard" in after.content.lower():
            await log_automated("logged a message containing Chaos Vanguard in " + after.channel.name + ":\n[" +
                                after.author.name + "]: " + after.content)
            # await client.delete_message(message)
            skycoder_mess = await client.send_message(
                CHANNELNAME_CHANNEL_DICT["spam-channel"],
                "~an " + after.author.mention +
                " AUTOMATED: Posted a message containing chaos vanguard: " + after.content)
        if after.channel.id not in BLACKLISTED_CHANNELS:
            match = constants.LINK_REGEX.search(after.content)
            if match is not None:
                await invite_checker(after, match)


# noinspection PyBroadException
async def invite_checker(message, regex_match):
    """

    :type regex_match: re.match
    :type message: discord.Message
    """
    try:
        print("matchgrp = " + str(regex_match.group(1)))
        invite = await client.get_invite(str(regex_match.group(1)))
        if invite.server.id != constants.OVERWATCH_SERVER_ID:
            channel = message.channel
            # await client.send_message(mess.channel, serverID + " " + OVERWATCH_ID)
            warn = await client.send_message(message.channel,
                                             "Please don't link other discord servers here " +
                                             message.author.mention + "\n" +
                                             message.server.get_member(constants.ZENITH_ID).mention)
            await client.delete_message(message)

            await log_automated("deleted an external invite: " + str(
                invite.url) + " from " + message.author.mention + " in " + message.channel.mention)
            skycoder_mess = await client.send_message(
                CHANNELNAME_CHANNEL_DICT["spam-channel"],
                "~an " + message.author.mention +
                " AUTOMATED: Posted a link to another server")
            await client.send_message(skycoder_mess.channel, "~rn " + message.author.mention)
        elif message.channel == CHANNELNAME_CHANNEL_DICT["general-discussion"]:

            channel_name = invite.channel.name
            party_vc_reg = re.compile(r"(^\[)\w+.\w+\]", re.IGNORECASE)
            match = party_vc_reg.search(channel_name)
            if match is not None:
                print("channelname = " + message.channel.name)
                await lfg_warner(found_message=message, warn_type="automated", warn_user=message.author,
                                 channel=message.channel)
                await client.delete_message(message)
    except discord.errors.NotFound:
        pass
    except:
        print(traceback.format_exc())


# noinspection PyPep8Naming
async def get_vc_link(mess):
    """

    :type mess: discord.Message
    """
    command = mess.content.replace("`join", "")
    if command[0:1] == " ": command = command[1:]
    print(command)
    if len(command) == 0:
        userID = await get_from_find(mess)
        print("userid = " + userID)
    else:
        # print("command list = " + str(command_list))
        command_list = await mention_to_id([command])
        userID = command_list[0]
    print("TYPE = " + userID)
    mentionedUser = mess.server.get_member(userID)
    try:
        vc = mentionedUser.voice.voice_channel
        instaInvite = await client.create_invite(vc, max_uses=1, max_age=6)
        return instaInvite.url
    except AttributeError:
        return None


async def mention_to_id(command_list):
    """

    :type command: list
    """
    new_command = []
    reg = re.compile(r"<@(!?)\d*>", re.IGNORECASE)
    for item in command_list:
        match = reg.search(item)
        if match is None:
            print("no match found")
            new_command.append(item)
        else:
            idmatch = re.compile(r"\d")
            id_chars = "".join(idmatch.findall(item))
            print("id chars")
            print(id_chars)
            new_command.append(id_chars)
    print(new_command)
    return new_command


async def log_automated(description: object) -> None:
    action = ("At " + str(datetime.utcnow().strftime("[%Y-%m-%d %H:%m:%S] ")) + ", I automatically " +
              str(description) + "\n" + "`kill to disable me")
    await client.send_message(CHANNELNAME_CHANNEL_DICT["alerts"], action)
    # await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), action)


#
# async def command_info(*args):
#     info_list = []
#     if len(args) == 2:
#         info_list = [
#             ["Command ", "Description ", "Usage"],
#             ["<Trusted>,", " ", " "],
#             ["`ui", "Retrieves user info", "`ui *<user>"],
#             ["`getmentions", "Mention retrieval", "`getmentions"],
#             ["`lfg", "Automated lfg logger and copypasta warning", "`lfg *<user>"],
#             ["`ping", "Gets a random mercy voice-line and bot ping", "`ping"],
#             ["`userlogs", "Gets logs from a user", "`userlogs <user> <count>"],
#             [" ", " ", " "],
#
#         ]
#         if await credential(args[0].author, "mod"):
#             info_list.append(["<Moderator>", " ", " "])
#             info_list.append(["`kill", "Disconnects bot", "`kill"])
#             info_list.append(["`join", "Gets an invite for a user's current VC", "`join <user>"])
#             info_list.append(["`find", "Finds users that have had similar nicknames", "`find <nick>|<count>"])
#             info_list.append(["`getnicks", "Gets the previous nicknames of a user", "`getnicks <id>"])
#     await client.send_message(args[0].channel, "```prolog\n" + await pretty_column(info_list, True) + "```")


async def ping(message):
    # lag = (datetime.utcnow() - message).timestamp.total_seconds() * 1000) + " ms")
    """
    :type message: discord.Message
    """

    timestamp = message.timestamp
    channel = message.channel

    await client.delete_message(message)
    voice = random.choice(constants.VOICE_LINES)
    sent = await client.send_message(channel, voice)
    await client.edit_message(sent,
                              voice + " (" + str(
                                  (sent.timestamp - timestamp).total_seconds() * 500) + " ms) " +
                              message.author.mention)


async def fuzzy_match(*args):
    if len(args) == 2:
        count = 1
    else:
        count = args[2]
    nick_to_find = args[1]
    mess = args[0]

    # cursor = database.cursor()
    # cursor.execute('SELECT userid,nickname FROM useridlist')
    # nickIdList = cursor.fetchall()
    nick_id_dict = {}

    mongo_cursor = userinfo_collection.find()
    async for userinfo_dict in mongo_cursor:
        try:
            for nick in userinfo_dict["nicks"]:
                # print(userinfo_dict["nicks"])
                nick_id_dict.setdefault(nick, []).append(userinfo_dict["userid"])
                # nickIdDict.setdefault(nick, []).append(id)
        except KeyError:
            try:
                await add_to_user_list(
                    SERVERS["OW"].get_member(userinfo_dict["userid"]))
            except:
                pass
    print("DONE")

    # for id, nick in nickIdList:
    #     nickIdDict.setdefault(nick, []).append(id)

    # noinspection PyUnusedLocal
    nick_fuzz = {}

    for nick in nick_id_dict.keys():
        ratio = fuzz.ratio(nick_to_find, str(nick))
        nick_fuzz[str(nick)] = int(ratio)

    top_nicks = heapq.nlargest(int(count), nick_fuzz, key=lambda k: nick_fuzz[k])
    message_to_send = "`Fuzzy Search:`\n"
    pretty_list = []
    for nick in top_nicks:
        user_id = nick_id_dict[nick]

        for singleID in user_id:
            pretty_list.append(["`ID: '" + str(singleID) + "'",
                                "| Nickname: " + nick,
                                " (" + str(nick_fuzz[nick]) + ")",
                                "` | " + "<@!" + singleID + ">"])

    message_to_send += await pretty_column(pretty_list, True)
    await client.send_message(mess.channel, message_to_send)


async def get_from_find(message):
    reg = re.compile(r"(?!ID: ')(\d+)(?=')", re.IGNORECASE)
    user_id = ""
    async for mess in client.logs_from(message.channel, limit=10):
        if "Fuzzy Search:" in mess.content:
            match = reg.search(mess.content)
            if match is not None:
                user_id = match.group(0)
    return user_id


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
                # auth = await credential(messageCheck.author, "mod")
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


    # noinspection PyBroadException


# (found_message=found_message, warn_type="targeted", warn_user=warn_user
async def lfg_warner(found_message, warn_type, warn_user, channel):
    """

    :param channel: discord.Channel
    :param warn_user: discord.Member
    :param found_message: discord.Message
    :type warn_type: str
    """

    lfg_text = ("You're probably looking for <#182420486582435840> or <#185665683009306625>."
                " Please avoid posting LFGs in ")
    if found_message:
        author = found_message.author
        channel = found_message.channel
    else:
        author = warn_user
        channel = channel
    lfg_text += channel.mention
    author_mention = ""
    count = 0
    try:
        count = await increment_lfgd_mongo(author)
        author_mention += ", " + author.mention + " (" + str(count) + ")"
    except:
        print(traceback.format_exc())

    if warn_type == "automated":
        print("AUTOMATED")
        # noinspection PyPep8
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])
        ordinal_count = ordinal(count)
        await log_automated(
            "warned " + author.mention + " in " + found_message.channel.mention + " for the " + ordinal_count + " time because of the message\n" +
            found_message.content)

    lfg_text += author_mention
    await client.send_message(channel, lfg_text)


async def get_user_logs(member, count):
    """

    :type count: int
    :type member: discord.Member
    """
    query_dict = {"userid": member.id}
    cursor = overwatch_db.message_log.find(query_dict, limit=count)
    cursor.sort("date", -1)
    message_list = []
    count = 0
    async for message_dict in cursor:
        if count % 500 == 0:
            print(count)
        count += 1
        message_list.append(await message_to_log(message_dict))
    return message_list


async def message_to_log(message_dict):
    cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
    try:
        name = cursor["names"][-1]
    except:
        try:
            await add_to_user_list(SERVERS["OW"].get_member(message_dict["userid"]))
            cursor = await overwatch_db.userinfo.find_one({"userid": message_dict["userid"]})
            name = cursor["names"][-1]

        except:
            name = cursor["userid"]

            return

    content = message_dict["content"].replace("```", "")
    try:
        channel_name = constants.CHANNELID_CHANNELNAME_DICT[str(message_dict["channel_id"])]
    except KeyError:
        channel_name = "Unknown"
    return "[" + message_dict["date"][:19] + "][" + channel_name + "][" + name + "]:" + \
           content


async def get_logs_mentions_2(query_type, message):
    await log_action_to_nadir(message, "logs", message.author)
    author_info = await parse_member_info(message.server.get_member(message.author.id))
    target = message.author
    if query_type == "1":
        cursor = overwatch_db.message_log.find({"mentioned_users": author_info["id"]})
    elif query_type == "2":
        cursor = overwatch_db.message_log.find({"mentioned_roles": {"$in": author_info["role_ids"]}})
    else:  # query_type == "3":
        cursor = overwatch_db.message_log.find(
            {"$or": [{"mentioned_users": author_info["id"]}, {"mentioned_roles": {"$in": author_info["role_ids"]}}]})


async def get_logs_mentions(query_type, mess):
    """
    :type query_type: Integer
    :type mess: discord.Message
    """
    try:
        await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(await parse_message_info(mess)))
    except:
        await client.send_message(client.get_channel(BOT_HAPPENINGS_ID), str(traceback.format_exc()))
    mess_info = await parse_message_info(mess)
    target = mess.author
    author_info = await parse_member_info(mess.server.get_member(mess.author.id))
    cursor = None
    if query_type == "1":
        cursor = overwatch_db.message_log.find({"mentioned_users": author_info["id"]})
    elif query_type == "2":
        cursor = overwatch_db.message_log.find({"mentioned_roles": {"$in": author_info["role_ids"]}})
    else:  # query_type == "3":
        cursor = overwatch_db.message_log.find(
            {"$or": [{"mentioned_users": author_info["id"]}, {"mentioned_roles": {"$in": author_info["role_ids"]}}]})

    # await client.send_message(target, "DEBUG: Query Did Not Fail!")
    number_message_dict = {}
    count = 1
    cursor.sort("date", -1)
    message_choices_text = "```\n"
    await client.send_message(target, "Retrieving Messages! (0) to get more messages!")
    mention_choices_message = await client.send_message(target, "Please wait...")
    response = 0
    async for message_dict in cursor:
        # user_info = await parse_member_info(target.server.get_member(message_dict["userid"]))
        # await client.send_message(target, "DEBUG: FOUND MATCH! " + message_dict["content"])
        number_message_dict[count] = message_dict
        message_choices_text += "(" + str(count) + ")" + await message_to_log(message_dict) + "\n"
        if count % 5 == 0:
            message_choices_text += "\n```"
            try:
                await client.edit_message(mention_choices_message, message_choices_text)
            except discord.errors.HTTPException:
                # message_choices_text
                await client.send_message(target, message_choices_text)
            response = await get_response_int(target)
            if response is None:
                await client.send_message(target, "You have taken too long to respond! Please restart.")
                return
            elif response.content == "0":
                count = 1
                message_choices_text = message_choices_text[:-4]
                continue
            else:
                break
        count += 1
    try:

        if response.content == "0":
            await client.send_message(target,
                                      "You have no (more) logged mentions!")
            response = await get_response_int(target)
        selected_message = number_message_dict[int(response.content)]
        await client.send_message(target, " \n Selected Message: \n[" + await message_to_log(selected_message))
        await client.send_message(target,
                                  "\n\n\n\nHow many messages of context would you like to retrieve? Enter an integer")
        response = await get_response_int(target)
        response = int(response.content)
        # print("Response = " + str(response))
        cursor = overwatch_db.message_log.find(
            {
                "date": {"$lt": selected_message["date"]},
                "channel_id": selected_message["channel_id"]
            }, limit=response
        )
        cursor.sort("date", -1)
        contextMess = await client.send_message(target, "Please wait...")
        contextContent = ""

        async for message_dict in cursor:
            try:
                # print("DEBUG: FOUND MATCH! " + message_dict["content"])
                user_info = await parse_member_info(
                    (client.get_server(message_dict["server_id"])).get_member(message_dict["userid"])
                )
                contextContent += "[" + message_dict["date"][:19] + "][" + user_info["name"] + "]: " + message_dict[
                    "content"] + "\n"
            except:
                pass

        gist = gistClient.create(name="M3R-CY Log", description=selected_message["date"], public=False,
                                 content=contextContent)
        await client.edit_message(contextMess, gist["Gist-Link"])


    except ValueError as e:
        await client.send_message(target, "You entered something wrong! Oops!")
        print(traceback.format_exc())
    except TypeError as e:
        await client.send_message(target, "You entered something wrong! Oops!")
        print(traceback.format_exc())
    pass


async def mongo_add_message_to_log(mess):
    messInfo = await parse_message_info(mess)
    result = await message_log_collection.insert_one(messInfo)
    # messText = await message_to_log(messInfo)
    # await message_to_stream(messInfo)
    # await client.send_message(STREAM, await message_to_stream(messInfo))


async def message_to_stream(mess_dict):
    string = ""
    string += "`<" + mess_dict["date"][:-7] + ">` "
    string += "**[" + constants.CHANNELID_CHANNELNAME_DICT[str(mess_dict["channel_id"])] + "]** "

    item = await get_user_info(mess_dict["userid"])
    string += "[" + item["nicks"][-1] + "]: "

    string += ":small_blue_diamond:" + mess_dict["content"]

    # await stream.add(string=string)
    return string


async def increment_lfgd_mongo(author):
    """

    :type author: discord.Member
    """
    result = await userinfo_collection.find_one_and_update(
        {"userid": author.id},
        {"$inc": {
            "lfg_count": 1
        }}, upsert=True, return_document=ReturnDocument.AFTER),
    return result[0]["lfg_count"]


async def add_to_user_set(member, set_name, entry):
    """

    :type entry: str
    :param set_name: str
    :type member: discord.Member
    """
    user_info = await parse_member_info(member)
    result = await userinfo_collection.update_one(
        {"userid": user_info["id"]},
        {
            "$addToSet": {set_name: entry}
        }
    )


async def add_to_user_list(member):
    """

    :type member: discord.Member
    """
    user_info = await parse_member_info(member)
    result = await userinfo_collection.update_one(
        {"userid": member.id},
        {
            "$addToSet": {"nicks": {
                "$each": [user_info["nick"], user_info["name"], user_info["name"] + "#" + str(user_info["discrim"])]},
                "names": user_info["name"],
                "avatar_urls": user_info["avatar_url"],
                "server_joins": user_info["joined_at"]},
            "$set": {"mention_str": user_info["mention_str"],
                     "created_at": user_info["created_at"]},

        }
        , upsert=True
    )
    # print(result.raw_result)
    pass


async def get_previous_nicks(member) -> list:
    """
paste
    :type member: discord.Member
    """
    userinfo_dict = await userinfo_collection.find_one({"userid": member.id})
    return list(userinfo_dict["nicks"])


async def shorten_link(link) -> str:
    return Shortener('Tinyurl').short(link)


scrim = None


async def scrim_end():
    global scrim
    await scrim.end()
    scrim = None


async def get_roles(message):
    message_list = []
    role_list = []
    role_list.append(["Name", "ID", "Position", "Color", "Hoisted", "Mentionable"])
    widths = None
    for role in message.server.role_hierarchy:
        old_list = role_list
        new_entry = [role.name, str(role.id), str(role.position), str(role.colour.to_tuple()), str(role.hoist),
                     str(role.mentionable)]
        role_list.append(new_entry)
        print(len(str(await pretty_column(role_list, True))))
        if len(str(await pretty_column(role_list, True))) >= 1000:
            message_list.append(old_list[:-1])
            role_list = [new_entry]
    message_list.append(role_list)
    # print(message_list)
    multi = await multi_column(message_list, True)
    # print(multi)
    for mess in multi:
        await pretty_send(message.channel, mess)


async def pretty_send(destination, text):
    await client.send_message(destination, "```\n" + text.strip() + "\n```")


async def scrim_reset():
    global scrim

    for pair in scrim.team1.vc.overwrites:
        await client.delete_channel_permissions(scrim.team1.vc, pair[0])
    for pair in scrim.team2.vc.overwrites:
        await client.delete_channel_permissions(scrim.team2.vc, pair[0])


async def scrim_manage(message):
    auths = await get_auths(message.author)

    command = message.content.replace("`scrim ", "")
    command_list = command.split(" ")

    if "mod" in auths:
        if not scrim and command_list[0] == "start":
            await scrim_start(message)
        if command_list[0] == "manager":
            command_list = await mention_to_id(command_list)
            if command_list[1] == "list":
                managers = await scrim.get_managers()
                manager_list = [["Name", "ID"]]
                for manager_id in managers:
                    member = message.server.get_member(manager_id)
                    manager_list.append([member.name, member.id])
                text = await pretty_column(manager_list, True)
                await pretty_send(message.channel, text)


            else:
                await overwatch_db.scrim.find_one_and_update({"userid": command_list[1]},
                                                             {"$bit": {"manager": {"xor": 1}}})
        if command_list[0] == "end":
            await overwatch_db.scrim.update_many({}, {"$set": {"active": False, "team": "0"}})
            await scrim_end()
    if scrim:
        try:
            managers = await scrim.get_managers()
            if command_list[0] == "commands":
                list = [
                    ["Command", "Description"],
                    ["Public", ""],
                    ["`scrim list", "Lists each active participant in the scrim sorted by SR"],
                    ["`scrim teams", "Lists each active participant sorted by team and SR"],
                    ["`scrim join", "Starts the registration process. Have your battletag ready"],
                    ["`scrim leave", "Leaves the scrim and removes you from the active participants list"],
                    ["", ""],
                    ["Manager", ""],
                    ["`scrim reset", "Unassigns all active members from their teams"],
                    ["`scrim end", ""],
                    ["`scrim move <@mention> <team>", "Assigns a member to a team. Ex: `scrim move @Zenith#7998 1"],
                    ["`scrim remove <@mention>", "Removes a member from the active participant pool"],
                    ["`scrim autobalance", "Automatically sorts members into teams"],
                ]
                text = await pretty_column(list, True)
                await pretty_send(message.channel, text)

            if command_list[0] == "list":
                cursor = overwatch_db.scrim.find({"active": True, "rank": {"$exists": True}})

                cursor.sort("rank", pymongo.DESCENDING)

                userlist = [["Name", "ID", "Manager", "SR", "Team"]]
                async for user in cursor:
                    user_entry = []
                    try:
                        user_entry.append(unidecode(message.server.get_member(user["userid"]).name))
                    except:
                        user_entry.append("MISSING")

                    user_entry.append(user["userid"])
                    if user["manager"] == 1:
                        user_entry.append("True")
                    else:
                        user_entry.append("False")
                    user_entry.append(user["rank"])
                    team = user["team"]
                    if team == "0":
                        user_entry.append("Unassigned")
                    else:
                        user_entry.append("Team " + team)
                    userlist.append(user_entry)

                text = await multi_block(userlist, True)
                for item in text:
                    await pretty_send(message.channel, item)
            if command_list[0] == "teams":
                cursor = overwatch_db.scrim.find({"active": True, "rank": {"$exists": True}})

                cursor.sort("rank", pymongo.DESCENDING)

                # userlist = [["Name", "ID", "Manager", "SR"]]
                unassigned = [["Unassigned", "", "", ""], ["Name", "ID", "Manager", "SR"]]
                team1 = [["Team 1", "", "", ""], ["Name", "ID", "Manager", "SR"]]
                team2 = [["Team 2", "", "", ""], ["Name", "ID", "Manager", "SR"]]
                async for user in cursor:
                    team = user["team"]

                    if team == "0":
                        target_team = unassigned
                    elif team == "1":
                        target_team = team1
                    elif team == "2":
                        target_team = team2
                    else:
                        print("fail - check teams")
                        return

                    user_entry = []
                    user_entry.append(unidecode(message.server.get_member(user["userid"]).name))
                    user_entry.append(user["userid"])
                    if user["manager"] == 1:
                        user_entry.append("True")
                    else:
                        user_entry.append("False")
                    user_entry.append(user["rank"])
                    try:
                        target_team.append(user_entry)
                    except:
                        print(user)
                text = await multi_column([unassigned, team1, team2], True)
                # text = await pretty_column(userlist, True)
                for item in text:
                    await pretty_send(message.channel, item)
            if command_list[0] == "join":
                # await scrim.add_user(message.author.id)
                result = await scrim_join(message.author)
                print("brasdadastuh")
                await client.send_message(message.channel,
                                          message.author.mention + " has joined the scrim with an SR of " + result)
                print("brtuh")
            if command_list[0] == "leave":
                await scrim.leave(message.author)

            if message.author.id in managers:
                # if command_list[0] == "init":
                #     await overwatch_db.scrim.create_index([("userid", pymongo.DESCENDING)], unique=True)
                if command_list[0] == "reset":
                    await scrim.reset(message)

                if command_list[0] == "remove":
                    command_list = await mention_to_id(command_list)
                    target = message.server.get_member(command_list[1])
                    result = await scrim.leave(target)
                    await client.send_message(message.channel, result)

                if command_list[0] == "move":
                    target_member = message.mentions[0]
                    response = await scrim.assign(target_member, command_list[2])
                    await client.send_message(message.channel, response)
                    # await scrim.deauth(target_member)
                    # await scrim.auth(target_member, command_list[2])
                if command_list[0] == "autobalance":
                    cursor = overwatch_db.scrim.find(
                        {"active": True, "rank": {"$ne": "unplaced"}, "team": {"$eq": "0"}},
                        projection=["userid", "rank"])
                    cursor.sort("rank", -1)
                    members = await cursor.to_list(None)

                    print(members)
                    counter = 0
                    for user in members:
                        if counter % 2 == 0:
                            await scrim.assign(message.server.get_member(user["userid"]), "1")
                        else:
                            await scrim.assign(message.server.get_member(user["userid"]), "2")
                        counter += 1
                if command_list[0] == "forceactive":
                    await overwatch_db.scrim.update_many({"rank": {"$exists": True}}, {"$set": {"active": True}}, )
        except IndexError:
            await client.send_message(message.channel, "Syntax error")
    pass


async def scrim_new(member):
    await client.send_message(member, "What is your battletag?")

    def check(msg):
        if regex_test(reg_str=r"^\D.{2,12}#\d{4,6}$", string=msg.content):
            return True
        return False

    message = await client.wait_for_message(author=member, check=check)
    btag = message.content
    confirmation = "Joining scrim as " + btag
    await client.send_message(member, confirmation)
    return


async def scrim_join(member):
    await scrim.add_user(member)
    user = await overwatch_db.scrim.find_one({"userid": member.id, "btag": {"$exists": True}})
    if user:
        confirmation = "Joining scrim as " + user["btag"] + "… PM me a battletag to override"
        await client.send_message(member, confirmation)
        await scrim.refresh(member)
    else:
        await scrim_new(member)

    return user["rank"]


async def scrim_start(message):
    global scrim
    server = message.server
    mod_role = ROLENAME_ROLE_DICT["MODERATOR_ROLE"]
    mod_role = await get_role(client.get_server("236343416177295360"), "260186671641919490")
    super_manager_role = await get_role(client.get_server("236343416177295360"), "261331682546810880")

    vc_overwrite_everyone = discord.PermissionOverwrite(connect=False)
    vc_overwrite_mod = discord.PermissionOverwrite(connect=True)
    vc_overwrite_super_manager = discord.PermissionOverwrite(connect=True)

    text_overwrite_everyone = discord.PermissionOverwrite(read_messages=False)
    text_overwrite_mod = discord.PermissionOverwrite(read_messages=True)
    super_manager_perms_text = discord.PermissionOverwrite(read_messages=True)

    vc_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=vc_overwrite_everyone)
    vc_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=vc_overwrite_mod)
    vc_permission_super_manager = discord.ChannelPermissions(target=super_manager_role,
                                                             overwrite=vc_overwrite_super_manager)

    text_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=text_overwrite_everyone)

    # text_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=text_overwrite_mod)
    #
    # admin_text = discord.ChannelPermissions(target=ROLENAME_ROLE_DICT["ADMINISTRATOR_ROLE"], overwrite=admin_perms_text)

    scrim1_vc = await client.create_channel(server, "[Scrim] Team 1", vc_permission_everyone, vc_permission_mod,
                                            vc_permission_super_manager,
                                            type=discord.ChannelType.voice)
    scrim2_vc = await client.create_channel(server, "[Scrim] Team 2", vc_permission_everyone, vc_permission_mod,
                                            vc_permission_super_manager,
                                            type=discord.ChannelType.voice)
    scrim1 = ScrimTeam("1", scrim1_vc)
    scrim2 = ScrimTeam("2", scrim2_vc)

    scrim_spectate = await client.create_channel(server, "[Scrim] Spectate", type=discord.ChannelType.voice)

    scrim_text = await client.create_channel(server, "Scrim", text_permission_everyone, type=discord.ChannelType.text)

    scrim = ScrimMaster(scr1=scrim1, scr2=scrim2, txt=scrim_text, spec=scrim_spectate)
    mod_list = await get_moderators(message.server)
    for mod in mod_list:
        await overwatch_db.scrim.update_one({"userid": mod.id}, {"$set": {"manager": 1}}, upsert=True)

    print(await scrim.get_managers())

    await client.move_channel(scrim.spectate, 1)
    await client.move_channel(scrim.team1.vc, 2)
    await client.move_channel(scrim.team2.vc, 3)

    pass


async def get_user_info(member_id):
    """

    :type member: discord.Member
    """
    mongo_cursor = await userinfo_collection.find_one(
        {"userid": member_id}, projection={"_id": False, "mention_str": False}
    )
    if not mongo_cursor:
        return None
    list = mongo_cursor["avatar_urls"]
    if len(list) > 0 and len(list[0]) > 0:
        shortened_list = []
        for link in list:
            shortened_list.append(await shorten_link(link))
        mongo_cursor["avatar_urls"] = shortened_list
    return mongo_cursor


async def add_tag(string, note, action, categories):
    await trigger_str_collection.update_one({"string": string}, {
        "$addtoset": {"actions": action,
                      "note": note,
                      "categories": {"$each": categories}}})


async def tag_update(message):
    string = message.content.replace("`tag ", "")
    await client.send_message(message)


async def tag_str(message):
    trigger = message.content.replace("`tag ", "")

    # if trigger_str_collection.find_one({"trigger": string}):
    #     await tag_update(message)
    #     return

    # if string == "reset":
    #     await trigger_str_collection.remove({})
    #     await trigger_str_collection.create_index([("trigger", pymongo.DESCENDING)], unique=True)
    #     return

    interact = await client.send_message(message.channel, "Tagging string: \n `" + trigger + "`\n" +
                                         "What actions should I take? (kick, delete, alert, ping, mute <duration>")
    action_response = (await client.wait_for_message(author=message.author, channel=message.channel)).content

    action_response = " ".join((await mention_to_id(action_response.split(" "))))
    action_response = action_response.split("&")
    actions = []
    for action in action_response:
        if any(["kick", "delete", "alert"]) in action:
            action_list = action.split(" ", 1)
            await trigger_str_collection.insert_one(
                {"trigger": trigger, "action": action_list[0], "note": action_list[1]})
        if "mute" in action_response:
            action_list = action.split(" ", 2)
            await trigger_str_collection.insert_one(
                {"trigger": trigger, "action": action_list[0], "duration": action_list[1], "note": action_list[2]})
        if "ping" in action_response:
            pass


            #
            # else:
            #     await client.edit_message(interact, "Syntax not recognized. Please restart")
            #     return
            #     # result = await trigger_str_collection.insert_one(database_entry)
            #     # print(result)


async def remove_tag():
    pass


async def show_tags():
    pass


async def message_check(message):
    responses = await parse_triggers(message)
    await parse_responses(responses)


async def parse_triggers(message) -> list:
    response_list = []
    content = message.content
    async for doc in trigger_str_collection.find():
        if doc["trigger"] in content:
            response_list.append(doc)
    return response_list


async def mute_user(interface_channel, action):
    """

    :type action: list
    """
    await client.send_message(interface_channel, "!!mute " + SERVERS["OW"].get_member.mention + " + " + action[1])


async def move_member_to_vc(member, target_id):
    pass


async def id_to_mention(id):
    return "<@!" + id + ">"


async def parse_responses(response_list):
    for response in response_list:  # trigger action type
        action = response["action"].split(" ")
        if action[0] == "mute":
            mute_user(CHANNELNAME_CHANNEL_DICT["spam-channel"], action)
    pass


async def get_sr(tag):
    ow = OverwatchAPI("")
    tag = tag.replace("#", "-")
    eu_result = ow.get_profile(platform="pc", region="eu", battle_tag=tag)
    na_result = ow.get_profile(platform="pc", region="us", battle_tag=tag)
    print(eu_result)
    print(na_result)
    try:
        eu_rank = eu_result["data"]["competitive"]["rank"]
    except:
        eu_rank = "0"
    try:
        na_rank = na_result["data"]["competitive"]["rank"]
    except:
        na_rank = "0"

    # if na_rank == 0 and eu_rank == 0:
    #     return "Unplaced"
    return max([eu_rank, na_rank])


# with open(PATHS["comms"] + "bootstate.txt", "r") as f:
#     line = f.readline().strip()
#     if line == "killed":
#         ENABLED = False
# client.loop.create_task(stream())

def regex_test(reg_str, string):
    reg = re.compile(reg_str)
    match = reg.search(string)
    return match


client.run(AUTH_TOKEN, bot=True)
