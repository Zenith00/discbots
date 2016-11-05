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
import urllib
import imgurpython
from imgurpython import ImgurClient
import os
import asyncio
import time, shutil, fileinput, sys, traceback, inspect, filelock
from datetime import datetime
from io import BytesIO, StringIO
from concurrent.futures import ProcessPoolExecutor
import aiohttp, csv
from urllib.parse import parse_qs
# import pandas as pd
import collections

streamFile = "C:\\Users\\Austin\\Desktop\\Programming\\stream.txt"
#lock = filelock.FileLock(streamFile

global PATHS
PATHS={}


# path =	"C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"


with open("paths.txt", "r") as f:
	global PATHS
	pathList = f.read()
	PATHS = ast.literal_eval(pathList)
	print("PATHS: " + str(PATHS))













#LFGBOT
print("asdf")
client = discord.Client()
lfgReg = re.compile("/lf(G|\d)/ig")
print("asdf")
@client.event
async def on_ready():
	print('Connected!')
	print('Username: ' + client.user.name)
	print('ID: ' + client.user.id)
	

@client.event
async def on_voice_state_update(before, after):
	global PATHS
	f = open(PATHS["comms"] + "voiceTracked.txt", "r")
	ids = f.readlines()
	if after.id in ids:
		await client.send_message(client.get_channel("238163810274246656"), "User ID " + str(after.id) + "/" + after.display_name  + " has logged into " + after.voice.voice_channel.name + ", joining ")
	f.close()


async def log_message(message):
	global PATHS
	# print("Called")
	try: 
		#with lock.acquire(timeout = 2):
			with open(PATH["logs"] + "stream.txt", "a+") as f:
				# print(message)
				f.write(str(message))
				
			# lock.release(force=True)
	except filelock.Timeout:
		print("timed out")
	return

async def ascii_string(str):
	return str.encode('ascii','ignore').decode("utf-8")
	
