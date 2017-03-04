import motor.motor_asyncio
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()
import discord

overwatch_db = mongo_client.overwatch
client = discord.Client()
from pymongo import ReturnDocument
import pymongo


class ScrimTeam:
    def __init__(self, id, channel):
        self.members = []
        self.name = id
        self.vc = channel

class ScrimMaster:
    def __init__(self, scr1, scr2, txt, spec, output):
        self.output = output
        self.team1 = scr1
        self.team2 = scr2
        self.text = txt
        self.spectate = spec
        self.masters = []
        self.client = globals().get(client)

    async def get_managers(self):
        managers = []
        manager_cursor = overwatch_db.scrim.find({"manager": 1})
        async for manager in manager_cursor:
            managers.append(manager["userid"])

        return managers

    async def end(self):
        await self.client.delete_channel(self.team1.vc)
        await self.client.delete_channel(self.team2.vc)
        await self.client.delete_channel(self.text)
        await self.client.delete_channel(self.spectate)
        await overwatch_db.scrim.update_many({}, {"$set": {"active": False, "pos": 0, "status": ""}})

    async def assign(self, member, team):
        await self.deauth(member)
        return await self.auth(member, team)

    async def reset(self):
        cursor = overwatch_db.scrim.find({"active": True})
        server = self.output.server
        async for person in cursor:
            await self.deauth(server.get_member(person["userid"]))
        await overwatch_db.scrim.update_many({"status": "playing"}, {"$set": {"active": False}})

    async def auth(self, member, team):
        print("Assigning {} to {}".format(member.id, team))
        if team == "1":
            target_team = self.team1
        elif team == "2":  # team == "2":
            target_team = self.team2
        else:
            return
        # self.members[member.id] = team
        await overwatch_db.scrim.update_one({"userid": member.id}, {"$set": {"team": target_team.name}})

        target_team.members.append(member.id)
        user_overwrite_vc = discord.PermissionOverwrite(connect=True)
        await self.client.edit_channel_permissions(target_team.vc, member, user_overwrite_vc)
        return member.mention + " added to team " + target_team.name

    async def deauth(self, member):
        if not member:
            return
        target_member = await overwatch_db.scrim.find_one({"userid": member.id})
        if not target_member:
            print("FAILED TO FIND {}".format(member.id))
            return
        if "team" not in target_member.keys():
            return
        target = target_member["team"]
        if target == "1":
            target_team = self.team1
        elif target == "2":
            target_team = self.team2
        else:
            return
        await self.client.delete_channel_permissions(target_team.vc, member)

    async def force_register(self, message):
        command_list = message.content.split(" ")
        print(command_list)
        print("Registering")
        await overwatch_db.scrim.update_one({"userid": command_list[5]},
                                            {"$set": {"rank"  : command_list[3].lower(), "btag": command_list[2],
                                                      "region": command_list[4], "active": True}}, upsert=True)
        await scrim.add_user(self.output.server.get_member(command_list[5]))

    async def register(self, message):
        command_list = message.content.split(" ")
        await overwatch_db.scrim.update_one({"userid": message.author.id},
                                            {"$set": {"rank"  : command_list[1].lower(), "btag": command_list[0],
                                                      "region": command_list[2], "active": True}}, upsert=True)
        await scrim.add_user(message.author)

    async def serve_scrim_prompt(self, member):
        user = await overwatch_db.scrim.find_one({"userid": member.id, "btag": {"$exists": True}})
        if user:
            confirmation = "Joining scrim as [{region}] {btag} with an SR of {sr}".format(region=user["region"],
                                                                                          btag=user["btag"],
                                                                                          sr=user["rank"])
            await self.client.send_message(member, confirmation)
            await scrim.add_user(member)
        else:
            await self.client.send_message(member,
                                      "Please enter your battletag, highest SR, and region (EU, NA, KR) in the format:\nBattleTag#0000 2500 EU\n or Battletag#00000 unplaced NA")

    async def add_user(self, member):
        size = 12
        # base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.DESCENDING)])
        await self.compress()
        cursor = overwatch_db.scrim.find({"active": True})
        count = await cursor.count()
        print(count)

        await overwatch_db.scrim.update_one({"userid": member.id},
                                            {"$set": {"active": True, "pos": count, "status": "pending",
                                                      "team"  : ""}})

        new_joined = await overwatch_db.scrim.find_one({"userid": member.id})
        cursor = overwatch_db.scrim.find({"active": True})
        count = await cursor.count()
        print(count)
        update = "[{region}] {btag} ({mention}) has joined the scrim with an SR of {sr} ({count}/{size})".format(
            region=new_joined["region"], btag=new_joined["btag"], mention=member.mention, sr=new_joined["rank"],
            count=count, size=size)
        await self.client.send_message(self.output, update)

    async def start(self):
        await self.compress()

        overwatch_db.scrim.update_many({"active": True}, {"$set": {"team": "pending"}})
        # await self.reset()
        size = 12
        cursor = overwatch_db.scrim.find({"active": True})
        count = await cursor.count()
        if count < size:
            await self.client.send_message(self.output,
                                      "Not enough players: ({count}/{size})".format(count=count, size=size))
            return
        else:
            base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.ASCENDING)])
            if not base:
                print("BLAHAHAHAH")
                return
            if base["pos"] != 1:
                print(str(base["pos"]) + " " + base["btag"])
                start = 1 - base["pos"]
                await overwatch_db.scrim.update_many({"active": True}, {"$inc": {"pos": start}})

            await self.client.send_message(self.output, "Starting...")
            await overwatch_db.scrim.update_many({"active": True, "pos": {"$lt": size + 1}},
                                                 {"$set": {"status": "playing"}})
            await self.autobalance()
            await self.output_teams()
            await overwatch_db.scrim.update_many({"status": "playing"}, {"active": False, "pos": ""})
            base = await overwatch_db.scrim.find_one({"active": True}, sort=[("pos", pymongo.ASCENDING)])
            if not base:
                print("BLAHAHAHAH")
                return
            if base["pos"] != 1:
                start = 1 - base["pos"]
                await overwatch_db.scrim.update_many({"active": True}, {"$inc": {"pos": start}})

    async def leave(self, member):
        userid = member.id
        await overwatch_db.scrim.update_one({"userid": userid},
                                            {"$set": {"team": "0", "active": False, "manager": 0, "status": "",}})
        return "Removed " + member.mention + " from the active user pool"

    # async def register(self, member, btag, sr, region):
    #
    #     await overwatch_db.scrim.update_one({"userid": member.id},
    #                                         {"$set": {"rank": sr, "btag": btag, "region": region, "active": True}},
    #                                         upsert=True)

    async def refresh(self, member):
        user = await overwatch_db.scrim.find_one({"userid": member.id})
        await self.register(member, user["btag"])

    async def autobalance(self):
        server = self.output.server

        cursor = overwatch_db.scrim.find(
            {"active": True, "status": "playing"},
            projection=["userid", "rank"])

        cursor.sort("rank", -1)
        members = await cursor.to_list(None)
        print(members)
        counter = 0
        for user in members:
            if counter == 4:
                counter = 0
            if counter == 0 or counter == 3:
                await scrim.assign(server.get_member(user["userid"]), "1")

            elif counter == 1 or counter == 2:
                await scrim.assign(server.get_member(user["userid"]), "2")
            counter += 1
        await self.client.send_message(self.output, "Autobalancing completed")

    async def compress(self):
        count = 1
        cursor = overwatch_db.scrim.find({"active": True})
        cursor.sort("pos", pymongo.ASCENDING)
        async for item in cursor:
            print(item)
            print(count)
            result = await overwatch_db.scrim.update_one({"userid": item["userid"]}, {"$set": {"pos": count}})
            print(result.raw_result)
            count += 1

    async def output_teams_list(self):
        await self.compress()
        cursor = overwatch_db.scrim.find({"active": True})

        cursor.sort("pos", pymongo.ASCENDING)

        userlist = [["Name", "Battletag", "SR", "Position"]]
        async for user in cursor:
            print(user)
            user_entry = []
            try:
                user_entry.append(unidecode(self.output.server.get_member(user["userid"]).name))
            except:
                user_entry.append("MISSING")

            user_entry.append(user["btag"])
            user_entry.append(user["rank"])
            user_entry.append(str(user["pos"]))
            userlist.append(user_entry)
        await send(self.output, userlist, "rows")

    async def output_teams(self):
        cursor = overwatch_db.scrim.find({"active": True, "status": "playing"})
        team1 = [["Team 1", "", "", ""], ["Name", "Battletag", "SR", "ID"]]
        team2 = [["Team 2", "", "", ""], ["Name", "Battletag", "SR", "ID"]]
        async for user in cursor:
            team = user["team"]

            if team == "1":
                target_team = team1
            elif team == "2":
                target_team = team2
            else:
                print("fail - check teams")
                return

            user_entry = []

            user_entry.append(unidecode(self.output.server.get_member(user["userid"]).name))
            user_entry.append(user["btag"])
            user_entry.append(user["rank"])
            user_entry.append(user["userid"])
            try:
                target_team.append(user_entry)
            except:
                print(user)
        for item in [team1, team2]:
            await send(destination=self.output, text=item, send_type="rows")


