userID = "'member.id'"
userNick = "'member.nick'"
userName = "'member.name'"
import sqlite3, ast
from collections import defaultdict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
with open("paths.txt", "r") as f:
	global PATHS
	pathList = f.read()
	PATHS = ast.literal_eval(pathList)
	# print("PATHS: " + str(PATHS))



database = sqlite3.connect(PATHS["comms"] + "userIDlist.db")

# database.execute('''CREATE TABLE useridlist (
    # userid   STRING,
    # nickname STRING,
    # username STRING,
    # UNIQUE (
        # userid
    # )
# )''')
sentMessages = []
cursor = database.cursor()
cursor.execute('SELECT userid,nickname FROM useridlist')
nickIdList = cursor.fetchall()
nickIdDict = {}
for v, k in nickIdList:
	nickIdDict.setdefault(k, []).append(v)
topThree = process.extract("awdwada", nickIdDict.keys(), limit=3)
for nickFuzzPair in topThree:
	nick = nickFuzzPair[0]
	for id in nickIdDict[nick]:
		sentMessages.append(
			# await client.send_message(mess.channel, 
			print(
				"ID: " + str(id) + " | Nickname: " + nick
			))
		

