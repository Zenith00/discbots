userID = "'member.id'"
userNick = "'member.nick'"
userName = "'member.name'"
import sqlite3, ast

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
toExecute = "INSERT INTO useridlist VALUES (?, ?, ?)"
vars = (userID, userNick, userName)
try:
	database.execute(toExecute, vars)
except:
	pass
database.execute(toExecute, ("'123'", "'123'", "'123'"))
database.commit()
for row in database.execute('SELECT * FROM useridlist'):
	print(row)