async def scrim_manage(message):
    auths = await get_auths(message.author)

    command = message.content.replace("..scrim ", "")
    command_list = command.split(" ")
    command_list = await mention_to_id(command_list)
    if "mod" in auths or "host" in auths:
        if not scrim and command_list[0] == "start":
            await scrim_start(message)
            # if command_list[0] == "manager":
            #     command_list = await mention_to_id(command_list)
            #     if command_list[1] == "list":
            #         managers = await scrim.get_managers()
            #         manager_list = [["Name", "ID"]]
            #         for manager_id in managers:
            #             member = message.server.get_member(manager_id)
            #             manager_list.append([member.name, member.id])
            #         await send(destination=message.channel, text=manager_list, send_type="rows")


            # else:
            #     await overwatch_db.scrim.find_one_and_update({"userid": command_list[1]},
            #                                                  {"$bit": {"manager": {"xor": 1}}})
        if command_list[0] == "end":
            await overwatch_db.scrim.update_many({}, {"$set": {"active": False, "pos": 0}})
            await scrim_end()
        if command_list[0] == "next":
            await scrim.start()
        if command_list[0] == "add":
            await scrim.force_register(message)
        if command_list[0] == "remove":
            user = await message.server.get_member(command_list[1])
            if user:
                await scrim.leave(user)
            else:
                await client.send_message(message.channel, "User not recognized")

    if scrim:
        try:
            # managers = await scrim.get_managers()
            # if command_list[0] == "commands":
            #     list = [
            #         ["Command", "Description"],
            #         ["Public", ""],
            #         ["`scrim list", "Lists each active participant in the scrim sorted by SR"],
            #         ["`scrim teams", "Lists each active participant sorted by team and SR"],
            #         ["`scrim join", "Starts the registration process. Have your battletag ready"],
            #         ["`scrim leave", "Leaves the scrim and removes you from the active participants list"],
            #         ["", ""],
            #         ["Manager", ""],
            #         ["`scrim reset", "Unassigns all active members from their teams"],
            #         ["`scrim end", ""],
            #         ["`scrim move <@mention> <team>", "Assigns a member to a team. Ex: `scrim move @Zenith#7998 1"],
            #         ["`scrim remove <@mention>", "Removes a member from the active participant pool"],
            #         ["`scrim autobalance", "Automatically sorts placed members into teams"],
            #         ["`scrim ping", "Pings every member assigned to a team"],
            #     ]
            #     await send(destination=message.channel, text=list, send_type="rows")
            #     # text = pretty_column(list, True)
            #     # await pretty_send(message.channel, text)


            if command_list[0] == "help":
                list = [["Command", "Details", "Role"],
                        ["..scrim join", "Joins the scrim. Bot will PM you", "Everyone"],
                        ["..scrim list", "Lists the members in the queue", "Everyone"],
                        ["..scrim start", "Starts up the scrimbot.", "Host+"],
                        ["..scrim end", "Ends the scrim and cleans up", "Host+"],
                        ["..scrim next", "Pulls the next 12 players and forms teams", "Host+"]
                        ]
                await send(destination=scrim.output, text=list, send_type="rows")
            if command_list[0] == "list":
                await scrim.output_teams_list()
                await client.delete_message(message)

            if command_list[0] == "join":
                # await scrim.add_user(message.author)
                await scrim.serve_scrim_prompt(message.author)
                await client.delete_message(message)

            if command_list[0] == "leave":
                await scrim.leave(message.author)




        except IndexError:
            await client.send_message(message.channel, "Syntax error")
    pass