@client.event
async def on_message(mess):
	global PATHS
	path2 = PATHS["logs"]
	zwidth = chr(8203)
	content = mess.content
	channel = mess.channel
	reg = re.compile(r"((lf(G|\d)))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF((((NA)|(EU)))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|(http(s?)://discord.gg/)|(xbox)|(ps4)", re.IGNORECASE)
	match = reg.search(mess.content)
	if mess.author.id == "129706966460137472":
		if mess.server == client.get_server("94882524378968064") and mess.channel.id not in ["152757147288076297", "170179130694828032", "147153976687591424", "200185170249252865", "209609220084072450"]:
			toSend = await ascii_string("[" + mess.channel.name + "] " + mess.author.name + ": -*0       " + mess.content + "\n")
			await log_message(toSend)
			return
		
		if "!join" == mess.content[0:5]:
			mentionedUser = mess.mentions[0]
			print(mentionedUser.name)
			print()
			vc = (mentionedUser.voice.voice_channel)
			print(str(mentionedUser.voice))
			print(await ascii_string(vc.name))
			
			print("opus: "  + str(discord.opus.is_loaded()))
			
			if vc != None:
				print("TRIGG12313ERED")
				print("TRIGG12313ERED")
				vclient = await client.join_voice_channel(vc)
				print("TRIGGERED")
				# vclient.move_to(vc)
				print(await ascii_string(vclient.channel.name))
				print(vclient.is_connected())
				print(client.voice.Channel.name)
				# client.
			return
		if "!join+" == mess.content[0:6]:
			id = mess.content[7:]
			mentionedUser = discord.Object(id)
			if mentionedUser.voice.voice_channel != None:
				await client.join_voice_channel(mentionedUser.voice.voice_channel)
		if "!getactivity" in mess.content:
			command = mess.content[13:]
			await client.delete_message(mess)
			d = datetime.timedelta(days=int(command))
			sinceTime = mess.timestamp - d
			messageCountConsolidated = []
			print(str(sinceTime))
			for channel in (y for y in mess.server.channels if y.type == discord.ChannelType.text):
				messageCount = []
				async for message in client.logs_from(channel, after=sinceTime):
					for x in range(len(str(message.content)) - 1):
						messageCount.append(message.author.name)
						messageCountConsolidated.append(message.author.name)
				print("messages retrieved")
				with open(PATHS["logs"] + str(channel.name) + ".csv", 'a', newline='') as myfile:
					wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL)
					# print(messageCount)
					for x in collections.Counter(messageCount).most_common():
						y = (str(x[0]).encode('ascii','ignore').decode("utf-8"), str(x[1]).encode('ascii','ignore').decode("utf-8"))
						
						# print("y = " + str(y))
						wr.writerow(list(y))
				
				print("finished")
			with open(PATHS["logs"] + "consolidated.csv", 'a', newline='') as myfile:
				wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL)
				# print(messageCount)
				for x in collections.Counter(messageCountConsolidated).most_common():
					y = (str(x[0]).encode('ascii','ignore').decode("utf-8"), str(x[1]).encode('ascii','ignore').decode("utf-8"))
					
					# print("y = " + str(y))
					wr.writerow(list(y))
			return
				
		if "!setstatus" in mess.content:
			status = mess.content[11:]
			await client.change_presence(game=discord.Game(name=str(status)))
			return

		if match != None and mess.channel.id == "94882524378968064":
			await client.send_message(client.get_channel("240310063082897409"), mess.content)
			return
			
		if "!getlogs" in mess.content:
			counter = 1
			time = datetime.now()
			async for message in client.logs_from(mess.channel, 1000000):
				counter = counter + 1
				with open(path2 + "logs.txt", "a") as myfile:
					try:
						myfile.write(message.timestamp.strftime("[%Y-%m-%d %H:%m:%S] ") + str(message.author.nick).encode('ascii','ignore').decode("utf-8") + ": " + message.content.encode('ascii','ignore').decode("utf-8") + "\n")
					except:
						print("error")
				if counter % 200 == 0:
					await client.edit_message(mess, "Log Retrieval at minimum " + str((float(i)/1000000) * 100) + "%")
			await client.send_message(mess.channel, "Log Retrieval complete after " + (datetime.utcnow() - time).strftime("%H:%m:%S"))
						
			
			return
		if "!google" in mess.content:
			query = mess.content[8:]
			"""Searches google and gives you top result."""
			try:
				entries = await get_google_entries(query)
			except RuntimeError as e:
				print(str(e))
			else:
				next_two = entries[1:3]
				if next_two:
					formatted = '\n'.join(map(lambda x: '<%s>' % x, next_two))
					msg = '{}\n\n**See also:**\n{}'.format(entries[0], formatted)
				else:
					msg = entries[0]

			await client.send_message(mess.channel, msg)
			await client.delete_message(mess)
			return
		

		if mess.channel.id == "168567769573490688":
			if "http" in mess.content:
				await client.send_message(client.get_channel("240310063082897409"), mess.content)
		
		if "!geticon" in mess.content:
			userID = mess.content[5:]
			user = await client.get_user_info(userID)
			await client.send_message(mess.channel, user.avatar_url)
			client.delete_message(mess)
		if "!run" in mess.content:
			code = mess.content[5:]
			try:
				result = eval(code)
			except Exception:
				formatted_lines = traceback.format_exc().splitlines()
				await client.edit_message(mess,('```py\n{}\n{}\n```'.format(formatted_lines[-1], '/n'.join(formatted_lines[4:-1]))))

			if asyncio.iscoroutine(result):
				result = await result

			if result:
				await client.edit_message(mess, "```py" + "\n" + "@Input:\n" + str(code) + "\n" + "@Output:\n" + str(result) + "\n```")
			
		if "!exe" in mess.content:
			code = mess.content[5:]
			#old_stdout = sys.stdout
			#redirected_output = sys.stdout = StringIO()
			#output = redirected_output
			output = ""
			try:
				#exec(code)
				print("asdf running code\n" * 5)
				print(exec(code))
				print("axa")
				print("axasdada")
				#print(str(next(aexec(code))))
			except Exception:
				formatted_lines = traceback.format_exc().splitlines()
				output = '```py\n{}\n{}\n```'.format(formatted_lines[-1], '\n'.join(formatted_lines[4:-1]))
			finally: 
				#sys.stdout = old_stdout
				time.sleep(0)
			if (not isinstance(output, str)):
				await client.edit_message(mess, output.getvalue())
			else:
				await client.edit_message(mess, str(output))
				print(output)
			

		#print(time.strftime("[%Y-%m-%d %H:%m:%S] ",time.gmtime()) + "message recieved")
		if mess.content == '!count':
			asyncio.sleep(.5)
			await client.edit_message(mess, mess.server.member_count)
			asyncio.sleep(.5)
		if mess.content == '!refreshart':
			global before
			#msg = client.send_message(client.get_channel("236531729425235968"), image['link'])
			f = open(PATH["comms"] + "botdata.txt", "r")
			for link in f:
				print("NOTE" * 3)
				stripLink = link.rstrip('\n')
				await client.send_message(mess.channel, stripLink)
				asyncio.sleep(1)
			f.close()
			f = open(PATH["comms"] + "botdata.txt", "w")
			f.close()
		
		if mess.content == '!lfg':
			lfgText = "You're probably looking for <#182420486582435840> or <#185665683009306625>. Please avoid posting LFGs in <#94882524378968064> . "
			await client.edit_message(mess, lfgText)
			#logs = clients.logs_from('94882524378968064', limit=5)
			# client=  discord.utils.get(server.channels, id='ID HERE')
			authorMention = ""
			messageStack = []
			async for messageCheck in client.logs_from(mess.channel,8):
				if messageCheck.author.id != client.user.id:
					print(messageCheck.content)
					reg = re.compile(r"((lf(G|\d)))|( \d\d\d\d )|(plat|gold|silver|diamond)|(^LF((((NA)|(EU)))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|(http(s?)://discord.gg/)|(xbox)|(ps4)", re.IGNORECASE)
					match = reg.search(messageCheck.content)
					if match != None:
						print("ASDF")
						#if messageCheck.channel.id == "94882524378968064":
						authorMention = "<@" + messageCheck.author.id + ">"
						break
					else:
						authorMention = ""
			# async for messageCheck in logs:
				
			#asyncio.sleep(.5)
			lfgText += authorMention
			#asyncio.sleep(.75)
			await client.edit_message(mess, lfgText)
			#asyncio.sleep(.5)
		#print (str(mess.server) + " " + mess.content)
		if "gib" in mess.content.lower() and "art" in mess.content.lower() and mess.server == None:
			print("SENDING \n" * 5)
			await client.send_message(mess.author, "http://bit.ly/zenithfanart")
		if mess.content == "!nothingbutfanarthere":
			f = open(PATHS["comms"] + "fileList.txt", "r")
			files = f.readline().split("^")
			f.close()
			print(files)
			rand_art = random.sample(files,15)
			f = open(PATHS["comms"] + "toUpload.txt", "a")
			for artpiece in rand_art:
				print(artpiece)
				f.write(artpiece + "\n")
			f.close()
		if mess.content == "!ping":
			print(str(datetime.utcnow()))
			newMessContent = "Ping!\nPong! " + str((datetime.utcnow() - mess.timestamp).total_seconds() * 1000) + " ms"
			await client.send_message(mess.channel, newMessContent)
			await client.delete_message(mess)
			content = newMessContent
			return
		
	# if mess.author.id == "129706966460137472":
		# try:
			# await client.edit_message(mess, await avoid_bot(content))
		# except:
			# client.send_message(mess.channel, await avoid_bot(content))

	
	
	

 




	
client.run("mfa.u17NxslSy23KcTcaMF7bwTgqvCONorAJ7JClDguYJ-Gj1np9pWWlngdxn57DQ_qGY1Dbj8-GlxsvI1rXwAf3", bot=False)