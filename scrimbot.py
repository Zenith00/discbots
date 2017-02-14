import motor.motor_asyncio
mongo_client = motor.motor_asyncio.AsyncIOMotorClient()



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