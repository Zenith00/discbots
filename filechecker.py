import os
import time
import sys, string, ast

path = 	"C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
global before

global PATHS
PATHS={}

with open("paths.txt", "r") as f:
	global PATHS
	pathList = f.read()
	PATHS = ast.literal_eval(pathList)
	print("PATHS: " + str(PATHS))



def clean_string(string):
	return (string.encode(sys.stdout.encoding, errors='replace')).decode("utf-8")
count = 99

def fix_names():
	for folderTuple in os.walk(PATHS["art"]):
		for file in folderTuple[2]:
			new_file_name = ''.join(c for c in file if c in string.printable)
			if new_file_name != file:
				os.rename(os.path.join(folderTuple[0], file), os.path.join(folderTuple[0], new_file_name))
				print("renaming to " + new_file_name)
	return
while True:	
	count = count + 1
	print("FILECHECKER START")
	#while True:
	# before = dict ([(f, None) for f in os.listdir (path)])
	# time.sleep(5)
	# after = dict ([(f, None) for f in os.listdir (path)])
	# added = [f for f in after if not f in before]
	# added = list(set(added))
	# print(added)
	
	fix_names()
	before = [];
	after = [];
	if count == 100:
		f = open (PATHS["comms"] + "fileList.txt", "w")
	for folderTuple in os.walk(PATHS["art"]):
		for file in folderTuple[2]:
			before.append(os.path.join(folderTuple[0],file))
			if count == 100:
				f.write(os.path.join(folderTuple[0],file) + "^")
	if count == 100:
		f.close()
		count = 1
	
	time.sleep(5)
	fix_names()
	for folderTuple in os.walk(PATHS["art"]):
		for file in folderTuple[2]:
			after.append(os.path.join(folderTuple[0],file))

	added = [f for f in after if f not in before]
	
	print(added)
	list = open(PATHS["comms"] + "fileList.txt", "a")
	f = open(PATHS["comms"] + "toUpload.txt", "a")
	for x in added:
		print("FILE REGISTERED. ADDING")
		f.write(str(x) + "\n")
		list.write(str(x) + "^")
	f.close()
	list.close()
	fix_names()
	
		