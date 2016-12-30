import discord
import motor.motor_asyncio

from utils_text import *



client = discord.Client()
scrim = None
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()



ow_db = mongo_client.overwatch

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
        manager_cursor = ow_db.scrim.find({"manager": 1})
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
        cursor = ow_db.scrim.find({"active": True})
        async for person in cursor:
            await self.deauth(message.server.get_member(person["userid"]))
            # await overwatch_db.scrim.update_many({"active": True}, {"$set": {"team": "0"}})

    async def auth(self, member, team):
        print("Assigning {} to {}".format(member.id, team))

        if team == "0":
            await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"team": "0"}})
            return member.mention + " unassigned"
        if team == "1":
            target_team = self.team1
        else:  # team == "2":
            target_team = self.team2

        # self.members[member.id] = team
        await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"team": target_team.name}})

        target_team.members.append(member.id)
        user_overwrite_vc = discord.PermissionOverwrite(connect=True)
        await client.edit_channel_permissions(target_team.vc, member, user_overwrite_vc)
        return member.mention + " added to team " + target_team.name

    async def deauth(self, member):
        # try:
        #     target = self.members[member.id]
        # except KeyError:
        #     return "User is not in a team"
        target_member = await         ow_db.scrim.find_one({"userid": member.id})
        if not target_member:
            print("FAILED TO FIND {}".format(member.id))
            return
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

        await ow_db.scrim.update_one({"userid": member.id}, {"$set": {"team": "0"}})
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

@client.event
async def on_message(message_in):

    
    if message_in.author == client.user:
        return
    if message_in.server is None:
        if scrim:
            if regex_test(reg_str=r"^\D.{2,12}#\d{4}$", string=message_in.content):
                await scrim.register(message_in.author, message_in.content)

        else:
            await client.send_message(await client.get_user_info(message_in.ZENITH_ID), "[{}]: {}".format(message_in.author.name, message_in.content))
        return



