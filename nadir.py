"""Provide an asynchronous equivalent *to exec*."""

import sys
import ast
import codeop
import asyncio

#from . import compat
import discord
import re
from discord.ext import commands
import random
import os
#import win32file
#import win32con
import time, shutil, fileinput, datetime, traceback, inspect, filelock
from io import BytesIO, StringIO
from concurrent.futures import ProcessPoolExecutor

from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sqlite3
global PATHS
PATHS = {}

with open("paths.txt", "r") as f:
	global PATHS
	pathList = f.read()
	PATHS = ast.literal_eval(pathList)
	# print("PATHS: " + str(PATHS))



database = sqlite3.connect(PATHS["comms"] + "userIDlist.db")
# os.environ["PYTHONASYNCIODEBUG"] = "1"


streamFile = "C:\\Users\\Austin\\Desktop\\Programming\\stream.txt"

# lock = filelock.FileLock(streamFile)
ZENITH_ID = "129706966460137472"

#FANARTBOT

global before

#LFGBOT

client = discord.Client()
lfgReg = re.compile("/lf(G|\d)/ig")

@client.event
async def on_ready():
	print('Connected!')
	print('Username: ' + client.user.name)
	print('ID: ' + client.user.id)
	
@client.event
async def on_member_join(member):
	# if "!startup" in mess.content:
	print("NEW USER JOINED")
	
	userID = member.id
	userNick = member.nick
	userName = await ascii_string(member.name)
	if userNick is None:
		userNick = userName
	else:
		userNick = await ascii_string(userNick)
	
	userNick = userNick.lower()
				
	toExecute = "INSERT INTO useridlist VALUES (?, ?, ?)"
	vars = (userID, userNick, userName)
	try:
		database.execute(toExecute, vars)
	except:
		pass
	database.commit()
	return
	
async def ascii_string(str):
	return str.encode('ascii','ignore').decode("utf-8")
	

@client.event
async def on_message(mess):
	global PATHS
	if "!join" == mess.content[0:5]:
		if len(mess.mentions) > 0:
			mentionedUser = mess.mentions[0]
		else:
			userID = mess.content[6:]
			mentionedUser = mess.server.get_member(userID)

		vc = (mentionedUser.voice.voice_channel)
		
		instaInvite = await client.create_invite(vc, max_uses=1, max_age=6)
		# VCMess = mess
		VCInvite = await client.send_message(mess.channel, instaInvite.url)
	if "!find" == mess.content[0:5]:
		command = mess.content[6:]
		match = await fuzzy_match(command, mess)
	
	
	
	if mess.channel.id == "240310063082897409":
		await client.send_message(client.get_channel("240320691868663809"), mess.content)
	if "!clear" in mess.content and mess.server.id == "236343416177295360":
		deleted = await client.purge_from(mess.channel)
	
	if mess.author.id == ZENITH_ID:
		if "!rebuild" in mess.content:
			database.execute('''CREATE TABLE useridlist (
				userid   STRING,
				nickname STRING,
				username STRING,
				UNIQUE (
					userid
				)
			)''')
			
			print("BUILDING DATABASE")
			count = 0
			for member in mess.server.members:
				if count % 100 == 0:
					print("ADDING A MEMBER" + str(count))
				count = count + 1
				userID = member.id
				userNick = member.nick
				userName = await ascii_string(member.name)
				if userNick is None:
					userNick = userName
				else:
					userNick = await ascii_string(userNick)
				
				userNick = userNick.lower()
				
				toExecute = "INSERT INTO useridlist VALUES (?, ?, ?)"
				vars = (userID, userNick, userName)
				try:
					database.execute(toExecute, vars)
					# print(str(database.commit()))
				except:
					pass
			database.commit()
			return
		
		
async def fuzzy_match(command, mess):
	sentMessages = []
	sentMessages.append(await client.send_message(mess.channel, "Input: " + command))
	cursor = database.cursor()
	cursor.execute('SELECT userid,nickname FROM useridlist')
	nickIdList = cursor.fetchall()
	nickIdDict = {}
	for v, k in nickIdList:
		nickIdDict.setdefault(k, []).append(v)
	# topThree = process.extract(command, nickIdDict.keys(), limit=3)
	# topOne = process.extractOne(command, nickIdDict.keys())
	# for nickFuzzPair in topThree:
		# nick = nickFuzzPair[0]
		# for id in nickIdDict[nick]:
			# sentMessages.append(
				# await client.send_message(mess.channel, 
				
					# "ID: " + str(id) + " | Nickname: " + nick + " (" + str(nickFuzzPair[1]) + ")"
				# )
			# )
	
	# await client.send_message(mess.channel, 
			
		# "ID: " + str(id) + " | Nickname: " + topOne[0] + " (" + str(topOne[1]) + ")"
	# 
	topScore = 0
	topNick = ""
	ratio = 0
	for k in nickIdDict.keys():
		ratio = fuzz.ratio(command, str(k))
		if ratio > topScore:
			topScore = ratio
			topNick = k
			print("new topScore: " + str(topScore))
			print("new nick: " + str(topNick))
	nick = topNick
	for id in nickIdDict[nick]:
		sentMessages.append(
			await client.send_message(mess.channel, 
			
				"ID: " + str(id) + " | Nickname: " + nick + " (" + str(topScore) + ")"
			)
		)


	
async def manually_reset():
	
	pass
async def stream():
	await client.wait_until_ready()
	while not client.is_closed:
		# print("asdf")
		try: 
			# with lock.acquire(timeout = 2):
			with open(streamFile, 'r') as f:
				f.seek(0)
				messToSend = str(f.readline())
			if messToSend == "":
				continue
			print("1")
			with open(streamFile, 'r') as fin:
				data = fin.read().splitlines(True)
			print("2")
			with open(streamFile, 'w') as fout:
				fout.writelines(data[1:])
			if len(messToSend) > 0:
				fullMessage = messToSend.split("-*0")
				print("fullMessage")
				if len(fullMessage) == 2:
					await client.send_message(client.get_channel("243161899410128898"), fullMessage[0] + "\n" + fullMessage[1])
		except:
			pass
		# await asyncio.sleep(.05)
	
# client.loop.create_task(stream())	
client.run("MjM2MzQxMTkzODQyMDk4MTc3.CvBk5w.gr9Uv5OnhXLL3I14jFmn0IcesUE", bot=True)