async def scrim_start(message):
    global scrim
    server = message.server
    # mod_role = ROLENAME_ROLE_DICT["MODERATOR_ROLE"]
    mod_role = await get_role(client.get_server("236343416177295360"), "260186671641919490")
    # super_manager_role = await get_role(client.get_server("236343416177295360"), "261331682546810880")

    vc_overwrite_everyone = discord.PermissionOverwrite(connect=False, speak=True)
    vc_overwrite_mod = discord.PermissionOverwrite(connect=True)
    vc_overwrite_super_manager = discord.PermissionOverwrite(connect=True)

    text_overwrite_everyone = discord.PermissionOverwrite(read_messages=False)
    # text_overwrite_mod = discord.PermissionOverwrite(read_messages=True)
    # super_manager_perms_text = discord.PermissionOverwrite(read_messages=True)

    vc_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=vc_overwrite_everyone)
    vc_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=vc_overwrite_mod)
    # vc_permission_super_manager = discord.ChannelPermissions(target=super_manager_role, overwrite=vc_overwrite_super_manager)

    text_permission_everyone = discord.ChannelPermissions(target=server.default_role, overwrite=text_overwrite_everyone)

    # text_permission_mod = discord.ChannelPermissions(target=mod_role, overwrite=text_overwrite_mod)
    #
    # admin_text = discord.ChannelPermissions(target=ROLENAME_ROLE_DICT["ADMINISTRATOR_ROLE"], overwrite=admin_perms_text)

    scrim1_vc = await client.create_channel(server, "[Scrim] Team 1", vc_permission_everyone, vc_permission_mod,
                                            type=discord.ChannelType.voice)
    scrim2_vc = await client.create_channel(server, "[Scrim] Team 2", vc_permission_everyone, vc_permission_mod,
                                            type=discord.ChannelType.voice)
    scrim1 = ScrimTeam("1", scrim1_vc)
    scrim2 = ScrimTeam("2", scrim2_vc)

    scrim_spectate = await client.create_channel(server, "[Scrim] Spectate", type=discord.ChannelType.voice)

    scrim_text = await client.create_channel(server, "Scrim", text_permission_everyone, type=discord.ChannelType.text)

    scrim = ScrimMaster(scr1=scrim1, scr2=scrim2, txt=scrim_text, spec=scrim_spectate, output=message.channel)
    # mod_list = await get_moderators(message.server)
    # for mod in mod_list:
    #     await overwatch_db.scrim.update_one({"userid": mod.id}, {"$set": {"manager": 1}}, upsert=True)

    time = datetime.utcnow().isoformat(" ")
    # pin_marker = await client.send_message(client.get_channel("262494034252005377"), "Highlights from " + time[5:10])
    # await client.pin_message(pin_marker)
    await client.move_channel(scrim.spectate, 1)
    await client.move_channel(scrim.team1.vc, 2)
    await client.move_channel(scrim.team2.vc, 3)

    pass


async def scrim_end():
    global scrim
    await scrim.end()
    scrim = None

async def scrim_reset():
    global scrim

    for pair in scrim.team1.vc.overwrites:
        await client.delete_channel_permissions(scrim.team1.vc, pair[0])
    for pair in scrim.team2.vc.overwrites:
        await client.delete_channel_permissions(scrim.team2.vc, pair[0])
